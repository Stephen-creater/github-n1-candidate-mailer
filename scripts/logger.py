#!/usr/bin/env python3
"""
极简日志工具 - 自动记录到logs/目录,保留7天
"""
import os
from datetime import datetime, timedelta

LOG_DIR = 'logs'

def log(message):
    """记录日志到今天的文件"""
    os.makedirs(LOG_DIR, exist_ok=True)

    today = datetime.now().strftime('%Y-%m-%d')
    log_file = f'{LOG_DIR}/{today}.log'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {message}\n')

    # 删除7天前的日志
    cutoff = datetime.now() - timedelta(days=7)
    for filename in os.listdir(LOG_DIR):
        if filename.endswith('.log'):
            try:
                file_date = datetime.strptime(filename[:-4], '%Y-%m-%d')
                if file_date < cutoff:
                    os.remove(f'{LOG_DIR}/{filename}')
            except:
                pass
