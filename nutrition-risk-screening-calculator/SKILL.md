---
name: nutrition-risk-screening-calculator
version: 0.1.0
description: 临床营养风险筛查计算器，内置 NRS-2002、MUST、MNA-SF、STRONGkids 四种国际通用量表，输入体征后即可输出维度分、风险等级与处置建议。中文优先，可输出 JSON 供系统集成。
license: MIT
tags: [nutrition, screening, nrs-2002, must, mna-sf, strongkids, clinical, calculator, chinese]
triggers:
  - 营养风险筛查
  - 营养风险评分
  - NRS-2002 计算
  - MUST 评分
  - MNA-SF 老年营养评估
  - STRONGkids 儿童营养风险
  - 住院患者营养风险
  - 营养不良筛查工具
  - 营养筛查量表
---

# 营养风险筛查计算器 (Nutrition Risk Screening Calculator)

> 把"营养风险筛查"这件临床琐事变成一条命令：输入 BMI、体重下降、进食量、疾病严重程度等体征，立刻得到**维度分 + 风险等级 + 处置建议**。

## 概览

| 项 | 内容 |
|----|------|
| 名称 | 营养风险筛查计算器 |
| 版本 | 0.1.0 |
| 内置量表 | NRS-2002（住院成人）/ MUST（通用）/ MNA-SF（老年 ≥65）/ STRONGkids（儿童） |
| 适用场景 | 入院筛查、门诊初筛、社区体检、科研入组前营养风险评估 |
| 输出 | 维度分、总分、风险等级（低/中/高/无）、风险说明、处置建议、免责声明 |
| 许可证 | MIT |
| 语言 | 中文优先，输出支持 JSON（便于系统对接） |

## 支持的量表与适用人群

| 量表 | 适用人群 | 计分维度 | 风险切点 |
|------|---------|---------|---------|
| **NRS-2002** | 住院成人（中国住院患者首选，ESPEN 推荐） | 营养状态(A) + 疾病严重程度(B) + 年龄附加(≥70) | 总分 ≥ 3 → 有营养风险 |
| **MUST** | 所有人群（英国 BAPEN 通用） | BMI + 体重下降 + 急性疾病 | 任一项 = 2 或合计 ≥ 2 → 高危 |
| **MNA-SF** | 老年人（≥65 岁）精简版 | 6 项（进食/体重/活动/应激/认知/BMI 或小腿围） | 0–7 营养不良 / 8–11 风险 / 12–14 正常 |
| **STRONGkids** | 儿童（≥1月，荷兰常用） | 主观评估 + 高危病 + 摄入 + 体重/生长 | 0 低 / 1–3 中 / ≥4 高 |
| **STAMP** | 儿科（2–17 岁，中国质控中心 2021 推荐） | 疾病风险 + 膳食摄入 + 人体测量 | ≤1 低 / 2–3 中 / ≥4 高 |

## 临床实施要点（2025 专家共识）

| 项目 | 要求 |
|------|------|
| 筛查时机 | **入院后 24 小时内**完成首筛 |
| 适用年龄（NRS-2002） | 18–90 岁住院成人（超过此范围需结合其他方法） |
| 执行人员 | 受培训的医师、营养师、药师或护士 |
| 复筛 | NRS-2002 < 3 分的患者如住院时间较长，**1 周后再次筛查** |
| 不适用 NRS-2002 | 严重腹水/水肿（BMI 失真）、意识障碍无法回答问题、次日 8 点前急诊手术、住院不过夜 |

> 本表参考 2025 营养风险及营养风险筛查工具临床应用专家共识（NUSOC 协作组）及 医启论 各指南要点汇总（2026-04-18）。

## 快速使用（CLI）

```bash
# NRS-2002：BMI 17.2、近 2 月体重降 8%、进食 60%、疾病中度(2)、年龄 72
python -m src.cli nrs2002 --bmi 17.2 --weight-loss-pct 8 --weight-loss-months 2 \
    --intake-pct 60 --disease-severity 2 --age 72

# MUST
python -m src.cli must --bmi 17.0 --weight-loss-pct 8 --acute-no-intake

# MNA-SF（老年）
python -m src.cli mna-sf --appetite 1 --weight-loss 2 --mobility 1 \
    --stress 0 --neuro 0 --bmi 21.5

# STRONGkids（儿童）
python -m src.cli strongkids --clinical 0 --high-risk-disease 2 --intake 1 --growth 1

# JSON 输出（便于集成）
python -m src.cli nrs2002 --bmi 16.8 --disease-severity 3 --age 65 --json
```



## 各量表输入字段

### NRS-2002
- `bmi`：体质指数 kg/m²；评分：<18.5→3 分，18.5–20.5→2 分，≥20.5→0 分
- `weight-loss-pct` / `weight-loss-months`：近 X 月体重下降百分比
- `intake-pct`：近一周进食量占正常的百分比（0–100）
- `disease-severity`：疾病严重程度 0–3（0 正常 / 1 轻度慢性 / 2 中度如大手术·卒中·重症肺炎 / 3 重度如 ICU·移植）
- `age`：年龄（≥70 自动 +1）

### MUST
- `bmi`：体质指数
- `weight-loss-pct`：近 3–6 月体重下降百分比
- `acute-no-intake`：急性疾病致 >5 天无进食

### MNA-SF（6 项，每项 0–2/3 分）
- `appetite` 食量下降 / `weight-loss` 近三月体重下降 / `mobility` 活动能力 / `stress` 应激或急性病 / `neuro` 神经心理问题
- `bmi` 或 `calf-cm`（小腿围，≥31cm 计 3 分；本量表分越高越好）

### STRONGkids（4 项，0–2 分）
- `clinical` 主观临床评估 / `high-risk-disease` 高危疾病 / `intake` 营养摄入下降 / `growth` 体重下降或生长迟缓

## 计分依据（参考）

- **NRS-2002**：Kondrup J, et al. *Clin Nutr*. 2003;22(3):321-36.
- **MUST**：Malnutrition Universal Screening Tool, BAPEN 2003.
- **MNA-SF**：Rubenstein LZ, et al. *J Gerontol A Biol Sci Med Sci*. 2001;56(6):M366-72.
- **STRONGkids**：Hulst J, et al. *Clin Nutr*. 2010;29(1):106-11.

完整评分细则见 `references/scoring.md`。

## 安全红线（务必遵守）

> 本工具是**筛查**而非**诊断**。以下为不可逾越的边界：

1. ❌ 不得输出"治疗/治愈/处方/用药/剂量"等临床处置结论。
2. ❌ 阳性结果不得替代临床营养师或医师的面诊与综合评估。
3. ✅ 所有输出必须附带免责声明，建议阳性者 24–48h 内由临床营养科评估。
4. ✅ BMI、体重下降等输入需在合理医学范围，越界由校验器拦截并提示。

## 架构

```
src/
├── schemas/screening.py   # Pydantic 数据模型（中文字段名）
├── calculators/           # NRS-2002 / MUST / MNA-SF / STRONGkids 算法
├── validators/validator.py# 输入范围校验 + 红线校验
└── cli.py                 # Typer 命令行入口
```

详情见 `README.md`。许可证见 `LICENSE`（MIT）。
