# 1.命名:
## 1.1 enrollment表
- enrollment_id改为course_id
- score设置可为空
## 1.2 角色名
- role_student
- role_teacher
- role_counselor
- role_admin
# 2

# 2.后端
dabase_design\application\backend\routes\auth.py
22行
   table_map = {
        'student': {'table': 'Student', 'id_col': 'student_id'},
        'teacher': {'table': 'Teacher', 'id_col': 'teacher_id'},
        'counselor': {'table': 'Counselor', 'id_col': 'counselor_id'},
        'admin': {'table': 'Admin', 'id_col': 'admin_id'}
    }
表结构未修正