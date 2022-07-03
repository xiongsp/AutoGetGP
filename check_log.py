import os

history_data = []
history_time = []
coding_method = 'utf-8'

if os.path.exists('./log'):
    # 列出文件夹下文件
    files = os.listdir('./log')
    files.sort()
    # 按照时间顺序排序
    for file in files:
        if file.endswith('.log'):
            with open('./log/' + file, 'rb') as f:
                f.seek(-30, 2)
                lines = f.readlines()
                last_line = lines[-1]
                f.seek(0)
                for line in f:
                    if len(history_data) == 0 or line[20:].decode(
                            coding_method) != history_data[-1]:
                        history_data.append(line[20:].decode(coding_method))
                        history_time.append(line[:19].decode(coding_method))
                        # print(line.decode(coding_method))
                    # 如果是最后一行
                    if last_line == line:
                        history_data.append(line[20:].decode(coding_method))
                        history_time.append(line[:19].decode(coding_method))
            print("-" * 10 + "新的一天" + "-" * 10)
            for time, data in zip(history_time, history_data):
                print(time, data)
            history_data, history_time = [], []
            # print(history_data)
            # print(history_time)
