from flask import Blueprint, request, jsonify
from db_helper import db

student_bp = Blueprint('student', __name__)

# 选课（修复参数错误和存储过程结果处理）
@student_bp.route('/enroll', methods=['POST'])
def enroll_course():
    data = request.json
    student_id = data.get('student_id')
    course_id = data.get('course_id')  # 修复：将schedule_id改为course_id（匹配存储过程参数）

    if not all([student_id, course_id]):  # 新增参数校验
        return jsonify({"code": 400, "msg": "学生ID和课程ID不能为空"})

    # ★★★ 核心修复：匹配存储过程参数（student_id, course_id）并处理返回结果 ★★★
    try:
        # 调用存储过程，第三个参数为OUT类型，接收返回结果
        # 假设db.call_procedure返回格式为：(('Success',),) 或 (('Already Enrolled',),) 等
        result = db.call_procedure('sp_student_enroll', (student_id, course_id, ''))
        p_result = result[0][0]  # 提取OUT参数结果

        if p_result == 'Success':
            return jsonify({"code": 200, "msg": "选课成功"})
        elif p_result == 'Already Enrolled':
            return jsonify({"code": 400, "msg": "已选过该课程，无法重复选课"})
        elif p_result == 'Course Full':
            return jsonify({"code": 400, "msg": "课程已满，无法选课"})
        else:
            return jsonify({"code": 500, "msg": f"选课失败：{p_result}"})

    except Exception as e:
        return jsonify({"code": 500, "msg": f"选课失败: {str(e)}"})

# 退课
@student_bp.route('/drop', methods=['POST'])
def drop_course():
    data = request.json
    student_id = data.get('student_id')
    course_id = data.get('course_id')

    if not all([student_id, course_id]):
        return jsonify({"code": 400, "msg": "参数不全"})

    try:
        sql = "DELETE FROM enrollment WHERE student_id = %s AND course_id = %s"
        rowcount = db.execute_update(sql, (student_id, course_id))
        if rowcount == 0:
            return jsonify({"code": 404, "msg": "未找到选课记录"})
        return jsonify({"code": 200, "msg": "退课成功"})
    except Exception as e:
        # 捕获触发器抛出的"已录入成绩无法退课"异常
        if "禁止删除：该课程已录入成绩，无法退课！" in str(e):
            return jsonify({"code": 403, "msg": "该课程已录入成绩，无法退课"})
        return jsonify({"code": 500, "msg": f"退课失败: {str(e)}"})

# 查看可选课
@student_bp.route('/available_courses', methods=['GET'])
def get_available_courses():
    student_id = request.args.get('student_id')
    
    # 已选课程ID
    enrolled_sql = "SELECT course_id FROM enrollment WHERE student_id = %s"
    enrolled_ids = [item['course_id'] for item in db.fetch_all(enrolled_sql, (student_id,))]
    
    # 可选课程（排除已选且有剩余容量）
    if enrolled_ids:
        placeholders = ', '.join(['%s'] * len(enrolled_ids))
        sql = f"""
        SELECT course_id, name as course_name, credits, capacity,
        (capacity - (SELECT COUNT(*) FROM enrollment WHERE course_id = c.course_id)) as remaining
        FROM course c
        WHERE course_id NOT IN ({placeholders})
        AND (capacity - (SELECT COUNT(*) FROM enrollment WHERE course_id = c.course_id)) > 0
        """
        courses = db.fetch_all(sql, enrolled_ids)
    else:
        sql = """
        SELECT course_id, name as course_name, credits, capacity,
        (capacity - (SELECT COUNT(*) FROM enrollment WHERE course_id = c.course_id)) as remaining
        FROM course c
        WHERE (capacity - (SELECT COUNT(*) FROM enrollment WHERE course_id = c.course_id)) > 0
        """
        courses = db.fetch_all(sql)
    
    return jsonify({"code": 200, "data": courses})

# 查看已选课
@student_bp.route('/enrolled_courses', methods=['GET'])
def get_enrolled_courses():
    student_id = request.args.get('student_id')
    sql = """
    SELECT c.course_id, c.name as course_name, c.credits, e.score, t.name as teacher_name
    FROM enrollment e
    JOIN course c ON e.course_id = c.course_id
    JOIN teacher t ON c.teacher_id = t.teacher_id
    WHERE e.student_id = %s
    """
    courses = db.fetch_all(sql, (student_id,))
    return jsonify({"code": 200, "data": courses})

# 修改个人信息
@student_bp.route('/update_profile', methods=['POST'])
def update_profile():
    data = request.json
    student_id = data.get('student_id')
    new_password = data.get('new_password')
    new_email = data.get('new_email')

    if not student_id:
        return jsonify({"code": 400, "msg": "学生ID不能为空"})
    
    # 构建更新字段
    updates = []
    params = []
    if new_password:
        updates.append("password = %s")
        params.append(new_password)
    if new_email:
        updates.append("email = %s")
        params.append(new_email)
    
    if not updates:
        return jsonify({"code": 400, "msg": "无更新内容"})
    
    sql = f"UPDATE student SET {', '.join(updates)} WHERE student_id = %s"
    params.append(student_id)
    
    rowcount = db.execute_update(sql, params)
    if rowcount == 0:
        return jsonify({"code": 404, "msg": "学生不存在"})
    return jsonify({"code": 200, "msg": "信息更新成功"})