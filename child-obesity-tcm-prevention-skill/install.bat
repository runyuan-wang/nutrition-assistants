@echo off
REM 营养学 | 儿童青少年肥胖治未病食养助手 - Windows安装脚本
REM 用法: double-click or run install.bat

echo 正在安装 营养学 ^| 儿童青少年肥胖治未病食养助手...
echo 来源：中华中医药学会《儿童青少年肥胖治未病干预指南》（2026年）
echo.

if exist SKILL.md (
    echo [OK] SKILL.md 已就绪
) else (
    echo [ERR] SKILL.md 缺失
    goto :error
)

if exist knowledge_base.md (
    echo [OK] knowledge_base.md 已就绪
) else (
    echo [ERR] knowledge_base.md 缺失
    goto :error
)

if exist dietary_formulas.md (
    echo [OK] dietary_formulas.md 已就绪
) else (
    echo [ERR] dietary_formulas.md 缺失
    goto :error
)

if exist system_prompt.md (
    echo [OK] system_prompt.md 已就绪
) else (
    echo [ERR] system_prompt.md 缺失
    goto :error
)

if exist skill.yaml (
    echo [OK] skill.yaml 已就绪
) else (
    echo [ERR] skill.yaml 缺失
    goto :error
)

echo.
echo 安装完成！本Skill包含：
echo   - 13 个KPK知识点
echo   - 11 道药膳方
echo   - 7 种中医体质辨识
echo   - 4 种中医辨证证型
echo   - 治未病四期干预
echo.
echo 使用方法：将 Skill 配置文件加载到您的 AI 平台即可使用。
pause
goto :eof

:error
echo 安装失败，请确保所有文件完整。
pause
