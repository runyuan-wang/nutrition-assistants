#!/usr/bin/env bash
# 营养风险筛查计算器 安装脚本
set -e

echo "📦 安装营养风险筛查计算器依赖..."
if command -v pip3 >/dev/null 2>&1; then
  pip3 install -r "$(dirname "$0")/requirements.txt"
else
  pip install -r "$(dirname "$0")/requirements.txt"
fi

echo "✅ 安装完成。试试："
echo "   python -m src.cli nrs2002 --bmi 17.2 --weight-loss-pct 8 --weight-loss-months 2 --intake-pct 60 --disease-severity 2 --age 72"
