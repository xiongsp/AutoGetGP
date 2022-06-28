import base64
import os
from email.mime.text import MIMEText
from smtplib import SMTP_SSL

import requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from lxml import etree

from config import *


def send_mail(subject, message):
    """
    :param subject: str 邮件主题描述
    :param message: str 邮件内容
    """
    # 填写真实的发邮件服务器用户名、密码
    user = config_mail_username
    password = config_mail_password
    to = config_mail_to
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


def login(account, password):
    # 密码进行加密处理
    password = '__RSA__' + encrypt(password)

    user = requests.session()
    user.headers.update({'User-Agent': userAgent})
    getResult = user.get('https://uis.nwpu.edu.cn/cas/login')
    form_data_execution = str(etree.HTML(getResult.content).xpath('//input[@name="execution"]/@value')[0])
    header = {
        'origin': 'https://uis.nwpu.edu.cn',
        'referer': 'https://uis.nwpu.edu.cn/cas/login',
    }
    postData = {
        'username': account,
        'password': password,
        'currentMenu': 1,
        'execution': form_data_execution,
        '_eventId': 'submit',
        'geolocation': '',
        'submit': 'One moment please...'
    }
    login_result = user.post('https://uis.nwpu.edu.cn/cas/login', data=postData,
                             headers=header)

    if login_result.status_code == 500:
        print("login error:response HTTP 500")
        exit(0)

    cookie = user.cookies
    if "TGC" in dict(cookie).keys() and (login_result.text.find('欢迎使用') != -1):
        user.get("https://jwxt.nwpu.edu.cn/student/sso-login")
        return user
    else:
        raise ("login error, user account " + account)


def encrypt(content):
    content = bytes(content, "utf8")
    keyContent = requests.get("https://uis.nwpu.edu.cn/cas/jwt/publicKey").content
    pubKey = RSA.import_key(keyContent)
    cipherRSA = PKCS1_v1_5.new(pubKey)
    cipherText = base64.b64encode(cipherRSA.encrypt(content))
    return cipherText.decode('utf-8')


session_login = login(config_account, config_password)
response = session_login.get(config_url).json()
history = []
for item in response['semesterId2studentGrades']['178']:
    course_name = item['course']['nameZh']
    course_credits = item['course']['credits']
    course_gp = item['gp']
    course_score = item['gaGrade']
    print(f'{course_name}\t{course_credits}\t{course_gp}\t{course_score}')
    history.append(f'{course_name}\t{course_credits}\t{course_gp}\t{course_score}')

if os.path.exists('record.txt'):
    with open('record.txt', 'r') as f:
        old_history = f.read()
    if old_history != str(history):
        # send_mail('出新成绩了', str(set(history) - set(eval(old_history))))
        with open('record.txt', 'w') as f:
            f.write(str(history))
else:
    with open('record.txt', 'w') as f:
        f.write(str(history))
