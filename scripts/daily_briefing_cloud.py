#!/usr/bin/env python3
"""
每日综合资讯日报 - 云端版本
在 GitHub Actions 中运行，自动生成并发送日报邮件
支持多个 AI API 提供商（DeepSeek/智谱/通义千问/OpenAI）
"""

import os
import sys
import json
import re
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# 第三方库
from tavily import TavilyClient
from openai import OpenAI  # 兼容所有 OpenAI 格式的 API

# ==================== 配置 ====================

# 五大板块配置（3中文 + 1英文 = 国内消息为主）
SECTIONS = [
    {
        "name": "🤖 AI新闻",
        "keywords": ["AI大模型", "人工智能", "OpenAI", "Google AI", "Anthropic", "AI产品发布", "AI技术突破"],
        "search_queries": [
            "人工智能 大模型 最新进展 国内AI产业",
            "DeepSeek 百度 阿里 字节 AI发布 国产大模型",
            "OpenAI Google Anthropic AI最新消息 中国相关",
            "AI technology China news domestic"
        ]
    },
    {
        "name": "🏥 医疗健康",
        "keywords": ["医疗政策", "医药新药", "生物技术", "医疗器械", "基因治疗", "临床试验"],
        "search_queries": [
            "中国医疗政策 医保 药品审批 卫健委最新",
            "国产新药 临床试验 生物医药 医疗器械突破",
            "国内医疗健康 创新药 基因治疗 最新消息",
            "China healthcare biotech FDA approval domestic"
        ]
    },
    {
        "name": "🔬 科学技术",
        "keywords": ["科学突破", "量子计算", "航空航天", "新能源", "材料科学"],
        "search_queries": [
            "中国科学突破 量子计算 航天 新能源技术",
            "国内科研进展 中科院 高校 技术创新最新",
            "中国航天 量子 深海 新材料 重大成果",
            "China science quantum space energy breakthrough"
        ]
    },
    {
        "name": "💰 金融投资",
        "keywords": ["A股行情", "美股", "港股", "基金", "ETF", "宏观经济"],
        "search_queries": [
            "A股行情 沪指 深指 市场动态 最新分析",
            "中国经济政策 央行 人民币 宏观经济最新",
            "A股 港股 美股 基金 ETF 市场新闻",
            "China stock market economy finance latest"
        ]
    },
    {
        "name": "⚖️ 法律法规",
        "keywords": ["新法规", "司法解释", "合规政策", "监管新规"],
        "search_queries": [
            "中国新法规 监管政策 国务院 部委发布最新",
            "司法解释 合规新规 数据安全 知识产权 最新",
            "国内法律 行业监管 政策法规 最新动态",
            "China regulation law policy compliance new"
        ]
    }
]

# AI API 提供商配置
AI_PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",  # DeepSeek-V3
        "env_key": "DEEPSEEK_API_KEY",
        "description": "国内首选，价格最低（¥1/百万token），注册送¥5"
    },
    "zhipu": {
        "name": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",  # 免费模型
        "env_key": "ZHIPU_API_KEY",
        "description": "国内可用，有免费模型（glm-4-flash），注册送¥5"
    },
    "qwen": {
        "name": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo",
        "env_key": "QWEN_API_KEY",
        "description": "阿里云，有免费额度（100万token/月）"
    },
    "moonshot": {
        "name": "Moonshot (Kimi)",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
        "env_key": "MOONSHOT_API_KEY",
        "description": "Kimi，注册送¥15"
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "description": "需要海外账号，价格较高"
    }
}

# 品牌配色
BRAND_DARK = "#0A4F5C"
BRAND_GOLD = "#C9A962"


def get_env_or_exit(key, optional=False):
    """获取环境变量，不存在则退出"""
    value = os.environ.get(key)
    if not value and not optional:
        print(f"❌ 环境变量 {key} 未设置")
        sys.exit(1)
    return value


def get_ai_client():
    """根据环境变量选择 AI API 提供商"""
    
    # 从环境变量读取使用的提供商（默认 deepseek）
    provider_name = os.environ.get("AI_PROVIDER", "deepseek").lower()
    
    if provider_name not in AI_PROVIDERS:
        print(f"❌ 不支持的 AI 提供商: {provider_name}")
        print(f"   支持的提供商: {', '.join(AI_PROVIDERS.keys())}")
        sys.exit(1)
    
    provider = AI_PROVIDERS[provider_name]
    api_key = get_env_or_exit(provider["env_key"])
    
    print(f"🤖 使用 AI 提供商: {provider['name']}")
    print(f"   模型: {provider['model']}")
    print(f"   说明: {provider['description']}")
    
    # 创建客户端（兼容 OpenAI SDK）
    client = OpenAI(
        api_key=api_key,
        base_url=provider["base_url"]
    )
    
    return client, provider["model"]


def search_news(tavily_client, queries, max_results=8):
    """使用 Tavily 搜索新闻"""
    all_results = []
    
    for query in queries:
        try:
            response = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                topic="news",
                days=1  # 过去24小时
            )
            if response and "results" in response:
                all_results.extend(response["results"])
        except Exception as e:
            print(f"⚠️ 搜索失败 [{query[:30]}...]: {e}")
            continue
    
    # 去重
    seen_urls = set()
    unique_results = []
    for result in all_results:
        url = result.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(result)
    
    return unique_results


def generate_section_content(ai_client, model_name, section_name, search_results):
    """使用 AI 生成板块内容"""
    
    # 构建搜索结果摘要
    news_items = []
    for i, result in enumerate(search_results[:15], 1):  # 最多取15条
        title = result.get("title", "")
        content = result.get("content", "")[:300]  # 限制长度
        url = result.get("url", "")
        published = result.get("published_date", "")
        source = result.get("source", "")
        
        news_items.append(f"""
{i}. 标题: {title}
   来源: {source}
   时间: {published}
   内容: {content}
   链接: {url}
""")
    
    news_text = "\n".join(news_items)
    
    # 生成 prompt
    prompt = f"""你是一名专业的资讯编辑，负责从搜索结果中精选最重要的新闻。

**任务**：从以下搜索结果中，为「{section_name}」板块精选5条最重要的资讯。

**筛选标准**：
1. 优先选择国内/中国相关的新闻，兼顾重大国际事件
2. 来自主流媒体或权威机构（如新华社、财联社、第一财经、科技日报等）
3. 热度高（多方报道同一事件）或重要性高（影响面广）
4. 有实质内容，非标题党或广告
5. 优先选择过去24小时内的新闻
6. 5条中至少3条为国内新闻

**输出格式**（严格按此格式）：

### 1. [标题，25字内]
**摘要**：[50-80字，提炼核心要点，不废话]
**来源**：[媒体名称] | **时间**：[相对描述，如"2小时前"或具体日期]
**重要性**：[1-2句话，说明为何重要/影响是什么]

### 2. [标题]
...（共5条）

**搜索结果**：
{news_text}

请严格按照上述格式输出5条资讯，不要添加任何其他内容。"""

    try:
        response = ai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一名专业的资讯编辑，擅长从大量信息中提炼核心要点。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        return content
    
    except Exception as e:
        print(f"❌ AI 生成失败: {e}")
        return None


def generate_briefing_md(tavily_client, ai_client, model_name):
    """生成完整的日报 Markdown"""
    
    today = datetime.now()
    date_str = today.strftime("%Y年%m月%d日")
    date_file = today.strftime("%Y%m%d")
    
    sections_content = []
    
    for section in SECTIONS:
        print(f"🔍 搜索: {section['name']}...")
        search_results = search_news(tavily_client, section["search_queries"])
        
        if not search_results:
            print(f"⚠️ {section['name']} 无搜索结果，使用占位内容")
            sections_content.append(f"""
## {section['name']}

*本板块暂无24小时内重大新闻*

---
""")
            continue
        
        print(f"📝 生成: {section['name']}...")
        content = generate_section_content(ai_client, model_name, section["name"], search_results)
        
        if content:
            sections_content.append(f"""
## {section['name']}

{content}

---
""")
        else:
            sections_content.append(f"""
## {section['name']}

*内容生成失败，请检查日志*

---
""")
    
    # 组装完整 Markdown
    md_content = f"""# 📰 每日综合资讯日报 - {date_str}

> 📅 时效范围：过去24小时 | 🕘 推送时间：09:00 | 每板块精选5条

---

{''.join(sections_content)}

*本日报由 WorkBuddy 自动生成 · 数据来源：主流媒体及权威机构 · 每日09:00推送*
"""
    
    return md_content, date_file


def save_briefing(md_content, date_file):
    """保存日报到本地"""
    
    # 创建目录
    base_dir = Path(__file__).parent.parent
    md_dir = base_dir / "daily-briefing"
    html_dir = md_dir / "html"
    md_dir.mkdir(parents=True, exist_ok=True)
    html_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存 Markdown
    md_path = md_dir / f"briefing-{date_file}.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"📄 Markdown 已保存: {md_path}")
    
    # 转换为 HTML 并保存
    html_content = markdown_to_html(md_content)
    html_path = html_dir / f"briefing-{date_file}.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"🌐 HTML 已保存: {html_path}")
    
    return md_path, html_path


def markdown_to_html(md_text):
    """将日报 Markdown 转为移动端优化的精美 HTML"""
    
    def escape_html(text):
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    lines = md_text.split("\n")
    parts = []
    first_h1 = True
    
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        
        m = re.match(r'^# (.+)$', line)
        if m:
            title = escape_html(m.group(1))
            if first_h1:
                parts.append(
                    '<div style="text-align:center;padding:28px 0 8px;">'
                    '<h1 style="font-size:18px;font-weight:700;color:{dark};'
                    'margin:0;letter-spacing:0.5px;line-height:1.5;">{text}</h1>'
                    '</div>'.format(dark=BRAND_DARK, text=title))
                first_h1 = False
            i += 1
            continue
        
        m = re.match(r'^> (.+)$', line)
        if m:
            desc = escape_html(m.group(1))
            parts.append(
                '<div style="background:#EDF2F7;padding:10px 14px;margin:0 0 20px;'
                'border-radius:6px;font-size:12px;color:#7F8C8D;line-height:1.7;'
                'text-align:center;">{text}</div>'.format(text=desc))
            i += 1
            continue
        
        if re.match(r'^---+$', line.strip()):
            parts.append(
                '<div style="margin:20px 0;text-align:center;">'
                '<span style="display:inline-block;width:50px;height:2px;'
                'background:linear-gradient(90deg,transparent,{gold},transparent);"></span>'
                '</div>'.format(gold=BRAND_GOLD))
            i += 1
            continue
        
        m = re.match(r'^## (.+)$', line)
        if m:
            section = escape_html(m.group(1))
            parts.append(
                '<h2 style="font-size:15px;font-weight:700;color:{dark};'
                'margin:24px 0 10px;padding-bottom:6px;'
                'border-bottom:2px solid {gold};line-height:1.4;">{text}</h2>'
                .format(dark=BRAND_DARK, gold=BRAND_GOLD, text=section))
            i += 1
            continue
        
        m = re.match(r'^### (\d+)\. (.+)$', line)
        if m:
            num = m.group(1)
            title = escape_html(m.group(2))
            parts.append(
                '<h3 style="font-size:13px;font-weight:600;color:#1A1A2E;'
                'margin:16px 0 6px;line-height:1.5;">{num}. {text}</h3>'
                .format(num=num, text=title))
            i += 1
            continue
        
        m = re.match(r'^\*\*(.+?)\*\*[：:](.+)$', line)
        if m:
            label = escape_html(m.group(1))
            value = escape_html(m.group(2).strip())
            
            if label in ("摘要",):
                parts.append(
                    '<p style="margin:2px 0;line-height:1.8;font-size:11px;'
                    'color:#2D3436;">{value}</p>'.format(value=value))
            elif label in ("来源", "时间"):
                parts.append(
                    '<p style="margin:1px 0;line-height:1.6;font-size:10px;'
                    'color:#7F8C8D;">{label}：{value}</p>'
                    .format(label=label, value=value))
            elif label == "重要性":
                parts.append(
                    '<p style="margin:4px 0 8px;line-height:1.7;font-size:10px;'
                    'color:#2D3436;">'
                    '<span style="color:{gold};font-weight:600;">💡 {label}：</span>'
                    '{value}</p>'
                    .format(gold=BRAND_GOLD, label=label, value=value))
            else:
                parts.append(
                    '<p style="margin:2px 0;line-height:1.7;font-size:11px;'
                    'color:#2D3436;">{label}：{value}</p>'
                    .format(label=label, value=value))
            i += 1
            continue
        
        if line.startswith("*本日报"):
            parts.append(
                '<div style="margin-top:24px;padding-top:12px;'
                'border-top:1px solid #E8ECF0;text-align:center;'
                'color:#7F8C8D;font-size:10px;line-height:1.6;">'
                '{text}</div>'.format(text=line.strip("*")))
            i += 1
            continue
        
        safe = escape_html(line)
        parts.append(
            '<p style="margin:3px 0;line-height:1.7;font-size:11px;'
            'color:#2D3436;">{text}</p>'.format(text=safe))
        i += 1
    
    body = "\n".join(parts)
    
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>每日综合资讯日报</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", sans-serif;
    background: #F5F7FA;
    color: #2D3436;
    -webkit-font-smoothing: antialiased;
}}
.container {{
    max-width: 640px;
    margin: 0 auto;
    padding: 12px 10px 24px;
}}
.card {{
    background: #FFFFFF;
    border-radius: 10px;
    padding: 4px 18px 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}
</style>
</head>
<body>
<div class="container">
<div class="card">
{body}
</div>
</div>
</body>
</html>""".format(body=body)
    
    return html


def send_email(subject, html_content, recipient_email):
    """发送邮件（自动识别 QQ/163/126 邮箱）"""
    
    sender_email = get_env_or_exit("SENDER_EMAIL").strip()
    sender_password = get_env_or_exit("EMAIL_PASSWORD").strip()
    
    # 自动识别邮箱服务商
    if "qq.com" in sender_email:
        smtp_server = "smtp.qq.com"
    elif "163.com" in sender_email:
        smtp_server = "smtp.163.com"
    elif "126.com" in sender_email:
        smtp_server = "smtp.126.com"
    else:
        print(f"❌ 不支持的邮箱: {sender_email}")
        sys.exit(1)
    
    print(f"📧 发送邮件: {sender_email} → {recipient_email}")
    print(f"   邮件服务商: {smtp_server}")
    
    # 构建邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"每日资讯日报 <{sender_email}>"
    msg['To'] = recipient_email
    
    # 纯文本版本
    plain_text = re.sub(r'<[^>]+>', '', html_content)[:500] + "..."
    msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
    
    # HTML 版本
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    # 尝试发送
    errors = []
    
    for port, description in [(465, "SSL"), (587, "TLS")]:
        try:
            print(f"   尝试 {description} 端口 {port}...")
            if port == 465:
                server = smtplib.SMTP_SSL(smtp_server, port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_server, port, timeout=15)
                server.starttls()
            
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            print(f"✅ 邮件已发送至: {recipient_email} ({description} {port})")
            return
        except Exception as e:
            errors.append(f"{description} {port}: {e}")
            print(f"   {description} {port} 失败，尝试下一个...")
    
    print(f"❌ 邮件发送失败:")
    for err in errors:
        print(f"   {err}")
    raise Exception("邮件发送失败")


def check_today_already_run():
    """通过 GitHub API 检查今天是否已有成功运行（真正的去重）"""
    
    # GitHub Actions 环境变量
    github_token = os.environ.get("GITHUB_TOKEN", "")
    github_repo = os.environ.get("GITHUB_REPOSITORY", "")
    github_run_id = os.environ.get("GITHUB_RUN_ID", "")
    workflow_ref = os.environ.get("GITHUB_WORKFLOW_REF", "")
    
    # 非 GitHub Actions 环境（本地测试），不做 API 去重
    if not github_token or not github_repo:
        print("⚠️ 非 GitHub Actions 环境，跳过去重检查")
        return False
    
    # 提取 workflow 文件名
    # GITHUB_WORKFLOW_REF 格式: owner/repo/.github/workflows/daily-briefing.yml@refs/heads/main
    # 直接硬编码文件名是最可靠的方式
    workflow_file = "daily-briefing.yml"
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # 调用 GitHub API 获取今天本 workflow 的成功运行
        api_url = (
            f"https://api.github.com/repos/{github_repo}/actions/workflows/"
            f"{workflow_file}/runs"
            f"?status=success"
            f"&created={today}"
            f"&per_page=5"
        )
        
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        print(f"🔍 检查今天是否已运行过: {today}")
        print(f"   API: {api_url}")
        resp = requests.get(api_url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            print(f"⚠️ API 查询失败 (状态码 {resp.status_code})，继续执行")
            return False
        
        data = resp.json()
        runs = data.get("workflow_runs", [])
        print(f"   找到 {data.get('total_count', 0)} 条记录，检查 {len(runs)} 条")
        
        # 排除自身（当前 run）
        for run in runs:
            conclusion = run.get("conclusion", "")
            run_id = str(run.get("id", ""))
            if run_id != github_run_id and conclusion == "success":
                run_time = run.get("created_at", "unknown")
                print(f"✅ 今天已有成功运行 (Run #{run['id']}, {run_time})，跳过！")
                return True
        
        print(f"📝 今天尚未成功运行，开始执行...")
        return False
        
    except Exception as e:
        print(f"⚠️ 去重检查异常: {e}，继续执行（以防漏报）")
        return False


def main():
    """主函数"""
    
    print("🚀 开始生成每日综合资讯日报...")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # === 去重检查：今天是否已经成功运行过 ===
    if check_today_already_run():
        print(f"⏭️ 今天的日报已发送过，跳过重复执行。")
        return
    
    # 检查环境变量
    tavily_key = get_env_or_exit("TAVILY_API_KEY")
    
    # 初始化 Tavily 客户端
    tavily_client = TavilyClient(api_key=tavily_key)
    
    # 初始化 AI 客户端（支持多个提供商）
    ai_client, model_name = get_ai_client()
    
    # 生成日报
    md_content, date_file = generate_briefing_md(tavily_client, ai_client, model_name)
    
    # 保存文件
    md_path, html_path = save_briefing(md_content, date_file)
    
    # 读取 HTML 内容
    html_content = html_path.read_text(encoding="utf-8")
    
    # 发送邮件
    today = datetime.now()
    subject = f"📰 每日综合资讯日报 - {today.strftime('%Y年%m月%d日')}"
    recipient_email = get_env_or_exit("RECIPIENT_EMAIL")
    
    try:
        send_email(subject, html_content, recipient_email)
    except Exception as e:
        print(f"❌ 推送失败: {e}")
        sys.exit(1)
    
    print()
    print("✅ 每日综合资讯日报推送完成！")


if __name__ == "__main__":
    main()
