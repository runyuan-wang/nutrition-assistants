"""MNA-SF 微型营养评估精简版（老年 ≥65 岁）。

6 项（进食/体重下降/活动/应激/认知/BMI 或小腿围），满分 14。
12–14 正常 / 8–11 有营养不良风险 / 0–7 营养不良。
参考文献：Rubenstein LZ, et al. J Gerontol A Biol Sci Med Sci. 2001;56(6):M366-72.
"""
from __future__ import annotations

from ..schemas.screening import MNA_SF输入, 筛查结果, 筛查工具, 风险等级


def _bmi分项(i: MNA_SF输入) -> tuple[int, str]:
    # MNA-SF 为"分越高越好"：BMI≥23→3，21–23→2，19–21→1，<19→0
    if i.bmi is not None:
        if i.bmi >= 23:
            return 3, f"BMI={i.bmi:.1f} → 3"
        if i.bmi >= 21:
            return 2, f"BMI={i.bmi:.1f} → 2"
        if i.bmi >= 19:
            return 1, f"BMI={i.bmi:.1f} → 1"
        return 0, f"BMI={i.bmi:.1f} → 0"
    if i.小腿围_cm is not None:
        # 小腿围≥31cm 计 3 分（正常），<31cm 计 0 分
        s = 3 if i.小腿围_cm >= 31 else 0
        return s, f"小腿围={i.小腿围_cm:.1f}cm（≥31 计 3）→ {s}"
    return 0, "BMI 与小腿围均缺失，按 0 计，建议补充测量"


def 计算(i: MNA_SF输入) -> 筛查结果:
    lifestyle = (
        i.食量下降 + i.近三月体重下降 + i.活动能力
        + i.应激或急性疾病 + i.神经心理问题
    )
    bmi_s, bmi_note = _bmi分项(i)
    total = lifestyle + bmi_s

    if total >= 12:
        level, status = 风险等级.低危, "营养状况正常"
    elif total >= 8:
        level, status = 风险等级.中危, "有营养不良风险"
    else:
        level, status = 风险等级.高危, "营养不良"

    note = (
        f"MNA-SF 总分 {total}/14（生活方式 5 项合计 {lifestyle}，{bmi_note}）。{status}。"
    )
    if level == 风险等级.高危:
        advice = "营养不良——尽快由临床营养师全面评估，制定个体化营养干预。"
    elif level == 风险等级.中危:
        advice = "有风险——加强膳食指导与监测，择期复评；必要时营养门诊。"
    else:
        advice = "营养状况正常——维持，定期（如每 3–6 月）复筛。"

    return 筛查结果(
        工具=筛查工具.MNA_SF,
        总分=total,
        维度分={
            "食量下降": i.食量下降,
            "近三月体重下降": i.近三月体重下降,
            "活动能力": i.活动能力,
            "应激或急性疾病": i.应激或急性疾病,
            "神经心理问题": i.神经心理问题,
            "BMI/小腿围分项": bmi_s,
        },
        风险等级=level,
        风险说明=note,
        建议=advice,
    )
