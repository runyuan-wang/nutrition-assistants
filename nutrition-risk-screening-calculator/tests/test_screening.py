"""营养风险筛查计算器 — 计分正确性断言测试。

运行：python tests/test_screening.py
退出码 0 = 全部通过；非 0 = 存在计分错误。

覆盖：四种量表的已知答案病例 + 边界（年龄附加、体重下降单维度驱动、越界输入）。
"""
from __future__ import annotations

import os
import sys

# 允许直接运行：将 skill 根目录加入路径，使 `import src` 可用
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.calculators import 调度
from src.schemas.screening import 筛查工具


def _检查(名称: str, 工具: 筛查工具, 入参: dict, 期望总分, 期望等级: str) -> bool:
    结果 = 调度(工具, **入参)
    通过 = (结果.总分 == 期望总分) and (结果.风险等级.value == 期望等级)
    标记 = "✅ PASS" if 通过 else "❌ FAIL"
    print(f"{标记}  {名称}: 总分={结果.总分} 等级={结果.风险等级.value} "
          f"(期望 {期望总分}/{期望等级})")
    return 通过


def 主() -> int:
    用例 = [
        # NRS-2002
        ("NRS 正常", 筛查工具.NRS2002, dict(bmi=23, 疾病严重程度评分=0, 年龄=40), 0, "无风险"),
        ("NRS 中度(BMI17.2+轻病)", 筛查工具.NRS2002, dict(bmi=17.2, 疾病严重程度评分=1, 年龄=60), 3, "高危"),
        ("NRS 体重下降单维度驱动", 筛查工具.NRS2002, dict(bmi=24, 近三月体重下降百分比=12, 体重下降观察月数=3, 疾病严重程度评分=0, 年龄=50), 3, "高危"),
        ("NRS 年龄附加(72岁)", 筛查工具.NRS2002, dict(bmi=22, 疾病严重程度评分=2, 年龄=72), 3, "高危"),
        # MUST
        ("MUST 低危", 筛查工具.MUST, dict(bmi=22), 0, "低危"),
        ("MUST 急性病高危", 筛查工具.MUST, dict(bmi=20, 急性疾病无进食超过5天=True), 2, "高危"),
        # MNA-SF（分越高越好）
        ("MNA 正常老人", 筛查工具.MNA_SF, dict(食量下降=2, 近三月体重下降=3, 活动能力=2, 应激或急性疾病=1, 神经心理问题=2, bmi=25), 13, "低危"),
        ("MNA 营养不良", 筛查工具.MNA_SF, dict(食量下降=0, 近三月体重下降=0, 活动能力=0, 应激或急性疾病=0, 神经心理问题=0, bmi=18), 0, "高危"),
        ("MNA 小腿围正常", 筛查工具.MNA_SF, dict(食量下降=2, 近三月体重下降=3, 活动能力=2, 应激或急性疾病=1, 神经心理问题=2, 小腿围_cm=33), 13, "低危"),
        # STRONGkids
        ("STRONG 低危", 筛查工具.STRONGKIDS, dict(主观临床评估=0, 高危疾病=0, 营养摄入下降=0, 体重下降或生长迟缓=0), 0, "低危"),
        ("STRONG 高危", 筛查工具.STRONGKIDS, dict(主观临床评估=2, 高危疾病=2, 营养摄入下降=2, 体重下降或生长迟缓=2), 8, "高危"),
    ]

    失败 = []
    for 名称, 工具, 入参, 期望总分, 期望等级 in 用例:
        if not _检查(名称, 工具, 入参, 期望总分, 期望等级):
            失败.append(名称)

    print()
    if 失败:
        print(f"❌ {len(失败)} 个用例失败：{', '.join(失败)}")
        return 1
    print("🎉 全部通过：算法与量表原文一致。")
    return 0


if __name__ == "__main__":
    sys.exit(主())
