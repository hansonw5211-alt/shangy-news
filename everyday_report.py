#!/usr/bin/env python3
"""
日报生成脚本
- 将Markdown日报转为移动端优化的精美HTML
- 保存到坚果云同步文件夹（手机端坚果云App查看）
- 同时保留工作区备份
"""

import os
import sys
import re
import subprocess
from datetime import datetime


# ==================== 品牌配色 ====================
BRAND_DARK = "#0A4F5C"
BRAND_GOLD = "#C9A962"
BG_CARD = "#FFFFFF"
TEXT_BODY = "#2D3436"
TEXT_META = "#7F8C8D"
TEXT_TITLE = "#1A1A2E"

# 坚果云同步文件夹
NUTSTORE_DIR = "/Users/wangheng/Nutstore Files/我的坚果云/每日资讯"


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def markdown_to_html(md_text):
    """将日报Markdown转为移动端优化的精美HTML"""
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
                'border-radius:6px;font-size:12px;color:{meta};line-height:1.7;'
                'text-align:center;">{text}</div>'.format(meta=TEXT_META, text=desc))
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
                '<h3 style="font-size:13px;font-weight:600;color:{title};'
                'margin:16px 0 6px;line-height:1.5;">{num}. {text}</h3>'
                .format(title=TEXT_TITLE, num=num, text=title))
            i += 1
            continue

        m = re.match(r'^\*\*(.+?)\*\*[：:](.+)$', line)
        if m:
            label = escape_html(m.group(1))
            value = escape_html(m.group(2).strip())

            if label in ("摘要",):
                parts.append(
                    '<p style="margin:2px 0;line-height:1.8;font-size:11px;'
                    'color:{body};">{value}</p>'.format(body=TEXT_BODY, value=value))
            elif label in ("来源", "时间"):
                parts.append(
                    '<p style="margin:1px 0;line-height:1.6;font-size:10px;'
                    'color:{meta};">{label}：{value}</p>'
                    .format(meta=TEXT_META, label=label, value=value))
            elif label == "重要性":
                parts.append(
                    '<p style="margin:4px 0 8px;line-height:1.7;font-size:10px;'
                    'color:{body};">'
                    '<span style="color:{gold};font-weight:600;">💡 {label}：</span>'
                    '{value}</p>'
                    .format(body=TEXT_BODY, gold=BRAND_GOLD, label=label, value=value))
            else:
                parts.append(
                    '<p style="margin:2px 0;line-height:1.7;font-size:11px;'
                    'color:{body};">{label}：{value}</p>'
                    .format(body=TEXT_BODY, label=label, value=value))
            i += 1
            continue

        if line.startswith("*本日报"):
            parts.append(
                '<div style="margin-top:24px;padding-top:12px;'
                'border-top:1px solid #E8ECF0;text-align:center;'
                'color:{meta};font-size:10px;line-height:1.6;">'
                '{text}</div>'.format(meta=TEXT_META, text=line.strip("*")))
            i += 1
            continue

        safe = escape_html(line)
        parts.append(
            '<p style="margin:3px 0;line-height:1.7;font-size:11px;'
            'color:{body};">{text}</p>'.format(body=TEXT_BODY, text=safe))
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


def main():
    if len(sys.argv) < 2:
        print("用法: python send_wechat.py <md文件路径> [任务名称]")
        sys.exit(1)

    md_file = sys.argv[1]
    task_name = sys.argv[2] if len(sys.argv) > 2 else "每日综合资讯日报"

    if not os.path.exists(md_file):
        print(f"错误: 文件不存在 - {md_file}")
        sys.exit(1)

    try:
        with open(md_file, "r", encoding="utf-8") as f:
            md_content = f.read()

        m = re.search(r'^# (.+)$', md_content, re.MULTILINE)
        title = m.group(1).strip() if m else task_name
        date_str = datetime.now().strftime("%Y%m%d")

        # 1. 生成HTML
        html = markdown_to_html(md_content)
        print(f"✅ HTML已生成")

        # 2. 保存到工作区（备份）
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_dir = os.path.join(script_dir, "daily-briefing", "html")
        os.makedirs(workspace_dir, exist_ok=True)
        workspace_path = os.path.join(workspace_dir, f"briefing-{date_str}.html")
        with open(workspace_path, "w", encoding="utf-8") as f:
            f.write(html)

        # 3. 复制到坚果云
        os.makedirs(NUTSTORE_DIR, exist_ok=True)
        nutstore_path = os.path.join(NUTSTORE_DIR, f"briefing-{date_str}.html")
        cp_result = subprocess.run(
            ["cp", workspace_path, nutstore_path],
            capture_output=True, text=True
        )
        if cp_result.returncode == 0:
            print(f"📂 坚果云: {nutstore_path}")
        else:
            print(f"⚠️ 坚果云复制失败，请检查权限")
            sys.exit(1)

        print(f"✅ {title} — 请在坚果云App打开查看")

    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
