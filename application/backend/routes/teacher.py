# routes/teacher.py
from flask import Blueprint, request, jsonify
from db_helper import db
from routes.auth import token_required

teacher_bp = Blueprint('teacher', __name__)

# 1. 查看教授课程及选课学生名单
@teacher_bp.route('/courses', methods=['GET'])
@token_required
def get_taught_courses():
    # 仅教师/管理员可访问
    if request.role not in ['teacher', 'admin']:
        return jsonify({"code": 403, "msg": "无权限访问"}), 403
    
    teacher_id = request.user_id  # 从Token获取，避免伪造
    # 查看教授的课程
    courses_sql = """
    SELECT course_id, name as course_name, credits, capacity 
    FROM course 
    WHERE teacher_id = %s
    """
    courses = db.fetch_all(courses_sql, (teacher_id,))
    
    # 为每个课程添加选课学生
    for course in courses:
        students_sql = """
        SELECT s.student_id, s.name as student_name, e.score, e.status
        FROM enrollment e
        JOIN student s ON e.student_id = s.student_id
        WHERE e.course_id = %s
        """
        students = db.fetch_all(students_sql, (course['course_id'],))
        course['students'] = students
    
    return jsonify({"code": 200, "data": courses})

# 2. 录入/修改成绩
@teacher_bp.route('/update_score', methods=['POST'])
@token_required
def update_score():
    if request.role not in ['teacher', 'admin']:
        return jsonify({"code": 403, "msg": "无权限操作"}), 403
    
    data = request.json
    course_id = data.get('course_id')
    student_id = data.get('student_id')
    score = data.get('score')
    
    if not all([course_id, student_id, score]):
        return jsonify({"code": 400, "msg": "课程ID、学生ID、成绩不能为空"}), 400
    
    try:
        # 校验成绩范围
        score = float(score)
        if not (0 <= score <= 100):
            return jsonify({"code": 400, "msg": "成绩必须在0-100之间"}), 400
        
        # 校验该课程是否由当前教师授课
        check_sql = "SELECT 1 FROM course WHERE course_id = %s AND teacher_id = %s"
        if not db.fetch_all(check_sql, (course_id, request.user_id)) and request.role != 'admin':
            return jsonify({"code": 403, "msg": "无权限操作该课程成绩"}), 403
        
        # 更新成绩
        sql = """
        UPDATE enrollment 
        SET score = %s, status = 'completed' 
        WHERE course_id = %s AND student_id = %s
        """
        rowcount = db.execute_update(sql, (score, course_id, student_id))
        if rowcount == 0:
            return jsonify({"code": 404, "msg": "未找到该选课记录"}), 404
        return jsonify({"code": 200, "msg": "成绩更新成功"}), 200
    except ValueError:
        return jsonify({"code": 400, "msg": "成绩必须为数字"}), 400
    except Exception as e:
        return jsonify({"code": 500, "msg": f"操作失败：{str(e)}"}), 500

# 3. 课程成绩统计分析
@teacher_bp.route('/course_analysis', methods=['GET'])
@token_required
def course_analysis():
    if request.role not in ['teacher', 'admin', 'counselor']:
        return jsonify({"code": 403, "msg": "无权限访问"}), 403
    
    course_id = request.args.get('course_id')
    teacher_id = request.user_id
    
    # 非管理员需校验课程归属
    if request.role != 'admin':
        check_sql = "SELECT 1 FROM course WHERE course_id = %s AND teacher_id = %s"
        if not db.fetch_all(check_sql, (course_id, teacher_id)):
            return jsonify({"code": 403, "msg": "无权限分析该课程"}), 403
    
    # 统计数据
    sql = """
    SELECT 
        COUNT(*) as total_students,
        IFNULL(AVG(score), 0) as avg_score,
        IFNULL(SUM(CASE WHEN score >= 60 THEN 1 ELSE 0 END) / COUNT(*), 0) as pass_rate,
        IFNULL(MAX(score), 0) as max_score,
        IFNULL(MIN(score), 0) as min_score
    FROM enrollment 
    WHERE course_id = %s AND score IS NOT NULL
    """
    stats = db.fetch_all(sql, (course_id,))[0] if db.fetch_all(sql, (course_id,)) else {}
    
    return jsonify({"code": 200, "data": stats})