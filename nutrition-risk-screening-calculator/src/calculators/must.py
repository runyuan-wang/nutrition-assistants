"""MUST 营养不良通用筛查工具（英国 BAPEN，适用于所有人群）。

三步：BMI + 体重下降 + 急性疾病。任一步 = 2 或合计 ≥ 2 → 高危。
参考文献：Malnutrition Universal Screening Tool, BAPEN 2003.
"""
from __future__ import annotations

from ..schemas.screening import MUST输入, 筛查结果, 筛查工具, 风险等级


def 计算(i: MUST输入) -> 筛查结果:
    bmi_s = 0 if i.bmi >= 20 else (1 if i.bmi >= 18.5 else 2)

    wl = i.近3_6月体重下降百分比
    wl_s = 0
    if wl is not None:
        wl_s = 0 if wl < 5 else (1 if wl <= 10 else 2)

    ac_s = 2 if i.急性疾病无进食超过5天 else 0

    total = bmi_s + wl_s + ac_s

    if bmi_s == 2 or wl_s == 2 or ac_s == 2:
        level = 风险等级.高危
    elif total == 0:
        level = 风险等级.低危
    elif total == 1:
        level = 风险等级.中危
    else:
        level = 风险等级.高危

    note = (
        f"MUST 合计 {total}（BMI={bmi_s}, 体重下降={wl_s}, 急性病={ac_s}）。"
    )
    if level == 风险等级.高危:
        note += "高危：需立即转诊临床营养团队，制定营养护理计划并规律监测。"
        advice = "高危——营养支持小组介入，记录饮食、计划复查（至少每月）。"
    elif level == 风险等级.中危:
        note += "中危：需观察性饮食记录，必要时营养指导。"
        advice = "中危——进行饮食记录，若临床状况变化重新筛查；可转营养门诊。"
    else:
        note += "低危：暂无营养不良风险。"
        advice = "低危——常规膳食，病情变化时复筛。"

    return 筛查结果(
        工具=筛查工具.MUST,
        总分=total,
        维度分={"BMI评分": bmi_s, "体重下降评分": wl_s, "急性疾病评分": ac_s},
        风险等级=level,
        风险说明=note,
        建议=advice,
    )
