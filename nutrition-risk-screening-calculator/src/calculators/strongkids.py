"""STRONGkids 儿科营养风险筛查（儿童）。

4 项（主观临床评估/高危疾病/营养摄入/体重或生长），各 0–2 分，满分 8。
0 分 = 低危 / 1–3 分 = 中危 / ≥4 分 = 高危。
参考文献：Hulst J, et al. Clin Nutr. 2010;29(1):106-11.
"""
from __future__ import annotations

from ..schemas.screening import STRONGkids输入, 筛查结果, 筛查工具, 风险等级


def 计算(i: STRONGkids输入) -> 筛查结果:
    total = (
        i.主观临床评估 + i.高危疾病 + i.营养摄入下降 + i.体重下降或生长迟缓
    )

    if total == 0:
        level = 风险等级.低危
    elif total <= 3:
        level = 风险等级.中危
    else:
        level = 风险等级.高危

    note = f"STRONGkids 总分 {total}/8（临床={i.主观临床评估}, 高危病={i.高危疾病}, 摄入={i.营养摄入下降}, 生长={i.体重下降或生长迟缓}）。"
    if level == 风险等级.高危:
        note += "高危：建议营养科会诊，制定营养支持计划。"
        advice = "高危——转营养科，启动营养评估与支持；住院患儿 48h 内评估。"
    elif level == 风险等级.中危:
        note += "中危：需营养监测与膳食指导。"
        advice = "中危——营养监测、膳食指导，每周复评；必要时营养门诊。"
    else:
        note += "低危：暂无营养风险。"
        advice = "低危——常规喂养，病情变化复筛。"

    return 筛查结果(
        工具=筛查工具.STRONGKIDS,
        总分=total,
        维度分={
            "主观临床评估": i.主观临床评估,
            "高危疾病": i.高危疾病,
            "营养摄入下降": i.营养摄入下降,
            "体重下降或生长迟缓": i.体重下降或生长迟缓,
        },
        风险等级=level,
        风险说明=note,
        建议=advice,
    )
