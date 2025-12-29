# routes/counselor.py
from flask import Blueprint, request, jsonify
from db_helper import db
from routes.auth import token_required

counselor_bp = Blueprint('counselor', __name__)

# 模拟AI成绩分析（可替换为真实AI接口）
def analyze_student_grades(student_name, grades):
    failed_courses = [g for g in grades if g['score'] < 60]
    avg_score = sum([g['score'] for g in grades]) / len(grades) if grades else 0
    return {
        "student_name": student_name,
        "total_courses": len(grades),
        "failed_courses": len(failed_courses),
        "avg_score": round(avg_score, 2),
        "suggestion": "重点补习不及格课程" if failed_courses else "成绩良好，继续保持"
    }

# 1. 查看学生选课及成绩（按班级）
@counselor_bp.route('/class_grades', methods=['GET'])
@token_required
def get_class_grades():
    if request.role not in ['counselor', 'admin']:
        return jsonify({"code": 403, "msg": "无权限访问"}), 403
    
    class_id = request.args.get('class_id')
    if not class_id:
        return jsonify({"code": 400, "msg": "班级ID不能为空"}), 400
    
    sql = """
    SELECT s.student_id, s.name as student_name,
    c.name as course_name, g.score, g.credits
    FROM v_student_grades g
    JOIN student s ON g.student_id = s.student_id
    WHERE s.class_id = %s
    """
    grades = db.fetch_all(sql, (class_id,))
    return jsonify({"code": 200, "data": grades})

# 2. 重点标记不及格学生
@counselor_bp.route('/failed_students', methods=['GET'])
@token_required
def get_failed_students():
    if request.role not in ['counselor', 'admin']:
        return jsonify({"code": 403, "msg": "无权限访问"}), 403
    
    class_id = request.args.get('class_id')
    if not class_id:
        return jsonify({"code": 400, "msg": "班级ID不能为空"}), 400
    
    sql = """
    SELECT s.student_id, s.name as student_name,
    c.name as course_name, g.score
    FROM v_student_grades g
    JOIN student s ON g.student_id = s.student_id
    JOIN course c ON g.course_name = c.name
    WHERE s.class_id = %s AND g.score < 60
    """
    failed = db.fetch_all(sql, (class_id,))
    return jsonify({"code": 200, "data": failed})

# 3. 班级成绩统计分析
@counselor_bp.route('/class_analysis', methods=['GET'])
@token_required
def class_analysis():
    if request.role not in ['counselor', 'admin']:
        return jsonify({"code": 403, "msg": "无权限访问"}), 403
    
    class_id = request.args.get('class_id')
    if not class_id:
        return jsonify({"code": 400, "msg": "班级ID不能为空"}), 400
    
    sql = """
    SELECT 
        c.name as course_name,
        IFNULL(AVG(g.score), 0) as avg_score,
        IFNULL(SUM(CASE WHEN g.score < 60 THEN 1 ELSE 0 END), 0) as failed_count,
        COUNT(DISTINCT g.student_id) as total_students
    FROM v_student_grades g
    JOIN student s ON g.student_id = s.student_id
    JOIN course c ON g.course_name = c.name
    WHERE s.class_id = %s
    GROUP BY c.name
    """
    analysis = db.fetch_all(sql, (class_id,))
    return jsonify({"code": 200, "data": analysis})

# 4. 生成学术报表
@counselor_bp.route('/academic_report', methods=['GET'])
@token_required
def academic_report():
    if request.role not in ['counselor', 'admin']:
        return jsonify({"code": 403, "msg": "无权限访问"}), 403
    
    class_id = request.args.get('class_id')
    if not class_id:
        return jsonify({"code": 400, "msg": "班级ID不能为空"}), 400
    
    # 班级信息
    class_info = db.fetch_all("SELECT name FROM class WHERE class_id = %s", (class_id,))
    if not class_info:
        return jsonify({"code": 404, "msg": "班级不存在"}), 404
    
    # 不及格统计
    failed = db.fetch_all("""
        SELECT s.student_id, s.name as student_name, c.name as course_name, g.score
        FROM v_student_grades g
        JOIN student s ON g.student_id = s.student_id
        JOIN course c ON g.course_name = c.name
        WHERE s.class_id = %s AND g.score < 60
    """, (class_id,))
    
    # 成绩分析
    analysis = db.fetch_all("""
        SELECT 
            c.name as course_name,
            IFNULL(AVG(g.score), 0) as avg_score,
            IFNULL(SUM(CASE WHEN g.score < 60 THEN 1 ELSE 0 END), 0) as failed_count,
            COUNT(DISTINCT g.student_id) as total_students
        FROM v_student_grades g
        JOIN student s ON g.student_id = s.student_id
        JOIN course c ON g.course_name = c.name
        WHERE s.class_id = %s
        GROUP BY c.name
    """, (class_id,))
    
    return jsonify({
        "code": 200,
        "class_name": class_info[0]['name'],
        "failed_summary": f"共{len(failed)}条不及格记录",
        "course_analysis": analysis,
        "failed_details": failed
    })

# 5. 单个学生成绩分析（AI辅助）
@counselor_bp.route('/analyze_student', methods=['POST'])
@token_required
def analyze_student():
    if request.role not in ['counselor', 'admin']:
        return jsonify({"code": 403, "msg": "无权限访问"}), 403
    
    data = request.json
    student_id = data.get('student_id')
    if not student_id:
        return jsonify({"code": 400, "msg": "学生ID不能为空"}), 400
    
    # 查学生基本信息
    student = db.fetch_all("SELECT name FROM student WHERE student_id = %s", (student_id,))
    if not student:
        return jsonify({"code": 404, "msg": "学生不存在"}), 404
    
    # 查成绩
    grades_sql = """
    SELECT course_name, score FROM v_student_grades WHERE student_id = %s
    """
    grades = db.fetch_all(grades_sql, (student_id,))
    if not grades:
        return jsonify({"code": 404, "msg": "该学生无成绩记录"}), 404
    
    # AI分析
    report = analyze_student_grades(student[0]['name'], grades)
    return jsonify({
        "code": 200,
        "student_id": student_id,
        "ai_report": report
    })