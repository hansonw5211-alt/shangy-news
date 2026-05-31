#!/bin/bash
# GitHub Actions 日报自动化 - 快速设置脚本

set -e

echo "=========================================="
echo "🚀 GitHub Actions 日报自动化设置"
echo "=========================================="
echo ""

# 检查是否已经是 git 仓库
if [ ! -d ".git" ]; then
    echo "📁 初始化 Git 仓库..."
    git init
    echo "✅ Git 仓库已初始化"
else
    echo "✅ Git 仓库已存在"
fi

# 创建 .gitignore
if [ ! -f ".gitignore" ]; then
    echo "📝 创建 .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
.env

# 日报输出（可选，如果不想上传历史日报）
# daily-briefing/briefing-*.md
# daily-briefing/html/briefing-*.html

# macOS
.DS_Store
.AppleDouble
.LSOverride

# IDE
.vscode/
.idea/
*.swp
*.swo
EOF
    echo "✅ .gitignore 已创建"
fi

# 添加所有文件
echo ""
echo "📦 添加文件到 Git..."
git add .

# 显示状态
echo ""
echo "📋 当前状态："
git status

echo ""
echo "=========================================="
echo "✅ 仓库已准备好！"
echo "=========================================="
echo ""
echo "下一步："
echo ""
echo "1. 在 GitHub 创建私有仓库："
echo "   https://github.com/new"
echo "   仓库名: daily-briefing-automation"
echo "   选择: Private"
echo ""
echo "2. 关联远程仓库（替换 YOUR_USERNAME）："
echo "   git remote add origin https://github.com/YOUR_USERNAME/daily-briefing-automation.git"
echo ""
echo "3. 提交并推送："
echo "   git commit -m '初始化每日综合资讯日报自动化'"
echo "   git push -u origin main"
echo ""
echo "4. 配置 GitHub Secrets："
echo "   打开仓库 → Settings → Secrets and variables → Actions"
echo "   添加以下 Secret："
echo "   - TAVILY_API_KEY"
echo "   - OPENAI_API_KEY"
echo "   - EMAIL_PASSWORD"
echo "   - SENDER_EMAIL"
echo "   - RECIPIENT_EMAIL"
echo ""
echo "5. 测试运行："
echo "   打开仓库 → Actions → Daily Briefing → Run workflow"
echo ""
echo "详细说明请查看: GITHUB_ACTIONS_SETUP.md"
echo ""
