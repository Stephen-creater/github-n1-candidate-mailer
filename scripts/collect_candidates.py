#!/usr/bin/env python3
"""
收集GitHub候选人 - 自动补充直到凑满目标数量

用法:
    python3 scripts/collect_candidates.py --count 50 --output data/candidates_new.xlsx

特点:
    - 自动过滤黑名单
    - 自动补充直到凑满目标数量
    - 使用分页和随机化避免重复
    - 扩大followers范围到1000
"""

import argparse
import os
import sys
import time
import random
import pandas as pd
from dotenv import load_dotenv
import requests

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def search_github_users(location, min_followers=50, max_followers=1000, min_repos=6, per_page=30, page=1):
    """搜索GitHub用户（支持分页）"""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}

    query = f'location:{location} followers:{min_followers}..{max_followers} repos:>{min_repos}'
    url = f'https://api.github.com/search/users?q={query}&per_page={per_page}&page={page}'

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('items', [])
    return []

def get_user_details(username):
    """获取用户详细信息"""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    url = f'https://api.github.com/users/{username}'

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def load_blacklist():
    """加载黑名单"""
    blacklist_file = 'data/sent_emails_blacklist.csv'
    if os.path.exists(blacklist_file):
        import pandas as pd
        df = pd.read_csv(blacklist_file)
        return set(df['email'].tolist())
    return set()

def collect_candidates(target_count, min_followers=50, max_followers=1000, min_repos=6):
    """收集候选人 - 保证返回target_count个全新候选人"""

    # 中国主要城市
    locations = [
        'Beijing', 'Shanghai', 'Shenzhen', 'Hangzhou', 'Guangzhou',
        'Chengdu', 'Nanjing', 'Wuhan', 'Xi\'an', 'Suzhou',
        'Chongqing', 'Tianjin', 'Dalian', 'Xiamen', 'Qingdao'
    ]

    print(f"🎯 目标: 收集 {target_count} 个全新候选人（过滤黑名单后）")
    print(f"📋 条件: followers {min_followers}-{max_followers}, repos >{min_repos}")
    print("="*60)

    # 加载黑名单
    blacklist = load_blacklist()
    print(f"📋 黑名单: {len(blacklist)} 个邮箱")

    all_candidates = []
    seen_usernames = set()
    seen_emails = set()

    round_num = 1
    max_rounds = 20  # 最多尝试20轮

    while len(all_candidates) < target_count and round_num <= max_rounds:
        print(f"\n{'='*60}")
        print(f"🔄 第 {round_num} 轮收集")
        print(f"当前已有: {len(all_candidates)} 个，还需: {target_count - len(all_candidates)} 个")
        print(f"{'='*60}")

        round_candidates = []

        # 随机打乱城市顺序
        random.shuffle(locations)

        for location in locations:
            if len(all_candidates) >= target_count:
                break

            # 随机选择页码（1-10页）
            page = random.randint(1, 10)

            print(f"\n搜索 {location} (第{page}页)...")
            users = search_github_users(location, min_followers, max_followers, min_repos, per_page=30, page=page)

            for user in users:
                username = user['login']

                # 跳过已见过的用户
                if username in seen_usernames:
                    continue

                seen_usernames.add(username)

                # 获取详细信息
                details = get_user_details(username)
                if not details:
                    continue

                # 过滤组织账号
                user_type = details.get('type', '')
                if user_type == 'Organization':
                    print(f"  ✗ 跳过组织账号: {username}")
                    continue

                email = details.get('email')
                if not email:
                    continue

                # 跳过重复邮箱
                if email in seen_emails:
                    continue

                # 跳过黑名单邮箱
                if email in blacklist:
                    print(f"  ✗ 黑名单: {username} ({email})")
                    continue

                seen_emails.add(email)

                candidate = {
                    'name': details.get('name', ''),
                    'username': username,
                    'email': email,
                    'bio': details.get('bio', ''),
                    'location': details.get('location', ''),
                    'repos': details.get('public_repos', 0),
                    'followers': details.get('followers', 0),
                    'profile_url': details.get('html_url', ''),
                    'created_at': details.get('created_at', '')
                }

                all_candidates.append(candidate)
                round_candidates.append(candidate)
                print(f"  ✓ [{len(all_candidates)}/{target_count}] {username} ({email})")

                # 达到目标，停止
                if len(all_candidates) >= target_count:
                    break

            # 避免API限流
            time.sleep(0.5)

        print(f"\n本轮收集: {len(round_candidates)} 个新候选人")

        # 如果本轮没有收集到任何新候选人，说明候选人池已耗尽
        if len(round_candidates) == 0:
            print(f"\n⚠️  警告: 本轮未收集到新候选人，候选人池可能已耗尽")
            break

        round_num += 1

    print("\n" + "="*60)
    if len(all_candidates) >= target_count:
        print(f"✅ 成功收集 {len(all_candidates)} 个全新候选人")
        return all_candidates[:target_count]  # 返回正好target_count个
    else:
        print(f"⚠️  只收集到 {len(all_candidates)} 个候选人（目标: {target_count}）")
        print(f"建议: 扩大搜索范围或调整筛选条件")
        return all_candidates

def main():
    parser = argparse.ArgumentParser(description='收集GitHub候选人')
    parser.add_argument('--count', type=int, required=True, help='目标候选人数量')
    parser.add_argument('--output', type=str, required=True, help='输出文件路径')
    parser.add_argument('--min-followers', type=int, default=50, help='最小followers数')
    parser.add_argument('--max-followers', type=int, default=1000, help='最大followers数')
    parser.add_argument('--min-repos', type=int, default=6, help='最小repos数')

    args = parser.parse_args()

    candidates = collect_candidates(
        args.count,
        args.min_followers,
        args.max_followers,
        args.min_repos
    )

    if not candidates:
        print("\n❌ 未收集到任何候选人")
        sys.exit(1)

    # 保存到Excel
    df = pd.DataFrame(candidates)
    # 清理所有字符串字段中的非法字符
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: ''.join(c for c in str(x) if c.isprintable() or c in '\n\r\t') if pd.notna(x) else x)
    df.to_excel(args.output, index=False)

    print(f"✓ 已保存到: {args.output}")
    print("="*60)

if __name__ == '__main__':
    main()
