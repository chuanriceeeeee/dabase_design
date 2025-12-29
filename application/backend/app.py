# app.py

from flask import Flask
from flask_cors import CORS
import config  # 导入配置

# 导入路由模块
from routes.auth import auth_bp
from routes.student import student_bp
from routes.counselor import counselor_bp
# 12-29 此处新增teacher和admin
from routes.teacher import teacher_bp
from routes.admin import admin_bp
app = Flask(__name__)
# 加载配置
app.config.from_object(config)
CORS(app) # 解决跨域问题

# 注册蓝图 (Blueprints)
app.register_blueprint(auth_bp, url_prefix='/api/auth')         # 登录接口变成 /api/auth/login
app.register_blueprint(student_bp, url_prefix='/api/student')   # 学生接口
app.register_blueprint(counselor_bp, url_prefix='/api/counselor') # 辅导员接口
app.register_blueprint(teacher_bp, url_prefix='/api/teacher')   # 教师接口
app.register_blueprint(admin_bp, url_prefix='/api/admin')       # 管理员接口

@app.route('/')
def index():
    return "Teaching System Backend is Running!"

if __name__ == '__main__':
    app.run(debug=True, port=5000)