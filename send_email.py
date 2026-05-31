#!/usr/bin/env python3
"""
行业资讯简报邮件发送脚本
支持Markdown转HTML邮件正文，支持失败通知
"""

import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import re

def markdown_to_html(markdown_text):
    """简单的Markdown转HTML"""
    html = markdown_text
    
    # 转义HTML特殊字符
    html = html.replace('&', '&amp;')
    html = html.replace('<', '&lt;')
    html = html.replace('>', '&gt;')
    
    # 标题转换（按层级从大到小，避免重复匹配）
    html = re.sub(r'^#### (.+)$', r'<h4 style="color:#0A4F5C;margin-top:15px;margin-bottom:8px;font-size:14px;font-weight:bold;">\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3 style="color:#0A4F5C;margin-top:20px;margin-bottom:10px;font-size:16px;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2 style="color:#0A4F5C;margin-top:25px;margin-bottom:12px;font-size:18px;border-bottom:2px solid #C9A962;padding-bottom:5px;">\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1 style="color:#0A4F5C;margin-top:0;margin-bottom:15px;font-size:22px;text-align:center;">\1</h1>', html, flags=re.MULTILINE)
    
    # 粗体
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#0A4F5C;">\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # 引用块
    html = re.sub(r'^&gt; (.+)$', r'<blockquote style="border-left:3px solid #C9A962;margin:10px 0;padding-left:10px;color:#666;font-style:italic;">\1</blockquote>', html, flags=re.MULTILINE)
    
    # 列表
    html = re.sub(r'^\d+\. \*\*(.+?)\*\*', r'<li style="margin:8px 0;"><strong style="color:#0A4F5C;">\1</strong>', html, flags=re.MULTILINE)
    html = re.sub(r'^\d+\. (.+)$', r'<li style="margin:5px 0;">\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'^- (.+)$', r'<li style="margin:5px 0;">\1</li>', html, flags=re.MULTILINE)
    
    # 分隔线
    html = re.sub(r'^---+$', r'<hr style="border:none;border-top:1px solid #ddd;margin:20px 0;">', html, flags=re.MULTILINE)
    
    # 段落
    paragraphs = html.split('\n\n')
    new_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<') and not p.startswith('<li'):
            p = f'<p style="margin:10px 0;line-height:1.6;">{p}</p>'
        new_paragraphs.append(p)
    html = '\n'.join(new_paragraphs)
    
    # 包裹列表
    html = re.sub(r'(<li[^>]*>.+?</li>\n?)+', lambda m: f'<ul style="margin:10px 0;padding-left:20px;">{m.group(0)}</ul>', html, flags=re.DOTALL)
    
    return html

def send_email(subject, markdown_content, to_email="hansonw5211@163.com"):
    """发送邮件"""
    # 邮件配置 - 使用163邮箱作为发送方
    smtp_server = "smtp.163.com"
    smtp_port = 465
    sender_email = "hansonw5211@163.com"  # 使用同一邮箱发送和接收
    
    # 从环境变量获取授权码
    sender_password = os.environ.get("EMAIL_PASSWORD", "")
    
    if not sender_password:
        print("错误：未设置邮箱授权码，请设置环境变量 EMAIL_PASSWORD")
        return False
    
    # 转换Markdown为HTML
    html_content = markdown_to_html(markdown_content)
    
    # 构建完整HTML邮件
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;line-height:1.6;color:#333;max-width:800px;margin:0 auto;padding:20px;background:#f5f5f5;">
    <div style="background:#fff;padding:30px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <div style="text-align:center;padding:20px 0;border-bottom:3px solid #0A4F5C;margin-bottom:20px;">
            <h1 style="color:#0A4F5C;margin:0;font-size:24px;">🔭 行业资讯简报</h1>
            <p style="color:#C9A962;margin:10px 0 0 0;font-size:14px;">{datetime.now().strftime('%Y年%m月%d日')}</p>
        </div>
        {html_content}
        <div style="margin-top:30px;padding-top:20px;border-top:1px solid #ddd;text-align:center;color:#999;font-size:12px;">
            <p>本简报由 WorkBuddy 自动生成</p>
            <p>发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
    
    # 创建邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"行业资讯简报 <{sender_email}>"
    msg['To'] = to_email
    
    # 添加纯文本版本
    msg.attach(MIMEText(markdown_content, 'plain', 'utf-8'))
    # 添加HTML版本
    msg.attach(MIMEText(full_html, 'html', 'utf-8'))
    
    try:
        # 发送邮件
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"✅ 邮件发送成功: {subject}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

def send_failure_notification(task_name, error_message, to_email="hansonw5211@163.com"):
    """发送任务失败通知"""
    smtp_server = "smtp.163.com"
    smtp_port = 465
    sender_email = "hansonw5211@163.com"
    sender_password = os.environ.get("EMAIL_PASSWORD", "")
    
    if not sender_password:
        return False
    
    subject = f"⚠️ 行业资讯简报任务失败 - {task_name}"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>任务失败通知</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;line-height:1.6;color:#333;max-width:600px;margin:0 auto;padding:20px;background:#f5f5f5;">
    <div style="background:#fff;padding:30px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);border-left:4px solid #e74c3c;">
        <h2 style="color:#e74c3c;margin-top:0;">⚠️ 自动化任务执行失败</h2>
        
        <div style="background:#f8f9fa;padding:15px;border-radius:5px;margin:15px 0;">
            <p style="margin:5px 0;"><strong>任务名称：</strong>{task_name}</p>
            <p style="margin:5px 0;"><strong>失败时间：</strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin:5px 0;"><strong>错误信息：</strong></p>
            <pre style="background:#f4f4f4;padding:10px;border-radius:3px;overflow-x:auto;">{error_message}</pre>
        </div>
        
        <p style="color:#666;">请检查系统状态或手动执行该任务。</p>
        
        <div style="margin-top:20px;padding-top:15px;border-top:1px solid #ddd;text-align:center;color:#999;font-size:12px;">
            <p>本通知由 WorkBuddy 自动发送</p>
        </div>
    </div>
</body>
</html>"""
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"WorkBuddy通知 <{sender_email}>"
    msg['To'] = to_email
    msg.attach(MIMEText(f"任务失败: {task_name}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n错误: {error_message}", 'plain', 'utf-8'))
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"✅ 失败通知已发送")
        return True
    except Exception as e:
        print(f"❌ 失败通知发送失败: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("用法: python send_email.py <markdown文件路径> [任务名称]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    task_name = sys.argv[2] if len(sys.argv) > 2 else "行业资讯简报"
    
    if not os.path.exists(md_file):
        error_msg = f"文件不存在: {md_file}"
        print(f"错误: {error_msg}")
        send_failure_notification(task_name, error_msg)
        sys.exit(1)
    
    try:
        # 读取Markdown内容
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取标题作为邮件主题
        subject_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if subject_match:
            subject = f"【行业资讯】{subject_match.group(1).replace(' - ', ' ')}"
        else:
            subject = f"【行业资讯简报】{datetime.now().strftime('%Y年%m月%d日')}"
        
        # 发送邮件
        success = send_email(subject, content)
        if not success:
            send_failure_notification(task_name, "邮件发送失败，请检查邮箱配置")
            sys.exit(1)
            
    except Exception as e:
        error_msg = str(e)
        print(f"错误: {error_msg}")
        send_failure_notification(task_name, error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
