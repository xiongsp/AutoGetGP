import os
import socket
import sys
import time
from email.mime.text import MIMEText
from smtplib import SMTP_SSL

from selenium import webdriver
from selenium.webdriver.common.by import By

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


def retry(retry_times, interval):
    def decorator(f):
        def wrap(*args, **kwargs):
            i = 0
            while retry_times and i < retry_times:
                try:
                    return f(*args, **kwargs)
                except ConnectionError:
                    i += 1
                    time.sleep(interval)
                    continue

        return wrap

    return decorator


@retry(retry_times=3, interval=1)
def get_info():
    try:
        IP = os.getenv("IP")
        PORT = os.getenv("PORT")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((IP, int(PORT)))
        s.send(b"GET!")
        info = s.recv(1024).decode("utf-8")
    except:
        time.sleep(1)
        return get_info()
    print(info)
    return info

@retry(retry_times=3, interval=1)
def set_info(message):
    try:
        IP = os.getenv("IP")
        PORT = os.getenv("PORT")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((IP, int(PORT)))
        s.send(message.encode("utf-8"))
        info = s.recv(1024).decode("utf-8")
    except:
        time.sleep(1)
        return set_info(message)
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


def deal(username, password, retry=False):
    try:
        # 执行
        record = []
        if not retry:
            b.get("https://uis.nwpu.edu.cn/cas/login?service=https://ecampus.nwpu.edu.cn/")
            b.find_element(By.ID, 'username').send_keys(username)
            b.find_element(By.ID, 'password').send_keys(password)  # 输入账号密码
            b.find_element(By.NAME, 'submit').click()
            output("步骤1-登录-成功！")
        time.sleep(1)
        b.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[1]/div/section/div/div[1]/div[2]/div/div[2]/ul[1]/li['
                                 '3]/span[1]').click()
        time.sleep(1)
        b.get('https://jwxt.nwpu.edu.cn/student/for-std/grade/sheet/semester-index/273409')
        time.sleep(3)
        table = b.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[1]/table/tbody')
        items = table.find_elements(By.XPATH, './tr')
        heads = table.find_elements(By.XPATH, '/html/body/div[1]/div[2]/div[1]/table/thead/tr/td')
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
                output("步骤2-发送成绩-成功！")
            if get_data != str(record) and get_data != 'None':
                send_mail('新成绩出了！', str(set(record).difference(set(eval(get_data)))))
        finish(0)

    except Exception as e:
        output(str(e))
        finish(1)
        send_mail('出错了！', str(e))


school_id = os.getenv('SCHOOL_ID')
school_password = os.getenv('SCHOOL_PSD')

deal(school_id, school_password)
