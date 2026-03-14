#!/usr/bin/env python3
"""
Pre-send Hook脚本
在任何邮件发送前自动执行，强制检查黑名单
防止重复发送
"""
import sys
import os
import pandas as pd
import json
from pathlib import Path

def check_file_before_send(xlsx_file):
    """发送前强制检查"""
    print('\n' + '='*70)
    print('🛡️  PRE-SEND HOOK: 强制黑名单检查')
    print('='*70)

    if not os.path.exists(xlsx_file):
        print(f'❌ 文件不存在: {xlsx_file}')
        return False

    # 读取待发送文件
    df = pd.read_excel(xlsx_file)
    batch_emails = set(df['email'].tolist())

    print(f'\n📧 待发送邮箱数量: {len(batch_emails)}')

    # 检查1: 内部重复
    total = len(df)
    unique = df['email'].nunique()

    if total != unique:
        print(f'\n❌ 发现内部重复邮箱: {total - unique} 个')
        duplicates = df[df.duplicated(subset=['email'], keep=False)]
        for email in duplicates['email'].unique()[:5]:
            count = len(df[df['email'] == email])
            print(f'   - {email}: {count}次')
        print('\n🚫 阻止发送！请先去重！')
        return False

    print(f'✅ 内部重复检查: 通过 ({unique} 个唯一邮箱)')

    # 检查2: 黑名单
    blacklist_file = 'data/sent_emails_blacklist.txt'
    if not os.path.exists(blacklist_file):
        print(f'\n⚠️  黑名单文件不存在: {blacklist_file}')
        print('🚫 阻止发送！请先创建黑名单文件！')
        return False

    with open(blacklist_file, 'r') as f:
        blacklist = set(line.strip() for line in f if line.strip())

    print(f'📋 黑名单数量: {len(blacklist)}')

    # 检查交集
    in_blacklist = batch_emails & blacklist

    if in_blacklist:
        print(f'\n❌ 发现黑名单邮箱: {len(in_blacklist)} 个')
        for email in list(in_blacklist)[:10]:
            print(f'   - {email}')
        if len(in_blacklist) > 10:
            print(f'   ... 还有 {len(in_blacklist) - 10} 个')
        print('\n🚫 阻止发送！这些邮箱已经发送过！')
        return False

    print(f'✅ 黑名单检查: 通过 (0 个重复)')

    # 检查3: 邮件模板
    if 'observation' not in df.columns:
        print(f'\n⚠️  缺少observation列')
        print('🚫 阻止发送！请先生成个性化观察！')
        return False

    empty_obs = df[df['observation'].isna() | (df['observation'] == '')]
    if len(empty_obs) > 0:
        print(f'\n⚠️  发现 {len(empty_obs)} 个空observation')
        print('🚫 阻止发送！请确保所有候选人都有observation！')
        return False

    print(f'✅ Observation检查: 通过')

    print('\n' + '='*70)
    print('✅ 所有检查通过，允许发送')
    print('='*70 + '\n')

    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 pre_send_hook.py <待发送文件.xlsx>')
        sys.exit(1)

    xlsx_file = sys.argv[1]

    if check_file_before_send(xlsx_file):
        sys.exit(0)  # 通过检查
    else:
        sys.exit(1)  # 阻止发送
