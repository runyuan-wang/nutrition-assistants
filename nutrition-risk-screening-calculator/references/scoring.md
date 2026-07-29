# 评分细则参考 (Scoring Reference)

本文件给出四种量表的完整评分逻辑，供复核与教学使用。

## 1. NRS-2002（住院成人）

**总分 = A(营养状态) + B(疾病严重程度) + 年龄附加(≥70 岁 +1)**

### A. 营养状态受损评分
| 维度 | 评分 |
|------|------|
| BMI < 18.5 | 3（重度） |
| BMI 18.5–20.5 | 2（中度） |
| BMI ≥ 20.5 | 0 |
| 体重下降 > 5%（≤1 月） | 3 |
| 体重下降 > 5%（≤2 月） | 2 |
| 体重下降 ≥ 5%（≤3 月） | 1 |
| 近一周进食量 ≤ 25% | 3 |
| 近一周进食量 26–50% | 2 |
| 近一周进食量 51–75% | 1 |

> 取 BMI / 体重下降 / 进食量 三个维度中**最重一档**作为 A 分。
> 本表采用中国临床简化版（中华医学会肠外肠内营养学分会推荐）；原版 ESPEN NRS-2002 另含 BMI<16.0→3 及一般状况受损修正项。

### B. 疾病严重程度评分
| 评分 | 示例 |
|------|------|
| 0 | 营养需求正常 |
| 1（轻度） | 慢性病：髋骨折、COPD、血透、糖尿病、肿瘤 |
| 2（中度） | 重大腹部手术、卒中、重症肺炎、血液系统恶性肿瘤 |
| 3（重度） | 颅脑损伤、骨髓移植、ICU（APACHE >10） |

**风险切点**：总分 ≥ 3 → 存在营养风险；< 3 → 无明确风险，每周复筛。

---

## 2. MUST（通用）

| 步骤 | 评分 |
|------|------|
| BMI ≥ 20 | 0 |
| BMI 18.5–20 | 1 |
| BMI < 18.5 | 2 |
| 近 3–6 月体重下降 <5% | 0 |
| 体重下降 5–10% | 1 |
| 体重下降 >10% | 2 |
| 急性疾病 >5 天无进食 | 2（否则 0） |

**风险判定**：任一步 = 2，或合计 ≥ 2 → **高危**；合计 = 1 → **中危**；合计 = 0 → **低危**。

---

## 3. MNA-SF（老年 ≥65）

| 项目 | 0 | 1 | 2 | 3 |
|------|---|---|---|---|
| A 食量下降 | 无/良好 | 适中 | 严重 | — |
| B 近三月体重下降 | 无 | 不知 | 1–3 kg | >3 kg |
| C 活动能力 | 外出 | 室内 | 卧床 | — |
| D 应激/急性病 | 无 | 有 | — | — |
| E 神经心理 | 无 | 有 | — | — |
| F BMI | <19→0 | 19–21→1 | 21–23→2 | ≥23→3 |
| F 小腿围* | <31cm→0 | — | — | ≥31cm→3 |

\* BMI 缺失时用小腿围替代 F 项。

**总分（满分 14）**：12–14 正常 / 8–11 有营养不良风险 / 0–7 营养不良。

---

## 4. STRONGkids（儿童）

下表按本 API 字段顺序列出；原量表题目顺序及分值为：高危疾病=2 / 主观临床评估=1 / 营养摄入或损失=1 / 体重下降或生长迟缓=1。

| API 字段（API 顺序） | 0 | 1 | 2 |
|------|---|---|---|
| 主观临床评估（API 第 1 项；原量表第 2 项） | 否 | 是 | — |
| 高危疾病或预计大手术（API 第 2 项；原量表第 1 项） | 否 | — | 是 |
| 营养摄入/损失（API 第 3 项；原量表第 3 项） | 否 | 是 | — |
| 体重下降/生长迟缓（API 第 4 项；原量表第 4 项） | 否 | 是 | — |

**总分（满分 5）**：0 低危（low） / 1–3 中危（moderate） / 4–5 高危（high）。

本 API 字段权重为：主观临床评估=1 / 高危疾病或预计大手术=2 / 营养摄入或损失=1 / 体重下降或生长迟缓=1；每项只能取表中列出的合法值，不可将一分项记为 2 分。

---

## 参考文献
- Kondrup J, Rasmussen HH, Hamberg O, Stanga Z; Ad Hoc ESPEN Working Group. Nutritional risk screening (NRS 2002): a new method based on an analysis of controlled clinical trials. *Clin Nutr*. 2003;22(3):321-36.
- Malnutrition Advisory Group, BAPEN. Malnutrition Universal Screening Tool (MUST). 2003.
- Rubenstein LZ, Harker JO, Salvà A, Guigoz Y, Vellas B. Screening for undernutrition in geriatric practice: developing the Short-Form Mini-Nutritional Assessment (MNA-SF). *J Gerontol A Biol Sci Med Sci*. 2001;56(6):M366-72.
- Hulst JM, Zwart H, Hop WC, Joosten KF. Dutch national survey to test the STRONGkids nutritional risk screening tool in hospitalized children. *Clin Nutr*. 2010;29(1):106-11.
