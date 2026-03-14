# CLAUDE.md

这是一个自动化招聘工具，用于从GitHub收集高质量开发者候选人，生成个性化观察，并通过多个邮箱账户发送邮件。

## 🚨 最高原则（必须严格遵守）

### 1. 绝对不可重复触达同一候选人
- 每批发送前必须检查黑名单
- 每批发送后立即更新黑名单
- Pre-send Hook会自动强制检查

### 2. 日常任务分配原则
- **标准任务**: 每天3个邮箱各发50封（Gmail 50 + QQ 50 + 163 50 = 150封）
- **严格执行**: 每个邮箱只发送分配给它的50封
- **禁止补发**: 如果某个邮箱发送失败，不要自动用其他邮箱补发
- **例外情况**: 只有用户明确要求时，才可以用其他邮箱重发失败的邮件

## 📋 标准工作流程

### 每日任务（自动化）

```bash
# 一键完成150封邮件（Gmail 50 + QQ 50 + 163 50）
python3 scripts/daily_task.py
```

### 测试任务

```bash
# 测试模式：每个邮箱发1封（共3封）
python3 scripts/daily_task_test.py
```

### 手动执行（如需单独操作）

```bash
# 收集候选人
python3 scripts/collect_candidates.py --count 100 --output data/batch.xlsx

# 生成observations
python3 scripts/generate_observations.py data/batch.xlsx

# 发送邮件（自动触发pre-send hook检查）
python3 scripts/send_emails.py --xlsx data/batch.xlsx --template data/email_template.txt --account gmail --yes

# 注意：post-send hook会自动执行，无需手动调用
```

## 🛡️ 三重防重复保护机制

### 1. 收集阶段自动过滤
- `collect_candidates.py` 自动去除内部重复
- 自动过滤黑名单邮箱
- 只输出全新候选人

### 2. 自动Hook检查（最重要）⭐
- `pre_send_hook.py` 在每次发送前自动执行
- 三重检查：内部重复、黑名单、observation
- 检查失败立即阻止发送
- **无需手动调用，send_emails.py会自动触发**

### 3. 发送中实时验证
- `send_emails.py` 内置黑名单检查
- 发送每封邮件前再次验证

## 📁 项目结构

```
项目根目录/
├── CLAUDE.md                           # 本文件 - Claude指令
├── README.md                           # 项目说明
├── requirements.txt                    # Python依赖
├── data/
│   ├── email_template.txt              # 邮件模板（必须包含{{observation}}）
│   └── sent_emails_blacklist.txt       # 黑名单（TXT格式）
├── scripts/
│   ├── collect_candidates.py           # 收集候选人（自动去重+过滤黑名单）
│   ├── generate_observations.py        # 生成个性化观察
│   ├── send_emails.py                  # 发送邮件（自动触发hook）
│   ├── pre_send_hook.py                # Pre-send Hook（自动执行）
│   ├── post_send_hook.py               # Post-send Hook（自动执行）
│   ├── logger.py                       # 日志工具
│   ├── daily_task.py                   # 每日任务（150封）
│   └── daily_task_test.py              # 测试任务（3封）
└── logs/                               # 发送日志（自动生成，保留7天）
```

## 🔧 核心脚本说明

### collect_candidates.py
- 从GitHub搜索中国主要城市的开发者
- 筛选条件：50-700 followers，6+ repos
- 自动去重 + 自动过滤黑名单
- 输出：Excel文件（name, username, email, bio, location, repos, followers, profile_url, created_at）

### generate_observations.py
- 调用MiniMax API分析候选人的GitHub项目
- 为每个候选人生成独特的observation
- 更新Excel文件，添加observation列

### send_emails.py
- 支持三个邮箱账户：Gmail/QQ/163
- Gmail需要SOCKS5代理（127.0.0.1:10034）
- **自动触发pre_send_hook.py进行检查**
- 发送前再次检查黑名单
- 记录详细日志到logs/

### pre_send_hook.py（自动执行）
- 在send_emails.py执行时自动触发
- 检查内部重复、黑名单、observation
- 检查失败立即阻止发送
- 无需手动调用

### post_send_hook.py（自动执行）
- 在send_emails.py成功后自动触发
- 更新黑名单（sent_emails_blacklist.txt）
- 删除中间batch文件
- 发送失败时不执行

### logger.py
- 极简日志工具（30行代码）
- 自动记录到logs/YYYY-MM-DD.log
- 自动删除7天前的旧日志
- 记录所有关键操作和错误

## 📧 邮箱账户配置

### Gmail
- 需要SOCKS5代理：127.0.0.1:10034
- 使用应用密码
- 环境变量：GMAIL_ADDRESS, GMAIL_APP_PASSWORD

### QQ邮箱
- 直接SMTP连接
- 使用授权码
- 环境变量：QQ_EMAIL, QQ_PASSWORD
- 注意：可能不稳定，容易触发反垃圾机制

### 163邮箱
- 直接SMTP连接
- 使用授权码
- 环境变量：EMAIL_163, PASSWORD_163
- 最稳定，推荐使用

## ⚠️ 重要注意事项

1. **Gmail发送前必须启动梯子**，确保SOCKS5代理运行在127.0.0.1:10034
2. **每批发送后必须立即更新黑名单**，这是防止重复的关键
3. **Pre-send Hook会自动执行**，无需手动调用
4. 邮件模板必须包含`{{observation}}`占位符
5. **不要自动补发**：如果某个邮箱失败，不要自动用其他邮箱补发，除非用户明确要求

## 🎯 每日目标

- 每天发送150封邮件（3个邮箱 × 50封）
- 零重复触达
- 每封邮件都有个性化observation
- 完整的日志记录（自动保留7天）
- 自动更新黑名单

## 🚫 禁止操作

1. 不要跳过pre-send hook检查
2. 不要手动修改黑名单文件
3. 不要创建不必要的文档文件
4. 不要自动用其他邮箱补发失败的邮件（除非用户要求）

## 📊 日志系统

- 日志文件：`logs/YYYY-MM-DD.log`
- 自动记录所有关键操作
- 自动记录错误信息
- 自动保留最近7天
- 测试模式标记为 `[测试]`

## 📝 环境变量（.env）

```bash
GITHUB_TOKEN=xxx                # GitHub API访问
MINIMAX_API_KEY=xxx            # 生成个性化观察
GMAIL_ADDRESS=xxx@gmail.com    # Gmail账户
GMAIL_APP_PASSWORD=xxx         # Gmail应用密码
QQ_EMAIL=xxx@qq.com           # QQ邮箱
QQ_PASSWORD=xxx               # QQ授权码
EMAIL_163=xxx@163.com         # 163邮箱
PASSWORD_163=xxx              # 163授权码
```
