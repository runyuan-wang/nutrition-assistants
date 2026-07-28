"""NRS-2002 营养风险筛查 2002（住院成人，ESPEN / 中国住院患者首选）。

计分 = 营养状态(A) + 疾病严重程度(B) + 年龄附加(≥70 岁 +1)。
总分 ≥ 3 → 存在营养风险；< 3 → 无明确风险，建议每周复筛。
参考文献：Kondrup J, et al. Clin Nutr. 2003;22(3):321-36.
"""
from __future__ import annotations

from ..schemas.screening import NRS2002输入, 筛查结果, 筛查工具, 风险等级


def _营养状态分(i: NRS2002输入) -> int:
    """取 BMI / 体重下降 / 进食量 三个维度中最重的一档作为 A 分。

    评分参考中华医学会肠外肠内营养学分会推荐的中国简化版：
    - BMI <18.5 → 3（重度）、18.5–20.5 → 2（中度）、≥20.5 → 0
    - 体重下降 >5%  1个月内 → 3、2个月内 → 2、3个月内 → 1
    - 进食量 0–25% → 3、26–50% → 2、51–75% → 1
    """
    scores: list[int] = []

    if i.bmi is not None:
        if i.bmi < 18.5:
            scores.append(3)
        elif i.bmi < 20.5:
            scores.append(2)
        else:
            scores.append(0)

    if i.近三月体重下降百分比 is not None and i.体重下降观察月数 is not None:
        pct, months = i.近三月体重下降百分比, i.体重下降观察月数
        if pct > 5 and months <= 1:
            scores.append(3)
        elif pct > 5 and months <= 2:
            scores.append(2)
        elif pct >= 5 and months <= 3:
            scores.append(1)
        else:
            scores.append(0)

    if i.近一周进食量占正常百分比 is not None:
        p = i.近一周进食量占正常百分比
        if p <= 25:
            scores.append(3)
        elif p <= 50:
            scores.append(2)
        elif p <= 75:
            scores.append(1)
        else:
            scores.append(0)

    return max(scores) if scores else 0


def 计算(i: NRS2002输入) -> 筛查结果:
    a = _营养状态分(i)
    b = i.疾病严重程度评分
    age_add = 1 if i.年龄 >= 70 else 0
    total = a + b + age_add
    has_risk = total >= 3

    return 筛查结果(
        工具=筛查工具.NRS2002,
        总分=total,
        维度分={
            "营养状态评分(A)": a,
            "疾病严重程度评分(B)": b,
            "年龄附加(≥70)": age_add,
        },
        风险等级=风险等级.高危 if has_risk else 风险等级.无风险,
        风险说明=(
            f"NRS-2002 总分 {total}（A={a}, B={b}, 年龄附加={age_add}）。"
            + ("≥3 分：存在营养风险，建议营养科会诊并制定营养支持计划。"
               if has_risk else
               "<3 分：目前无明确营养风险，建议每周复筛；若临床状况变化需重新评估。")
        ),
        建议=(
            "存在营养风险者应在 24–48h 内由临床营养师评估，必要时启动肠内/肠外营养支持。"
            if has_risk else
            "维持常规膳食，每周复筛；临床状况变化随时重新评估。"
        ),
    )
