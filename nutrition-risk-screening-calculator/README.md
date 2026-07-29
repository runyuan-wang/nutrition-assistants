# 营养风险筛查计算器 · Nutrition Risk Screening Calculator

一个临床营养风险筛查计算器 skill，内置 **NRS-2002 / MUST / MNA-SF / STRONGkids** 四种国际通用量表。输入体征（BMI、体重下降、进食量、疾病严重程度等），即可输出维度分、风险等级与处置建议。中文优先，支持 JSON 输出便于系统集成。

> ⚠️ 本工具仅用于**营养风险筛查**，不能替代临床营养诊断与医师面诊。阳性结果须由临床营养师/医师结合综合评估确认。

## 内置量表

| 量表 | 适用人群 | 风险切点 |
|------|---------|---------|
| NRS-2002 | 住院成人（中国住院患者首选） | 总分 ≥ 3 → 有营养风险 |
| MUST | 所有人群（通用） | 任一项=2 或合计≥2 → 高危 |
| MNA-SF | 老年人 ≥65 岁 | 0–7 营养不良 / 8–11 风险 / 12–14 正常 |
| STRONGkids | 儿童（儿科） | 0 低 / 1–3 中 / 4–5 高（API 字段权重：主观评估=1 / 高危疾病=2 / 摄入或损失=1 / 体重或生长=1，满分 5） |

## 快速开始

```bash
pip install -r requirements.txt
python -m src.cli nrs2002 --bmi 17.2 --weight-loss-pct 8 --weight-loss-months 2 \
    --intake-pct 60 --disease-severity 2 --age 72
```

## 目录结构

```
nutrition-risk-screening-calculator/
├── SKILL.md
├── README.md
├── skill.yaml
├── requirements.txt
├── install.sh
├── LICENSE
├── references/scoring.md      # 完整评分细则
├── examples/                   # 示例输入与输出
└── src/
    ├── schemas/screening.py    # Pydantic 数据模型
    ├── calculators/            # 四种量表算法
    ├── validators/validator.py # 红线与范围校验
    └── cli.py                  # Typer CLI
```

## 引用

- Kondrup J, et al. ESPEN guidelines for nutrition screening 2002. *Clin Nutr*. 2003.
- BAPEN. Malnutrition Universal Screening Tool (MUST). 2003.
- Rubenstein LZ, et al. MNA-SF validation. *J Gerontol A Biol Sci Med Sci*. 2001.
- Hulst J, et al. STRONGkids. *Clin Nutr*. 2010.

## 许可证

MIT License. 禁止抄袭商用——请保留原作者署名（Ryunyuan / 王润圆）。

---

## English Summary

A clinical **nutrition risk screening** calculator skill bundling four validated tools: **NRS-2002** (hospitalized adults), **MUST** (universal), **MNA-SF** (elderly ≥65), and **STRONGkids** (pediatrics). Feed in BMI, weight loss, intake, and disease severity to get dimension scores, risk tier, and action advice. Chinese-primary, with JSON output for integration. Screening only — not a substitute for clinical diagnosis.
