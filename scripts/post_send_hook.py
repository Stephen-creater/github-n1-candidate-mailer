#!/usr/bin/env python3
"""
Post-send Hook - 发送后自动更新黑名单并删除中间文件

用法:
    python3 scripts/post_send_hook.py <已发送的文件.xlsx> <账户名>
"""

import pandas as pd
import sys
import os
from datetime import datetime

BLACKLIST_FILE = 'data/sent_emails_blacklist.csv'

def load_blacklist_emails():
    """加载黑名单中已有的邮箱集合"""
    if os.path.exists(BLACKLIST_FILE):
        df = pd.read_csv(BLACKLIST_FILE)
        return set(df['email'].tolist())
    return set()

def update_blacklist(batch_file, account='unknown'):
    """更新黑名单"""

    print("\n" + "="*60)
    print("🔄 Post-send Hook: 更新黑名单")
    print("="*60)

    # 读取刚发送的文件
    df = pd.read_excel(batch_file)
    print(f"📧 本批发送: {len(df)} 个邮箱")

    # 读取现有黑名单
    if os.path.exists(BLACKLIST_FILE):
        existing_df = pd.read_csv(BLACKLIST_FILE)
        existing_emails = set(existing_df['email'].tolist())
    else:
        existing_df = pd.DataFrame()
        existing_emails = set()

    original_count = len(existing_emails)
    print(f"📋 黑名单原有: {original_count} 个邮箱")

    # 只添加新邮箱
    sent_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_rows = []
    for _, row in df.iterrows():
        email = row.get('email', '')
        if email and email not in existing_emails:
            new_rows.append({
                'username': row.get('username', ''),
                'name': row.get('name', ''),
                'email': email,
                'bio': row.get('bio', ''),
                'location': row.get('location', ''),
                'repos': row.get('repos', ''),
                'followers': row.get('followers', ''),
                'profile_url': row.get('profile_url', ''),
                'created_at': row.get('created_at', ''),
                'observation': row.get('observation', ''),
                'sent_at': sent_at,
                'sent_account': account,
            })

    if new_rows:
        new_df = pd.DataFrame(new_rows)
        combined = pd.concat([existing_df, new_df], ignore_index=True) if not existing_df.empty else new_df
        combined.to_csv(BLACKLIST_FILE, index=False)

    new_count = original_count + len(new_rows)
    print(f"✓ 黑名单已更新: {original_count} -> {new_count} (+{len(new_rows)})")

    # 删除中间文件
    print(f"\n🗑️  删除中间文件: {batch_file}")
    os.remove(batch_file)
    print("✓ 中间文件已删除")

    print("="*60)
    print("✓ Post-send Hook 完成")
    print("="*60)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 post_send_hook.py <已发送的文件.xlsx> [账户名]')
        sys.exit(1)

    batch_file = sys.argv[1]
    account = sys.argv[2] if len(sys.argv) > 2 else 'unknown'

    if not os.path.exists(batch_file):
        print(f'错误: 文件不存在 {batch_file}')
        sys.exit(1)

    update_blacklist(batch_file, account)
