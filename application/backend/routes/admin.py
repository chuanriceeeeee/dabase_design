from flask import Blueprint, request, jsonify
from db_helper import db

admin_bp = Blueprint('admin', __name__)

# 1. 专业管理（CRUD）
@admin_bp.route('/departments', methods=['GET'])
def get_departments():
    depts = db.fetch_all("SELECT * FROM department")
    return jsonify({"code": 200, "data": depts})

@admin_bp.route('/departments', methods=['POST'])
def add_department():
    data = request.json
    dept_id = data.get('dept_id')
    name = data.get('name')
    if not all([dept_id, name]):
        return jsonify({"code": 400, "msg": "参数不全"})
    sql = "INSERT INTO department (dept_id, name) VALUES (%s, %s)"
    db.execute_update(sql, (dept_id, name))
    return jsonify({"code": 200, "msg": "专业添加成功"})

@admin_bp.route('/departments/<dept_id>', methods=['PUT'])
def update_department(dept_id):
    name = request.json.get('name')
    if not name:
        return jsonify({"code": 400, "msg": "专业名称不能为空"})
    sql = "UPDATE department SET name = %s WHERE dept_id = %s"
    db.execute_update(sql, (name, dept_id))
    return jsonify({"code": 200, "msg": "专业更新成功"})

@admin_bp.route('/departments/<dept_id>', methods=['DELETE'])
def delete_department(dept_id):
    sql = "DELETE FROM department WHERE dept_id = %s"
    db.execute_update(sql, (dept_id,))
    return jsonify({"code": 200, "msg": "专业删除成功"})

# 2. 班级管理（类似专业CRUD，略）

# 3. 学生数据管理
@admin_bp.route('/students', methods=['GET'])
def get_students():
    sql = "SELECT * FROM student"
    students = db.fetch_all(sql)
    return jsonify({"code": 200, "data": students})

@admin_bp.route('/students', methods=['POST'])
def add_student():
    data = request.json
    # 简化处理，实际需校验所有必填字段
    sql = """
    INSERT INTO student (student_id, name, password, class_id, email, dept_id)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    db.execute_update(sql, (
        data['student_id'], data['name'], data['password'],
        data['class_id'], data.get('email', ''), data['dept_id']
    ))
    return jsonify({"code": 200, "msg": "学生添加成功"})

# 4. 课程数据管理（类似学生CRUD，略）

# 5. 生成选课情况报表
@admin_bp.route('/reports/enrollment', methods=['GET'])
def enrollment_report():
    sql = """
    SELECT c.course_id, c.name as course_name, 
    COUNT(e.student_id) as enrolled, c.capacity,
    (c.capacity - COUNT(e.student_id)) as remaining
    FROM course c
    LEFT JOIN enrollment e ON c.course_id = e.course_id
    GROUP BY c.course_id, c.name, c.capacity
    """
    report = db.fetch_all(sql)
    return jsonify({"code": 200, "data": report})

# 6. 给予管理员修改老师的role的权限（添加路由装饰器）
@admin_bp.route('/update_teacher_role', methods=['POST'])  # 新增路由装饰器
def update_teacher_role():
    data = request.json
    teacher_id = data.get('teacher_id')
    new_roll_type = data.get('roll_type')  # 只能是'teacher'/'admin'/'counselor'
    operator_id = data.get('operator_id')  # 操作人（必须是admin）

    # 验证操作人是管理员
    if not db.fetch_all(
        "SELECT 1 FROM teacher WHERE teacher_id = %s AND roll_type = 'admin'",
        (operator_id,)
    ):
        return jsonify({"code": 403, "msg": "无权限修改角色"})

    if new_roll_type not in ['teacher', 'admin', 'counselor']:
        return jsonify({"code": 400, "msg": "无效的角色类型"})

    # 更新roll_type
    db.execute_update(
        "UPDATE teacher SET roll_type = %s WHERE teacher_id = %s",
        (new_roll_type, teacher_id)
    )
    return jsonify({"code": 200, "msg": "角色更新成功"})