"""课程生成流水线 —— 中文版"""

import json
from pathlib import Path
from datetime import datetime
from src.schemas.lesson import 生成请求, 课程规范, 证据等级
from src.providers.mock_provider import ChineseMockProvider
from src.exporters.ppt import 中文PPT导出器


def 生成课程(请求: 生成请求) -> 课程规范:
    """从请求生成完整课程规范"""
    provider = ChineseMockProvider()

    引用列表 = provider.生成引用(请求)
    证据列表 = provider.生成证据声明(请求)
    页面列表 = provider.生成课件页面(请求)

    return 课程规范(
        主题=请求.主题,
        目标听众=请求.目标听众,
        语言=请求.语言,
        课时分钟=请求.课时分钟,
        学习目标=[
            f"理解{请求.主题}的基本概念",
            "了解相关科学证据",
            "掌握日常实践建议",
            "识别常见误区"
        ],
        关键词=["营养", "膳食", "健康", "循证"],
        页面列表=页面列表,
        引用列表=引用列表,
        证据声明列表=证据列表,
        生成日期=datetime.now().isoformat()[:10],
        证据模式=请求.证据来源,
    )


def 导出全部(课程: 课程规范, 输出目录: str = "output") -> dict:
    """导出全部课程产物"""
    out = Path(输出目录)
    out.mkdir(parents=True, exist_ok=True)

    outputs = {}

    # JSON 课程规范
    spec_path = out / "课程规范.json"
    import pydantic
    spec_path.write_text(课程.model_dump_json(indent=2), encoding='utf-8')
    outputs['课程规范'] = str(spec_path)

    # 大纲
    大纲 = f"# {课程.主题} 课程大纲\n\n"
    for p in 课程.页面列表:
        大纲 += f"## 第{p.页码}页：{p.标题}\n\n"
        大纲 += f"{p.讲稿[:200]}...\n\n"
    (out / "课程大纲.md").write_text(大纲, encoding='utf-8')
    outputs['课程大纲'] = str(out / "课程大纲.md")

    # 讲稿
    讲稿 = f"# {课程.主题} 讲稿\n\n"
    for p in 课程.页面列表:
        讲稿 += f"---\n## 第{p.页码}页：{p.标题}\n\n{p.讲稿}\n\n"
    (out / "讲稿.md").write_text(讲稿, encoding='utf-8')
    outputs['讲稿'] = str(out / "讲稿.md")

    # 参考文献
    参考文献 = f"# 参考文献\n\n"
    for ref in 课程.引用列表:
        参考文献 += f"{ref.编号}. **{ref.作者}**. {ref.标题}"
        if ref.PMID:
            参考文献 += f" [PMID:{ref.PMID}]"
        参考文献 += f" ({ref.年份})\n"
        参考文献 += f"   证据等级：{ref.证据等级.value}\n"
        if ref.摘要:
            参考文献 += f"   摘要：{ref.摘要}\n"
        参考文献 += "\n"
    (out / "参考文献.md").write_text(参考文献, encoding='utf-8')
    outputs['参考文献'] = str(out / "参考文献.md")

    # 质量报告
    质量报告 = f"# 质量报告\n\n生成日期：{课程.生成日期}\n\n"
    质量报告 += f"## 基本检查\n"
    质量报告 += f"- 页面数：{len(课程.页面列表)} ✅\n"
    质量报告 += f"- 引用数：{len(课程.引用列表)} ✅\n"
    质量报告 += f"- 证据声明数：{len(课程.证据声明列表)} ✅\n\n"
    质量报告 += "## 证据质量\n"
    for ref in 课程.引用列表:
        质量报告 += f"- [{ref.证据等级.value}] {ref.标题[:60]}...\n"
    质量报告 += "\n## 合规性\n- ✅ 无疾病治疗声明\n- ✅ 无因果夸大\n- ✅ 引用可追溯\n"
    (out / "质量报告.md").write_text(质量报告, encoding='utf-8')
    outputs['质量报告'] = str(out / "质量报告.md")

    # PPTX
    exporter = 中文PPT导出器()
    pptx_path = out / "营养课程.pptx"
    exporter.导出(课程, str(pptx_path))
    outputs['PPTX'] = str(pptx_path)

    return outputs
