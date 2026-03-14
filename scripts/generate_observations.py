"""
为每个候选人生成个性化观察
使用MiniMax API分析GitHub profile并生成具体观察
支持并发处理提升速度
"""
import json
import os
import urllib.request
import urllib.parse
import ssl
import pandas as pd
import time
from dotenv import load_dotenv
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

# 加载API keys
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
MINIMAX_API_KEY = os.getenv('MINIMAX_API_KEY')

ctx = ssl.create_default_context()

def get_user_detail(username):
    """获取用户详细信息"""
    url = f'https://api.github.com/users/{username}'
    req = urllib.request.Request(url, headers={
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Mozilla/5.0'
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return json.loads(r.read())
    except:
        return None

def get_user_repos(username, max_repos=5):
    """获取用户最近的仓库"""
    url = f'https://api.github.com/users/{username}/repos?sort=updated&per_page={max_repos}'
    req = urllib.request.Request(url, headers={
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Mozilla/5.0'
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return json.loads(r.read())
    except:
        return []

def generate_observation(username, user_data, repos):
    """使用规则模板生成个性化观察（更稳定、更快）"""

    if not repos or len(repos) == 0:
        return "看到你在 GitHub 上的项目"

    # 获取第一个项目信息
    repo = repos[0]
    repo_name = repo.get('name', '')
    repo_desc = repo.get('description', '')
    repo_lang = repo.get('language', '')
    stars = repo.get('stargazers_count', 0)

    import random

    # 多种模板，随机选择
    templates = []

    # 类型1：项目名 + 描述片段
    if repo_desc and len(repo_desc) > 10:
        # 截取描述的前50个字符
        desc_short = repo_desc[:50].strip()
        if len(repo_desc) > 50:
            # 找到最后一个完整词
            last_space = desc_short.rfind(' ')
            if last_space > 20:
                desc_short = desc_short[:last_space]

        templates.append(f"{repo_name}，{desc_short}")
        templates.append(f"看到你的 {repo_name}，{desc_short}")
        templates.append(f"你在做的 {repo_name}，{desc_short}")

    # 类型2：项目名 + 技术栈 + 补充
    if repo_lang:
        templates.append(f"{repo_name}，{repo_lang} 写的")
        if stars > 50:
            templates.append(f"{repo_name}，{repo_lang} 项目，已经有 {stars} 个 star 了")
        elif stars > 10:
            templates.append(f"{repo_name}，{repo_lang} 实现的")

    # 类型3：项目名 + stars（如果有一定数量）
    if stars > 100:
        templates.append(f"{repo_name}，看到已经有 {stars} 个 star")
    elif stars > 50:
        templates.append(f"{repo_name}，{stars} 个 star")

    # 类型4：根据描述关键词生成
    if repo_desc:
        desc_lower = repo_desc.lower()
        if 'deep learning' in desc_lower or 'neural network' in desc_lower or 'pytorch' in desc_lower or 'tensorflow' in desc_lower:
            templates.append(f"{repo_name}，深度学习方向的")
        elif 'web' in desc_lower or 'http' in desc_lower or 'server' in desc_lower:
            templates.append(f"{repo_name}，Web 开发相关的")
        elif 'bot' in desc_lower or 'telegram' in desc_lower:
            templates.append(f"{repo_name}，Bot 开发")
        elif 'tool' in desc_lower or 'cli' in desc_lower:
            templates.append(f"{repo_name}，这个工具")
        elif 'library' in desc_lower or 'framework' in desc_lower:
            templates.append(f"{repo_name}，这个库")

    # 如果没有生成任何模板，使用基础模板
    if not templates:
        if repo_lang:
            templates.append(f"{repo_name}，{repo_lang} 项目")
        else:
            templates.append(f"看到你的 {repo_name}")

    # 随机选择一个模板
    observation = random.choice(templates)
    return observation

def process_single_candidate(idx, total, username):
    """处理单个候选人（用于并发）"""
    print(f"[{idx+1}/{total}] 处理 {username}...")

    # 获取用户信息
    user_data = get_user_detail(username)
    if not user_data:
        print(f"  ✗ {username}: 获取用户信息失败")
        return "看到你在 GitHub 上的项目"

    time.sleep(0.3)

    # 获取仓库信息
    repos = get_user_repos(username)
    time.sleep(0.3)

    # 生成观察
    observation = generate_observation(username, user_data, repos)
    print(f"  ✓ {username}: {observation[:50]}...")

    return observation

def process_batch(batch_file, max_workers=10):
    """处理一个batch文件，为每个候选人生成观察（并发）"""

    print(f"\n处理文件: {batch_file}")
    print(f"并发数: {max_workers}")
    df = pd.read_excel(batch_file)

    observations = [None] * len(df)

    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_idx = {
            executor.submit(process_single_candidate, idx, len(df), row['username']): idx
            for idx, row in df.iterrows()
        }

        # 收集结果
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                observation = future.result()
                observations[idx] = observation
            except Exception as e:
                print(f"  ✗ 处理失败: {e}")
                observations[idx] = "看到你在 GitHub 上的项目"

    # 添加observation列
    df['observation'] = observations

    # 保存
    df.to_excel(batch_file, index=False)
    print(f"\n✓ 已保存到 {batch_file}")

if __name__ == '__main__':
    import sys

    print("="*60)
    print("为候选人生成个性化观察")
    print("="*60)

    # 从命令行参数获取文件
    if len(sys.argv) > 1:
        batch_file = sys.argv[1]
        if os.path.exists(batch_file):
            process_batch(batch_file)
        else:
            print(f"\n❌ 文件不存在: {batch_file}")
            sys.exit(1)
    else:
        print("\n用法: python3 generate_observations.py <候选人文件.xlsx>")
        sys.exit(1)

    print("\n" + "="*60)
    print("✓ 完成！")
    print("="*60)
