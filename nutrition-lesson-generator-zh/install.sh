#!/bin/bash
# 中文营养课程生成器 - 安装脚本
echo "正在安装 中文营养课程生成器..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "错误：需要 Python 3.11+"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "错误：requirements.txt 缺失"
    exit 1
fi

pip install -r requirements.txt

echo ""
echo "验证安装..."
python3 -c "from src.schemas.lesson import 生成请求; print('✅ Pydantic 模型正常')"
python3 -c "from src.providers.mock_provider import ChineseMockProvider; print('✅ MockProvider 正常')"
python3 -c "from src.exporters.ppt import 中文PPT导出器; print('✅ PPT导出器正常')"

echo ""
echo "🎉 安装完成！"
echo "使用方法："
echo "  python -m src.main generate --topic \"主题\" --audience \"目标听众\" --duration 30"
