# GitHub Actions 云端日报自动化 - 配置指南

## 📋 概述

本方案将每日综合资讯日报自动化迁移到 GitHub Actions 云端运行，**无需本地电脑开机**，每天北京时间 09:00 自动执行并发送邮件。

**优势**：
- ✅ 完全免费（GitHub Actions 每月 2000 分钟免费额度）
- ✅ 不依赖本地电脑，云端稳定运行
- ✅ 自动发送精美 HTML 日报邮件
- ✅ 支持手动触发（调试用）
- ✅ 支持多个 AI API 提供商（国内可用）

---

## 🔧 配置步骤

### 步骤 1：创建 GitHub 私有仓库

1. 访问 https://github.com/new
2. Repository name: `daily-briefing-automation`
3. 选择 **Private**（私有仓库，保护你的代码和配置）
4. 点击 Create repository

### 步骤 2：上传代码到 GitHub

在本地项目目录执行：

```bash
# 初始化 Git 仓库（如果还没有）
cd /Users/wangheng/WorkBuddy/2026-04-早报自动化系统
git init

# 添加所有文件
git add .

# 提交
git commit -m "初始化每日综合资讯日报自动化"

# 关联远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/daily-briefing-automation.git

# 推送
git push -u origin main
```

### 步骤 3：获取 API 密钥

#### 3.1 Tavily API（新闻搜索）

1. 访问 https://tavily.com
2. 注册账号（可用 Google 登录）
3. 进入 Dashboard → API Keys
4. 复制 API Key（格式：`tvly-xxxxxxxxxx`）

**免费额度**：每月 1000 次搜索，足够每日运行（每天约 20 次搜索）

#### 3.2 AI API（内容生成）- 选择一个

**推荐：DeepSeek API（国内首选）**

1. 访问 https://platform.deepseek.com
2. 注册账号（手机号注册）
3. 进入 API Keys 页面
4. 创建 API Key
5. 复制 API Key（格式：`sk-xxxxxxxxxx`）

**免费额度**：注册送 ¥5，约可用 3-4 个月

**其他选择**：

| 服务 | 注册地址 | 免费额度 | 价格 |
|------|---------|---------|------|
| **智谱 GLM** | https://open.bigmodel.cn | 注册送 ¥5，有免费模型 | ¥0.1/百万token |
| **通义千问** | https://dashscope.console.aliyun.com | 100万token/月 | ¥0.3/百万token |
| **Moonshot** | https://platform.moonshot.cn | 注册送 ¥15 | ¥1/百万token |
| **OpenAI** | https://platform.openai.com | 无 | $0.15/百万token |

#### 3.3 163 邮箱授权码

1. 登录 163 邮箱：https://mail.163.com
2. 进入 设置 → POP3/SMTP/IMAP
3. 开启 SMTP 服务
4. 按提示发送短信验证
5. 获取授权码（不是邮箱密码！）

### 步骤 4：配置 GitHub Secrets

1. 打开你的 GitHub 仓库页面
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**，依次添加以下 Secret：

**必填（3个）**：

| Secret 名称 | 值 | 说明 |
|-------------|---|------|
| `TAVILY_API_KEY` | `tvly-xxxxxxxxxx` | Tavily 搜索 API 密钥 |
| `EMAIL_PASSWORD` | `xxxxxxxxxx` | 163 邮箱授权码 |
| `RECIPIENT_EMAIL` | `hansonw5211@163.com` | 接收邮箱地址 |

**AI API（选择一个提供商）**：

**方案 A：DeepSeek（推荐）**
| Secret 名称 | 值 |
|-------------|---|
| `AI_PROVIDER` | `deepseek` |
| `DEEPSEEK_API_KEY` | `sk-xxxxxxxxxx` |

**方案 B：智谱 GLM**
| Secret 名称 | 值 |
|-------------|---|
| `AI_PROVIDER` | `zhipu` |
| `ZHIPU_API_KEY` | `xxxxxxxxxx` |

**方案 C：通义千问**
| Secret 名称 | 值 |
|-------------|---|
| `AI_PROVIDER` | `qwen` |
| `QWEN_API_KEY` | `sk-xxxxxxxxxx` |

**方案 D：Moonshot (Kimi)**
| Secret 名称 | 值 |
|-------------|---|
| `AI_PROVIDER` | `moonshot` |
| `MOONSHOT_API_KEY` | `sk-xxxxxxxxxx` |

**方案 E：OpenAI**
| Secret 名称 | 值 |
|-------------|---|
| `AI_PROVIDER` | `openai` |
| `OPENAI_API_KEY` | `sk-xxxxxxxxxx` |

**可选（1个）**：

| Secret 名称 | 值 | 说明 |
|-------------|---|------|
| `SENDER_EMAIL` | `hansonw5211@163.com` | 发送邮箱（默认与接收相同）|

### 步骤 5：手动触发测试

1. 打开仓库页面 → **Actions** 标签
2. 左侧选择 **Daily Briefing**
3. 点击 **Run workflow** → **Run workflow**
4. 等待约 2-3 分钟完成
5. 检查邮箱是否收到日报

---

## 📊 执行流程

```
每天 UTC 01:00（北京时间 09:00）
    ↓
GitHub Actions 启动云端服务器
    ↓
安装 Python 3.11 + 依赖包
    ↓
运行 daily_briefing_cloud.py
    ↓
┌─────────────────────────────────────┐
│ 1. Tavily 搜索五大板块新闻（20次搜索）│
│ 2. AI 生成精选内容（5板块×5条）      │
│ 3. 生成 Markdown 日报               │
│ 4. 转换为精美 HTML                   │
│ 5. 发送邮件                          │
└─────────────────────────────────────┘
    ↓
邮件送达，手机/电脑直接查看
```

---

## 🔍 查看执行日志

1. 打开仓库 → **Actions** 标签
2. 点击最近一次 workflow run
3. 点击 **generate-briefing** job
4. 展开 **Generate and send daily briefing** 查看详细日志

---

## ⚙️ 高级配置

### 修改执行时间

编辑 `.github/workflows/daily-briefing.yml`：

```yaml
schedule:
  # 修改 cron 表达式（UTC 时间）
  - cron: '0 1 * * *'  # 北京时间 09:00
  # - cron: '0 2 * * *'  # 北京时间 10:00
  # - cron: '30 0 * * *' # 北京时间 08:30
```

### 修改邮件内容

编辑 `scripts/daily_briefing_cloud.py` 中的：
- `SECTIONS` 列表：修改搜索关键词
- `generate_section_content()` 函数：调整 AI 生成的 prompt
- `markdown_to_html()` 函数：修改 HTML 样式

### 添加微信通知（可选）

在 `daily_briefing_cloud.py` 末尾添加 Server 酱推送：

```python
import requests

def send_wechat_notification(content):
    """发送微信通知"""
    server_key = os.environ.get("SERVER_CHAN_KEY")
    if server_key:
        url = f"https://sctapi.ftqq.com/{server_key}.send"
        data = {"title": "📰 每日资讯日报", "desp": content[:100]}
        requests.post(url, data=data)
```

然后在 GitHub Secrets 中添加 `SERVER_CHAN_KEY`。

---

## 💰 成本估算

| 服务 | 免费额度 | 超出费用 | 每月预估 |
|------|---------|---------|---------|
| GitHub Actions | 2000 分钟/月 | $0.008/分钟 | 免费（约 150 分钟） |
| Tavily API | 1000 次/月 | $0.01/次 | 免费（约 600 次） |
| DeepSeek API | 注册送 ¥5 | ¥1/百万token | ~¥0.1 |
| 163 邮箱 | 免费 | - | 免费 |
| **总计** | | | **~¥0.1/月** |

---

## 🔧 故障排查

### 问题 1：Workflow 未触发

**原因**：GitHub 对非活跃仓库会暂停 scheduled workflows

**解决**：
- 每隔 60 天手动触发一次
- 或者推一次 commit 重新激活

### 问题 2：Tavily 搜索失败

**原因**：API Key 无效或额度用完

**解决**：
1. 登录 https://tavily.com 检查额度
2. 确认 GitHub Secrets 中的 `TAVILY_API_KEY` 正确

### 问题 3：AI 生成失败

**原因**：API Key 无效或余额不足

**解决**：
1. 检查对应的 API Key 是否正确
2. 登录对应平台检查余额
3. 确认 `AI_PROVIDER` 设置正确

### 问题 4：邮件发送失败

**原因**：163 邮箱授权码错误或 SMTP 未开启

**解决**：
1. 登录 163 邮箱 → 设置 → POP3/SMTP/IMAP
2. 确认 SMTP 已开启
3. 重新获取授权码
4. 更新 GitHub Secrets 中的 `EMAIL_PASSWORD`

---

## 📱 查看日报

每天 09:00 后，打开邮箱即可查看精美 HTML 日报。

**手机查看**：
- 邮件 App（推荐）
- 浏览器登录邮箱

**电脑查看**：
- 邮件客户端
- 浏览器登录邮箱

---

## 🎯 下一步

配置完成后，你可以：
1. ✅ 每天自动收到日报邮件
2. ✅ 在 GitHub Actions 查看执行日志
3. ✅ 随时手动触发测试
4. ✅ 根据需要调整内容和样式

如有问题，随时联系我！
