#!/usr/bin/env python3
"""
每日自动化任务 - 一键完成每日150封邮件

用法:
    python3 scripts/daily_task.py

功能:
    - 自动收集候选人（3批 × 55个，预留10%缓冲）
    - 自动生成observations（3批 × 55个）
    - 自动发送邮件（Gmail 50 + QQ 50 + 163 50）
    - 自动更新黑名单（Post-send Hook）
    - 自动删除中间文件
    - 出错立即停止并报告
"""

import subprocess
import sys
import os
from datetime import datetime
from logger import log

def run_command(cmd, description):
    """运行命令并检查结果"""
    print("\n" + "="*70)
    print(f"📋 {description}")
    print("="*70)

    log(description)

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # 打印输出
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        error_msg = f"❌ 错误: {description} 失败 (退出码: {result.returncode})"
        print(f"\n{error_msg}")
        log(error_msg)
        sys.exit(1)

    log(f"✓ {description} 完成")
    return result

def daily_task():
    """执行每日任务"""

    print("\n" + "="*70)
    print("🚀 开始每日自动化任务")
    print(f"📅 日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    log("========== 开始每日任务 ==========")

    # 第一批：Gmail 50封
    print("\n" + "🔵"*35)
    print("第一批：Gmail 50封")
    print("🔵"*35)

    run_command(
        "python3 scripts/collect_candidates.py --count 55 --output data/batch1_55.xlsx",
        "收集第一批候选人（55个，预留10%缓冲）"
    )

    run_command(
        "python3 scripts/generate_observations.py data/batch1_55.xlsx",
        "生成第一批observations"
    )

    # 取前50个
    run_command(
        """python3 -c "
import pandas as pd
df = pd.read_excel('data/batch1_55.xlsx')
df.head(50).to_excel('data/batch1_50.xlsx', index=False)
print(f'✓ 已取前50个候选人')
" """,
        "取前50个候选人"
    )

    run_command(
        "python3 scripts/send_emails.py --xlsx data/batch1_50.xlsx --template data/email_template.txt --account gmail --yes",
        "发送第一批邮件（Gmail，间隔2秒）"
    )

    # 删除临时文件
    if os.path.exists('data/batch1_55.xlsx'):
        os.remove('data/batch1_55.xlsx')
        print("✓ 已删除临时文件 batch1_55.xlsx")

    # 第二批：QQ 50封
    print("\n" + "🟡"*35)
    print("第二批：QQ 50封")
    print("🟡"*35)

    run_command(
        "python3 scripts/collect_candidates.py --count 55 --output data/batch2_55.xlsx",
        "收集第二批候选人（55个，预留10%缓冲）"
    )

    run_command(
        "python3 scripts/generate_observations.py data/batch2_55.xlsx",
        "生成第二批observations"
    )

    # 取前50个
    run_command(
        """python3 -c "
import pandas as pd
df = pd.read_excel('data/batch2_55.xlsx')
df.head(50).to_excel('data/batch2_50.xlsx', index=False)
print(f'✓ 已取前50个候选人')
" """,
        "取前50个候选人"
    )

    run_command(
        "python3 scripts/send_emails.py --xlsx data/batch2_50.xlsx --template data/email_template.txt --account qq --yes",
        "发送第二批邮件（QQ，间隔8秒）"
    )

    # 删除临时文件
    if os.path.exists('data/batch2_55.xlsx'):
        os.remove('data/batch2_55.xlsx')
        print("✓ 已删除临时文件 batch2_55.xlsx")

    # 第三批：163 50封
    print("\n" + "🟢"*35)
    print("第三批：163 50封")
    print("🟢"*35)

    run_command(
        "python3 scripts/collect_candidates.py --count 55 --output data/batch3_55.xlsx",
        "收集第三批候选人（55个，预留10%缓冲）"
    )

    run_command(
        "python3 scripts/generate_observations.py data/batch3_55.xlsx",
        "生成第三批observations"
    )

    # 取前50个
    run_command(
        """python3 -c "
import pandas as pd
df = pd.read_excel('data/batch3_55.xlsx')
df.head(50).to_excel('data/batch3_50.xlsx', index=False)
print(f'✓ 已取前50个候选人')
" """,
        "取前50个候选人"
    )

    run_command(
        "python3 scripts/send_emails.py --xlsx data/batch3_50.xlsx --template data/email_template.txt --account 163 --yes",
        "发送第三批邮件（163，间隔2秒）"
    )

    # 删除临时文件
    if os.path.exists('data/batch3_55.xlsx'):
        os.remove('data/batch3_55.xlsx')
        print("✓ 已删除临时文件 batch3_55.xlsx")

    # 完成
    print("\n" + "="*70)
    print("✅ 每日任务完成！")
    print("="*70)
    print(f"📧 总计发送: 150封邮件")
    print(f"  - Gmail: 50封（间隔2秒）")
    print(f"  - QQ: 50封（间隔8秒）")
    print(f"  - 163: 50封（间隔2秒）")
    print(f"🛡️  黑名单已自动更新")
    print(f"🗑️  中间文件已自动删除")
    print("="*70)

    log("========== 任务完成 ==========")
    log("📊 总结: 成功150封, Gmail 50 + QQ 50 + 163 50")

if __name__ == '__main__':
    try:
        daily_task()
    except KeyboardInterrupt:
        log("⚠️ 用户中断任务")
        print("\n\n⚠️  用户中断任务")
        sys.exit(1)
    except Exception as e:
        log(f"❌ 发生错误: {e}")
        print(f"\n\n❌ 发生错误: {e}")
        sys.exit(1)
