# GitHub N1候选人邮件发送系统

自动化招聘工具，从GitHub收集高质量开发者候选人并发送个性化邮件。

## 🚀 快速开始

### 每日任务（150封邮件）

```bash
# 一键执行
python3 scripts/daily_task.py
```

### 测试模式（3封邮件）

```bash
# 测试流程
python3 scripts/daily_task_test.py
```

## 🚨 核心原则

1. **绝对不可重复触达同一候选人**
2. **每天3个邮箱各发50封**（不自动补发失败邮件）

## 📁 项目结构

```
├── CLAUDE.md                    # 详细文档（必读）
├── README.md                    # 本文件
├── data/
│   ├── email_template.txt       # 邮件模板
│   └── sent_emails_blacklist.txt # 黑名单
├── scripts/
│   ├── collect_candidates.py    # 收集候选人
│   ├── generate_observations.py # 生成个性化观察
│   ├── send_emails.py           # 发送邮件
│   ├── pre_send_hook.py         # 发送前检查
│   ├── post_send_hook.py        # 发送后更新黑名单
│   ├── logger.py                # 日志工具
│   ├── daily_task.py            # 每日任务（150封）
│   └── daily_task_test.py       # 测试任务（3封）
└── logs/                        # 日志文件（自动生成）
```

## 📧 环境配置

需要在`.env`文件中配置：
- `GITHUB_TOKEN` - GitHub API访问
- `MINIMAX_API_KEY` - 生成个性化观察
- Gmail/QQ/163 邮箱账户信息

## ⚠️ 重要提醒

- Gmail发送前必须启动梯子
- 每批发送后自动更新黑名单
- Pre-send Hook自动检查，无需手动调用
- 日志自动保留7天

---

**详细文档请查看 CLAUDE.md**
