#!/usr/bin/env python3
"""
Post-send Hook - 发送后自动更新黑名单并删除中间文件

用法:
    python3 scripts/post_send_hook.py <已发送的文件.xlsx>
"""

import pandas as pd
import sys
import os

def update_blacklist(batch_file):
    """更新黑名单"""

    print("\n" + "="*60)
    print("🔄 Post-send Hook: 更新黑名单")
    print("="*60)

    # 读取刚发送的文件
    df = pd.read_excel(batch_file)
    sent_emails = set(df['email'].tolist())

    print(f"📧 本批发送: {len(sent_emails)} 个邮箱")

    # 读取现有黑名单
    blacklist_file = 'data/sent_emails_blacklist.txt'
    if os.path.exists(blacklist_file):
        with open(blacklist_file, 'r') as f:
            existing = set(line.strip() for line in f if line.strip())
    else:
        existing = set()

    original_count = len(existing)
    print(f"📋 黑名单原有: {original_count} 个邮箱")

    # 合并并排序
    all_emails = existing | sent_emails
    sorted_emails = sorted(all_emails)

    # 保存黑名单
    with open(blacklist_file, 'w') as f:
        for email in sorted_emails:
            f.write(f"{email}\n")

    new_count = len(sorted_emails)
    added_count = new_count - original_count

    print(f"✓ 黑名单已更新: {original_count} -> {new_count} (+{added_count})")

    # 删除中间文件
    print(f"\n🗑️  删除中间文件: {batch_file}")
    os.remove(batch_file)
    print("✓ 中间文件已删除")

    print("="*60)
    print("✓ Post-send Hook 完成")
    print("="*60)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 post_send_hook.py <已发送的文件.xlsx>')
        sys.exit(1)

    batch_file = sys.argv[1]

    if not os.path.exists(batch_file):
        print(f'错误: 文件不存在 {batch_file}')
        sys.exit(1)

    update_blacklist(batch_file)
