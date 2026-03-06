from django import forms
from django.db import connection


class StudentForm(forms.Form):
    """学生表单 - 使用ModelForm风格"""
    学号 = forms.CharField(max_length=12, label="学号", required=True)
    姓名 = forms.CharField(max_length=50, label="姓名", required=True)
    性别 = forms.ChoiceField(choices=[('M', '男'), ('F', '女')], label="性别", required=True)
    出生日期 = forms.DateField(label="出生日期", required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    手机号 = forms.CharField(max_length=11, label="手机号", required=True)
    邮箱 = forms.EmailField(label="邮箱", required=False)
    班级ID = forms.CharField(max_length=10, label="班级ID", required=False)
    入学日期 = forms.DateField(label="入学日期", required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    密码 = forms.CharField(max_length=100, label="密码", required=True, widget=forms.PasswordInput())
    状态 = forms.ChoiceField(choices=[(1, '在校'), (0, '离校')], label="状态", initial=1, required=True)


class TeacherForm(forms.Form):
    """教师表单 - 使用ModelForm风格"""
    工号 = forms.CharField(max_length=10, label="工号", required=True)
    姓名 = forms.CharField(max_length=50, label="姓名", required=True)
    性别 = forms.ChoiceField(choices=[('M', '男'), ('F', '女')], label="性别", required=True)
    手机号 = forms.CharField(max_length=11, label="手机号", required=True)
    邮箱 = forms.EmailField(label="邮箱", required=False)
    职称 = forms.CharField(max_length=20, label="职称", required=False)
    部门 = forms.CharField(max_length=50, label="部门", required=False)
    密码 = forms.CharField(max_length=100, label="密码", required=True, widget=forms.PasswordInput())
    状态 = forms.ChoiceField(choices=[(1, '在职'), (0, '离职')], label="状态", initial=1, required=True)


class CourseForm(forms.Form):
    """课程表单 - 使用ModelForm风格"""
    课程ID = forms.CharField(max_length=10, label="课程ID", required=True)
    课程名称 = forms.CharField(max_length=100, label="课程名称", required=True)
    课程代码 = forms.CharField(max_length=20, label="课程代码", required=False)
    学分 = forms.DecimalField(max_digits=3, decimal_places=1, label="学分", required=True)
    授课教师工号 = forms.CharField(max_length=10, label="授课教师工号", required=False)
    上课时间 = forms.CharField(max_length=100, label="上课时间", required=False)
    上课地点 = forms.CharField(max_length=50, label="上课地点", required=False)
    课程状态 = forms.ChoiceField(choices=[(1, '开课'), (0, '停课')], label="课程状态", initial=1, required=True)


class ClassForm(forms.Form):
    """班级表单 - 使用ModelForm风格"""
    班级ID = forms.CharField(max_length=10, label="班级ID", required=True)
    班级名称 = forms.CharField(max_length=50, label="班级名称", required=True)
    专业 = forms.CharField(max_length=50, label="专业", required=False)
    年级 = forms.CharField(max_length=10, label="年级", required=False)
    班主任工号 = forms.CharField(max_length=10, label="班主任工号", required=False)

