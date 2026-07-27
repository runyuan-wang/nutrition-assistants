#!/bin/bash
# 营养学 | 儿童青少年肥胖治未病食养助手 - 安装脚本
# 用法: bash install.sh

echo "正在安装 营养学 | 儿童青少年肥胖治未病食养助手..."
echo "来源：中华中医药学会《儿童青少年肥胖治未病干预指南》（2026年）"
echo ""

# 检查 SKILL.md 是否存在
if [ -f "SKILL.md" ]; then
    echo "✅ SKILL.md 已就绪"
else
    echo "❌ SKILL.md 缺失"
    exit 1
fi

# 检查 knowledge_base.md
if [ -f "knowledge_base.md" ]; then
    KPK_COUNT=$(grep -c '^## KPK-' knowledge_base.md)
    echo "✅ knowledge_base.md 已就绪（$KPK_COUNT 个KPK知识点）"
else
    echo "❌ knowledge_base.md 缺失"
    exit 1
fi

# 检查 dietary_formulas.md
if [ -f "dietary_formulas.md" ]; then
    FORMULA_COUNT=$(grep -c '^### [0-9]' dietary_formulas.md)
    echo "✅ dietary_formulas.md 已就绪（11道药膳方）"
else
    echo "❌ dietary_formulas.md 缺失"
    exit 1
fi

# 检查 system_prompt.md
if [ -f "system_prompt.md" ]; then
    echo "✅ system_prompt.md 已就绪"
else
    echo "❌ system_prompt.md 缺失"
    exit 1
fi

# 检查 skill.yaml
if [ -f "skill.yaml" ]; then
    echo "✅ skill.yaml 已就绪"
else
    echo "❌ skill.yaml 缺失"
    exit 1
fi

echo ""
echo "🎉 安装完成！本Skill包含："
echo "  - $(grep -c '^## KPK-' knowledge_base.md) 个KPK知识点"
echo "  - 11 道药膳方"
echo "  - 7 种中医体质辨识"
echo "  - 4 种中医辨证证型"
echo "  - 治未病四期干预（未病先防→欲病救萌→既病防变→瘥后防复）"
echo ""
echo "使用方法：将 Skill 配置文件加载到您的 AI 平台即可使用。"
