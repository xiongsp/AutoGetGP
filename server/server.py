import os
import socket
import time


def log(message):
    print(message)
    # 日期格式 YYYY-MM-DD
    with open(f'{time.strftime("%Y-%m-%d")}.log', 'a') as file_to_write:
        file_to_write.write(message + '\n')


try:
    # 建立tcp服务端
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 23333))
    s.listen(1)
    # 接收客户端连接
    conn, addr = s.accept()
    log(f'{time.ctime()} 连接地址：{addr}')
    # 接收客户端发送的数据
    while True:
        data = conn.recv(1024)
        if not data:
            break
        log(f"收到数据：{data.decode('utf-8')}")
        if data.decode('utf-8') == 'GET!':
            if os.path.exists('record.txt'):
                with open('record.txt', 'r') as f:
                    send_data = f.read()
            else:
                send_data = 'None'
        else:
            with open('record.txt', 'w') as f:
                f.write(data.decode('utf-8'))
            send_data = 'OK'
        conn.send(send_data.encode('utf-8'))
    conn.close()
    s.close()
    exit(0)
except Exception as e:
    log(f'{time.ctime()} {e}')
    exit(1)
