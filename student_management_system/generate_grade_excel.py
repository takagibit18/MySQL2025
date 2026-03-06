"""
生成张老师课程成绩导入Excel示例文件
用于演示教师端一键导入成绩功能
"""
import pandas as pd
from pathlib import Path

# 张老师（T001）的课程和学生数据
# 注意：只使用数据库中真实存在的学号和选课记录
# COURSE001 - Python程序设计
# 根据database.sql，COURSE001的选课学生：2021001001, 2021001002
python_course_data = [
    {'学号': '2021001001', '平时成绩': 85.0, '期末成绩': 90.0, '总成绩': 88.5},
    {'学号': '2021001002', '平时成绩': 80.0, '期末成绩': 85.0, '总成绩': 83.5},
]

# COURSE002 - 数据库原理
# 根据database.sql，COURSE002的选课学生：2021001001
database_course_data = [
    {'学号': '2021001001', '平时成绩': 90.0, '期末成绩': 95.0, '总成绩': 93.5},
]

def create_excel_file(data, filename, course_name):
    """创建Excel文件"""
    # 创建DataFrame，按照导入要求的列顺序：学号、平时成绩、期末成绩、总成绩
    df = pd.DataFrame(data, columns=['学号', '平时成绩', '期末成绩', '总成绩'])
    
    # 保存为Excel文件
    output_path = Path(__file__).parent / filename
    df.to_excel(output_path, index=False, sheet_name='成绩表')
    
    print(f"[OK] 已生成: {filename}")
    print(f"  课程: {course_name}")
    print(f"  学生数: {len(data)}")
    print(f"  文件路径: {output_path}")
    print()

if __name__ == '__main__':
    # 确保输出目录存在
    output_dir = Path(__file__).parent
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("生成张老师课程成绩导入Excel示例文件")
    print("=" * 60)
    print()
    
    # 生成Python程序设计课程的成绩表
    create_excel_file(
        python_course_data,
        '张老师_Python程序设计_成绩表.xlsx',
        'Python程序设计 (COURSE001)'
    )
    
    # 生成数据库原理课程的成绩表
    create_excel_file(
        database_course_data,
        '张老师_数据库原理_成绩表.xlsx',
        '数据库原理 (COURSE002)'
    )
    
    print("=" * 60)
    print("生成完成！")
    print("=" * 60)
    print()
    print("使用说明：")
    print("1. 在教师端登录（工号：T001，密码：123456）")
    print("2. 进入'成绩管理'页面")
    print("3. 选择对应课程")
    print("4. 点击'Excel批量导入'按钮")
    print("5. 选择生成的Excel文件上传")
    print()
    print("注意：")
    print("- Excel文件格式：第一列学号，第二列平时成绩，第三列期末成绩，第四列总成绩")
    print("- 如果总成绩列为空，系统会自动计算：总成绩 = 平时成绩×0.3 + 期末成绩×0.7")
    print("- 确保Excel中的学号对应的学生已经选课")

