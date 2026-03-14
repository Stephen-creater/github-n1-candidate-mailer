#!/usr/bin/env python3
"""
每日任务测试版 - 小规模测试自动化流程

用法:
    python3 scripts/daily_task_test.py

测试内容:
    - Gmail: 1封
    - QQ: 1封
    - 163: 1封
    - 总计: 3封邮件
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

    log(f"[测试] {description}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # 打印输出
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        error_msg = f"❌ 错误: {description} 失败 (退出码: {result.returncode})"
        print(f"\n{error_msg}")
        log(f"[测试] {error_msg}")
        sys.exit(1)

    log(f"[测试] ✓ {description} 完成")
    return result

def test_daily_task():
    """执行测试任务"""

    print("\n" + "="*70)
    print("🧪 开始测试自动化流程")
    print(f"📅 日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⚠️  测试模式：每个邮箱只发送1封")
    print("="*70)

    log("========== 开始测试任务 ==========")

    # 第一批：Gmail 1封
    print("\n" + "🔵"*35)
    print("测试批次1：Gmail 1封")
    print("🔵"*35)

    run_command(
        "python3 scripts/collect_candidates.py --count 5 --output data/test_batch1.xlsx",
        "收集测试候选人（5个）"
    )

    run_command(
        "python3 scripts/generate_observations.py data/test_batch1.xlsx",
        "生成observations"
    )

    # 只取第1个
    run_command(
        """python3 -c "
import pandas as pd
df = pd.read_excel('data/test_batch1.xlsx')
df.head(1).to_excel('data/test_gmail_1.xlsx', index=False)
print(f'✓ 已取1个候选人用于测试')
" """,
        "取1个候选人"
    )

    run_command(
        "python3 scripts/send_emails.py --xlsx data/test_gmail_1.xlsx --template data/email_template.txt --account gmail --yes",
        "发送测试邮件（Gmail，间隔2秒）"
    )

    # 删除临时文件
    if os.path.exists('data/test_batch1.xlsx'):
        os.remove('data/test_batch1.xlsx')
        print("✓ 已删除临时文件")

    # 第二批：QQ 1封
    print("\n" + "🟡"*35)
    print("测试批次2：QQ 1封")
    print("🟡"*35)

    run_command(
        "python3 scripts/collect_candidates.py --count 5 --output data/test_batch2.xlsx",
        "收集测试候选人（5个）"
    )

    run_command(
        "python3 scripts/generate_observations.py data/test_batch2.xlsx",
        "生成observations"
    )

    # 只取第1个
    run_command(
        """python3 -c "
import pandas as pd
df = pd.read_excel('data/test_batch2.xlsx')
df.head(1).to_excel('data/test_qq_1.xlsx', index=False)
print(f'✓ 已取1个候选人用于测试')
" """,
        "取1个候选人"
    )

    run_command(
        "python3 scripts/send_emails.py --xlsx data/test_qq_1.xlsx --template data/email_template.txt --account qq --yes",
        "发送测试邮件（QQ，间隔8秒）"
    )

    # 删除临时文件
    if os.path.exists('data/test_batch2.xlsx'):
        os.remove('data/test_batch2.xlsx')
        print("✓ 已删除临时文件")

    # 第三批：163 1封
    print("\n" + "🟢"*35)
    print("测试批次3：163 1封")
    print("🟢"*35)

    run_command(
        "python3 scripts/collect_candidates.py --count 5 --output data/test_batch3.xlsx",
        "收集测试候选人（5个）"
    )

    run_command(
        "python3 scripts/generate_observations.py data/test_batch3.xlsx",
        "生成observations"
    )

    # 只取第1个
    run_command(
        """python3 -c "
import pandas as pd
df = pd.read_excel('data/test_batch3.xlsx')
df.head(1).to_excel('data/test_163_1.xlsx', index=False)
print(f'✓ 已取1个候选人用于测试')
" """,
        "取1个候选人"
    )

    run_command(
        "python3 scripts/send_emails.py --xlsx data/test_163_1.xlsx --template data/email_template.txt --account 163 --yes",
        "发送测试邮件（163，间隔2秒）"
    )

    # 删除临时文件
    if os.path.exists('data/test_batch3.xlsx'):
        os.remove('data/test_batch3.xlsx')
        print("✓ 已删除临时文件")

    # 完成
    print("\n" + "="*70)
    print("✅ 测试完成！")
    print("="*70)
    print(f"📧 总计发送: 3封测试邮件")
    print(f"  - Gmail: 1封（间隔2秒）")
    print(f"  - QQ: 1封（间隔8秒）")
    print(f"  - 163: 1封（间隔2秒）")
    print(f"\n🔍 请检查:")
    print(f"  1. Pre-send Hook是否正常检查")
    print(f"  2. 邮件是否发送成功")
    print(f"  3. Post-send Hook是否自动更新黑名单")
    print(f"  4. 中间文件是否被删除")
    print(f"  5. 黑名单数量: 1005 -> 1008 (+3)")
    print("="*70)

    log("========== 测试完成 ==========")
    log("📊 总结: 成功3封测试邮件")

if __name__ == '__main__':
    try:
        test_daily_task()
    except KeyboardInterrupt:
        log("[测试] ⚠️ 用户中断测试")
        print("\n\n⚠️  用户中断测试")
        sys.exit(1)
    except Exception as e:
        log(f"[测试] ❌ 发生错误: {e}")
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
