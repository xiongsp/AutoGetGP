import os
import socket
import sys
import time
from email.mime.text import MIMEText
from smtplib import SMTP_SSL

from retry import retry
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

options = webdriver.ChromeOptions()
# 判断操作系统
if sys.platform == 'win32':
    b = webdriver.Edge()  # 调试用
else:
    options.add_argument("--headless")
    b = webdriver.Chrome(options=options)
error_times = 0

if os.path.exists('ENV.txt'):
    with open("ENV.txt", 'r') as file_to_write:
        env_str = file_to_write.read()
        for each_item in env_str.split(';'):
            os.environ[each_item.split('=')[0]] = each_item.split('=')[1]


@retry(tries=3, delay=1)
def get_info():
    IP = os.getenv("IP")
    PORT = os.getenv("PORT")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((IP, int(PORT)))
    s.send(b"GET!")
    info = s.recv(1024).decode("utf-8")
    print(info)
    return info


@retry(tries=3, delay=1)
def set_info(message):
    IP = os.getenv("IP")
    PORT = os.getenv("PORT")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((IP, int(PORT)))
    s.send(message.encode("utf-8"))
    info = s.recv(1024).decode("utf-8")
    if info == "OK":
        return True


def send_mail(subject, message):
    """
    :param subject: str 邮件主题描述
    :param message: str 邮件内容
    """
    # 填写真实的发邮件服务器用户名、密码
    user = os.getenv("USER_NAME")
    password = os.getenv("PASSWORD")
    to = os.getenv("TO")
    # 邮件内容
    msg = MIMEText(message, 'plain', _charset="utf-8")
    # 邮件主题描述
    msg["Subject"] = subject
    # 发件人
    msg["from"] = '成绩信息'
    with SMTP_SSL(host="smtp.qq.com", port=465) as smtp:
        # 登录发邮件服务器
        smtp.login(user=user, password=password)
        # 实际发送、接收邮件配置
        smtp.sendmail(from_addr=user, to_addrs=to, msg=msg.as_string())


def output(string):
    sys.stdout.write(string + "\r\n")
    sys.stdout.flush()


def finish(code):
    if code == 0:
        output("成功！")
    else:
        output("失败！")
    if sys.platform == 'win32':
        # os.system("taskkill /f /IM msedge.exe")
        os.system("taskkill /f /IM msedgedriver.exe")
    else:
        os.system("killall -9 chromedriver")
    exit(code)


@retry(tries=10, delay=2)
def login(username, password):
    b.get("https://uis.nwpu.edu.cn/cas/login?service=https://ecampus.nwpu.edu.cn/")
    user_box = WebDriverWait(b, 30).until(EC.presence_of_element_located((By.ID, 'username')))
    user_box.send_keys(username)
    pass_box = WebDriverWait(b, 30).until(EC.presence_of_element_located((By.ID, 'password')))
    pass_box.send_keys(password)  # 输入账号密码
    submit_button = WebDriverWait(b, 30).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/main/div/div/div[2]/div[3]/div/div[2]/div[3]/div/'
                                                  'div/div[1]/div[1]/form/div[4]/div/input[5]')))
    submit_button.click()
    output("步骤1-登录-成功！")


@retry(tries=10, delay=2)
def deal():
    # 执行
    record = []
    b.get('https://ecampus.nwpu.edu.cn/main.html#/Index')
    jw_button = WebDriverWait(b, 30).until(EC.presence_of_element_located(
        (By.XPATH, '/html/body/div[1]/div[1]/div[1]/div/section/div/div[1]/div[2]/div/div[2]/ul[1]/li[3]/span[1]')))
    jw_button.click()
    output("步骤2-前往教务系统-成功")
    time.sleep(4)
    b.get('https://jwxt.nwpu.edu.cn/student/for-std/grade/sheet/semester-index/273409')
    WebDriverWait(b, 300).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div[1]/table/tbody/tr[1]')))
    table = WebDriverWait(b, 30).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div[1]/table/tbody')))
    items = table.find_elements(By.XPATH, './tr')
    heads = table.find_elements(By.XPATH, '/html/body/div[1]/div[2]/div[1]/table/thead/tr/td')
    output("步骤3-表格获取-成功")
    for head in heads:
        print(head.text, end='\t')
    print()
    for item in items:
        class_name = item.find_element(By.XPATH, './td[1]/div[1]').text
        credit_num = item.find_element(By.XPATH, './td[2]').text
        gp_num = item.find_element(By.XPATH, './td[3]').text
        grade_num = item.find_element(By.XPATH, './td[4]').text
        print(class_name, end='\t')
        print(credit_num, end='\t')
        print(gp_num, end='\t')
        print(grade_num)
        record.append(str([class_name, credit_num, gp_num, grade_num]))
    get_data = get_info()
    if get_data is None:
        raise 'Get Error After Actively Retry'
    if get_data == 'None' or get_data != str(record):
        if set_info(str(record)):
            output("步骤4-发送成绩-成功！")
        if get_data != str(record) and get_data != 'None':
            send_mail('新成绩出了！', str(set(record).difference(set(eval(get_data)))))
    finish(0)


school_id = os.getenv('SCHOOL_ID')
school_password = os.getenv('SCHOOL_PSD')

login(school_id, school_password)
deal()
