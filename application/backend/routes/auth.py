# routes/auth.py

from flask import Blueprint, request, jsonify
from db_helper import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')  # 工号（教师/管理员/辅导员共用teacher_id）
    password = data.get('password')
    role = data.get('role')  # 'admin', 'student', 'teacher', 'counselor'

    if not all([username, password, role]):
        return jsonify({"code": 400, "msg": "信息不完整"})

    # 角色映射调整：admin和counselor也从teacher表查询，通过roll_type区分
    table_map = {
        'student': {'table': 'Student', 'id_col': 'student_id'},
        # 管理员和辅导员存储在teacher表，通过roll_type验证
        'teacher': {'table': 'Teacher', 'id_col': 'teacher_id', 'roll_type': 'teacher'},
        'admin': {'table': 'Teacher', 'id_col': 'teacher_id', 'roll_type': 'admin'},
        'counselor': {'table': 'Teacher', 'id_col': 'teacher_id', 'roll_type': 'counselor'}
    }

    if role not in table_map:
        return jsonify({"code": 400, "msg": "无效的角色类型"})

    target = table_map[role]
    table_name = target['table']
    id_col = target['id_col']

    # 构造查询SQL：如果是teacher/admin/counselor，需要额外校验roll_type
    if table_name == 'Teacher':
        sql = f"SELECT * FROM {table_name} WHERE {id_col} = %s AND password = %s AND roll_type = %s"
        params = (username, password, target['roll_type'])
    else:
        # 学生表查询逻辑不变
        sql = f"SELECT * FROM {table_name} WHERE {id_col} = %s AND password = %s"
        params = (username, password)

    try:
        users = db.fetch_all(sql, params)
        if users:
            user = users[0]
            user.pop('password', None)
            return jsonify({
                "code": 200,
                "msg": "登录成功",
                "data": {
                    "token": "fake-jwt-token-for-demo",
                    "role": role,
                    "info": user
                }
            })
        else:
            return jsonify({"code": 401, "msg": "账号或密码错误，或角色不匹配"})
    except Exception as e:
        print(f"Login Error: {e}")
        return jsonify({"code": 500, "msg": "服务器内部错误"})