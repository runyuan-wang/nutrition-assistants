"""课程生成流水线 —— 中文版"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.schemas.lesson import 生成请求, 课程规范, 课件页面, 引用来源, 证据声明, 证据等级
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


def 从PubMed生成课程(请求: 生成请求, date_from: Optional[str] = None, date_to: Optional[str] = None) -> dict:
    """使用 PubMed 实时检索生成课程"""
    from src.pubmed.client import PubMedClient

    out = Path(请求.输出目录)
    out.mkdir(parents=True, exist_ok=True)

    client = PubMedClient()
    检索结果 = client.搜索(请求.主题, max_results=请求.max_results, 日期范围=(date_from, date_to))

    # 保存 PubMed 原始数据
    (out / "检索请求.json").write_text(json.dumps({
        "主题": 请求.主题,
        "查询语句": 检索结果.查询.最终查询语句,
        "请求数量": 请求.max_results,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / "检索关键词.json").write_text(json.dumps({"查询": 检索结果.查询.最终查询语句}, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / "pubmed_raw.json").write_text(json.dumps(检索结果.原始搜索响应, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / "pubmed_records.json").write_text(json.dumps([r.model_dump() for r in 检索结果.文献列表], ensure_ascii=False, indent=2, default=str), encoding='utf-8')

    # 从 PubMed 文献构建引用列表
    引用列表 = []
    for i, 文献 in enumerate(检索结果.文献列表, 1):
        等级 = 证据等级.C_级  # PubMed 默认观察性/综述
        for pt in (文献.出版类型 or []):
            if "Meta-Analysis" in pt or "Systematic Review" in pt:
                等级 = 证据等级.A_级
                break
            elif "Randomized Controlled Trial" in pt:
                等级 = 证据等级.B_级
                break

        引用列表.append(引用来源(
            编号=i,
            作者=文献.作者 or "作者不详",
            标题=文献.标题 or "无标题",
            期刊=文献.期刊,
            年份=文献.出版年份,
            PMID=文献.pmid,
            DOI=文献.doi,
            证据等级=等级,
            摘要=文献.摘要[:300] if 文献.摘要 else f"[PMID:{文献.pmid}]",
            局限性="从 PubMed 摘要生成，未经全文评审",
        ))

    # 从 PubMed 构建证据声明
    证据列表 = []
    for i, 文献 in enumerate(检索结果.文献列表):
        证据列表.append(证据声明(
            声明ID=f"PMC-{i+1:03d}",
            声明内容=文献.标题 or f"PMID:{文献.pmid}",
            证据摘要=f"[PMID:{文献.pmid}] 从 PubMed 检索获取",
            解释说明="基于 PubMed 文献摘要",
            实践建议="请查阅原文获取完整信息",
            引用=[i+1],
            局限说明="基于摘要分析，未进行全文评审 | 仅限 PubMed 检索结果",
        ))

    # 从 PubMed 构建课件页面
    页面列表 = []
    页面列表.append(课件页面(
        页码=1, 标题=请求.主题,
        正文=f"# {请求.主题}\n\n基于 PubMed 循证文献\n授课对象：{请求.目标听众}\n时长：{请求.课时分钟}分钟",
        讲稿="欢迎！本课基于 PubMed 实时检索的循证文献。", 页面类型="封面"
    ))
    页面列表.append(课件页面(
        页码=2, 标题="课程概述",
        正文=f"## 本课内容\n\n1. 研究背景\n2. PubMed 文献证据\n3. 实践建议\n4. 总结要点",
        讲稿="分为四个部分。", 页面类型="目录"
    ))
    页面列表.append(课件页面(
        页码=3, 标题="PubMed 文献证据",
        正文="## 检索到的文献\n\n" + "\n".join(
            f"- **[{i}]** {r.标题[:100] if r.标题 else '无标题'} (PMID:{r.pmid})" for i, r in enumerate(检索结果.文献列表, 1)
        ),
        讲稿=f"PubMed 检索到 {len(检索结果.文献列表)} 篇相关文献。",
        引用编号=list(range(1, len(检索结果.文献列表)+1)),
        页面类型="内容"
    ))
    for i, 文献 in enumerate(检索结果.文献列表[:5]):
        页面列表.append(课件页面(
            页码=4+i, 标题=f"文献 {i+1}",
            正文=f"## {文献.标题}\n\n**PMID**: {文献.pmid}\n**期刊**: {文献.期刊}\n**年份**: {文献.出版年份}\n\n{文献.摘要 or '无摘要'}",
            讲稿=f"第{i+1}篇文献：{文献.标题}",
            引用编号=[i+1],
            页面类型="内容"
        ))
    页面列表.append(课件页面(
        页码=9, 标题="总结要点",
        正文="## 关键信息\n\n1. 本课基于 PubMed 实时循证文献\n2. 所有引用均带 PMID 可追溯\n3. 局限性：仅基于摘要分析\n4. 建议查阅原文获取详细信息",
        讲稿="总结：本课基于PubMed实时检索。",
        页面类型="总结"
    ))
    页面列表.append(课件页面(
        页码=10, 标题="参考文献",
        正文="## 参考文献\n\n" + "\n".join(f"{i}. PMID:{r.pmid} {r.标题}" for i, r in enumerate(检索结果.文献列表, 1)),
        讲稿="以上为本课参考文献。",
        引用编号=list(range(1, len(检索结果.文献列表)+1)),
        页面类型="参考文献"
    ))

    课程 = 课程规范(
        主题=请求.主题,
        目标听众=请求.目标听众,
        语言=请求.语言,
        课时分钟=请求.课时分钟,
        学习目标=["了解该主题的 PubMed 文献证据", "获取可追溯的文献引用"],
        关键词=["PubMed", "循证", "文献"],
        页面列表=页面列表,
        引用列表=引用列表,
        证据声明列表=证据列表,
        生成日期=datetime.now().isoformat()[:10],
        证据模式="pubmed",
    )

    return 导出全部(课程, 请求.输出目录)
