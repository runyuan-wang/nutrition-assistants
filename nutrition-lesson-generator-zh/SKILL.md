---
name: nutrition-lesson-generator-zh
version: 0.2.0
author: 王润圆（中国注册营养师，昆明医科大学营养与食品卫生学硕士）
last_changed_at: 2026-07-27T23:00:00+08:00
description: |
  中文营养课程生成器 —— 将营养主题转化为结构化的中文课件包，导出可编辑的 PowerPoint。
  基于 nutrition-lesson-generator 设计，适配中国营养语境：卫健委食养指南、中国居民膳食指南、
  中国 DRIs（2023版）、中医食养。支持离线 Mock 模式与 PubMed 证据检索模式，引用采用 GB/T 7714 格式。
triggers:
  - 生成营养课程
  - 制作营养课件
  - 营养教育PPT
  - 做营养科普幻灯片
  - 膳食纤维课件
  - 循证营养课程
  - 生成中文营养讲稿
  - 营养课大纲
  - 中文营养课件
non_triggers:
  - 视频生成
  - 语音生成
  - 图片生成
  - 网页应用
  - 医学诊断
  - 处方开具
  - 补充剂剂量
  - 英文课件
  - 食养指南蒸馏
inputs:
  topic:
    type: string
    required: true
    description: 营养主题（如"膳食纤维与肠道健康""儿童青少年肥胖防治"）。
  audience:
    type: string
    required: false
    default: 普通成年人
    description: 目标听众（如"普通成年人""糖尿病患者""孕产妇""老年人""学龄儿童家长"）。
  language:
    type: string
    required: false
    default: zh
    description: 输出语言（默认中文，可支持 en/ja）。
  duration:
    type: integer
    required: false
    default: 30
    description: 目标课时长度（分钟）。
  output_dir:
    type: string
    required: false
    default: output
    description: 输出目录。
  evidence_source:
    type: string
    required: false
    default: mock
    description: 证据来源 —— 'mock'（离线模式，基于中国指南 fixture）/ 'pubmed'（NCBI 实时检索）。
---

# 中文营养课程生成器 Skill

当用户要求生成中文营养教育课程、课件、讲稿或循证教学材料时使用。本 Skill 基于
[nutrition-lesson-generator](https://github.com/9s5bz2jvd2-lang/nutrition-lesson-generator)
设计，继承其安全证据规则与质量门禁体系，并适配中文输出与中国营养语境。

> 当前版本为纯中文输出 Skill。原版（英文）适用于英文课件场景。

---

## 一、何时调用

- 用户想要某个营养主题的中文课程（如膳食纤维、饮水健康、宏量营养素等）
- 用户想要给健康教育者、营养师或普通公众使用的中文 PowerPoint
- 用户想要结构化的中文讲稿和参考文献
- 用户明确要求中文学术证据支撑的营养课件
- 用户提到中国营养指南（中国居民膳食指南、卫健委食养指南等）

## 二、何时不要调用

- 用户要求医学诊断、治疗方案、处方变更或补充剂剂量
- 用户要求视频/语音/图片生成或网页应用
- 用户要求为特定个人提供健康建议
- 用户要求英文输出（应使用原版 `nutrition-lesson-generator`）
- 用户要求食养指南蒸馏 Skill（应使用对应食养助手 Skill）

---

## 三、安全证据规则（不可逾越）

1. **每条实质性健康声明必须引用参考文献**——无引用的声明不得出现在课件中
2. **观察性关联不得表述为因果结论**——"研究发现高纤维饮食人群心脏病风险较低"不能写成"高纤维饮食预防心脏病"
3. **证据摘要 / 解释说明 / 实践建议 三段必须分开**——证据陈述、营养师解读、实用建议是三个独立字段，不可混写
4. **禁止疾病治疗承诺、诊断建议、处方、补充剂剂量、药物调整建议**
5. **必须包含局限性和适用人群说明**——每条声明需注明研究人群和适用限制
6. **标记未经验证的数值型声明**——如果数值来源不可靠，标记为"待验证"
7. **仅使用已验证的引用**：
   - `mock` 模式：引用中国营养学会、国家卫健委发布的权威文件（内置 fixture）
   - `pubmed` 模式：引用实时从 NCBI 检索的文献记录
8. **严禁捏造 PMID、DOI、标题或作者**——PubMed 检索失败时如实报告，不得回退到编造数据
9. **特殊人群安全门**：涉及孕妇、儿童、老年人、肝肾疾病患者的建议必须标注"需在医师或注册营养师指导下应用"
10. **进食障碍/体重管理**：不得使用羞耻化语言，不得将体重与健康价值直接等同

---

## 四、与中国营养语境的适配

### 证据来源优先级

1. **中国权威指南**（优先引用）：
   - 国家卫生健康委食养指南系列（糖尿病/肥胖/痛风/高血压/高脂血症/CKD 等）
   - 《中国居民膳食指南（2022）》
   - 中华中医药学会指南（治未病干预系列）
   - 中国营养学会相关标准（含 DRIs 2023版）

2. **PubMed 国际文献**（补充引用）：
   - 中英文文献均可
   - 英文文献引用时需提供中文摘要翻译

### 中医食养内容适配

- 当主题涉及中医养生（如食疗、药膳、体质调理），优先使用 KPK 知识库中的食药物质数据
- 中医术语保持中文原词 + 必要的 pinyin 标注
- 体质辨识和辨证分型内容适配中国临床实际
- 课件支持「中医食养」页面类型（`页面类型: 中医食养`），以赭金色强调呈现

### 中国公共卫生语境

- 数字使用中国统计口径（发病率用中国数据）
- 食物份量用中国传统单位（克、毫升、两），同时标注公制
- 食物举例以中国市场常见品种为主
- 涉及营养素推荐量时，引用 `china_dris.json`（中国 DRIs 2023版精选），并自动在相关幻灯片底部渲染「中国 DRIs 参考」提示框

---

## 五、工作流程

本 Skill 为可运行的 Python CLI 项目。从项目根目录 `nutrition-lesson-generator-zh/` 运行。

### 第一步：确定主题与受众

接收用户输入的 `topic`、`audience`、`duration`、`evidence_source`，确定课件标题、学习目标与幻灯片数量。

### 第二步：证据收集

- **mock 模式（默认）**：使用内置中文证据 fixture（`src/providers/mock_provider.py`），基于中国膳食指南、Lancet/Cell 等权威文献的脱敏摘要生成课程。
- **pubmed 模式**：调用 NCBI E-utilities 实时检索（`src/pubmed/client.py`），将检索到的文献构建为引用与证据声明。

### 第三步：生成课件包

运行 CLI 后自动生成：课程规范 JSON、大纲、讲稿、参考文献、质量报告、PowerPoint。

### 第四步：导出 PowerPoint

由 `src/exporters/ppt.py`（中文PPT导出器）渲染，设计要点：
- 16:9 画布，中文字体「微软雅黑」
- 千里江山图配色：青蓝 `#2E75B6` / 苍绿 `#5B8C5A` / 赭金 `#E8A83E`
- 内容页：Markdown 项目符号渲染 + 证据等级徽章（右上角）+ 中国 DRIs 参考框（底部）
- 页面类型：封面 / 目录 / 内容 / 误区 / 总结 / 参考文献 / 中医食养

### 第五步：质量检查

运行后自动执行 `src/pipeline/validator.py` 校验，详见 `references/quality_gates.md`。

---

## 六、中国营养标准参考

关键 DRIs 数据见 `china_dris.json`（中国居民膳食营养素参考摄入量 2023版精选），涵盖：

- 能量（成人按身体活动水平分级）
- 宏量营养素（蛋白质、脂肪、碳水化合物、膳食纤维）
- 矿物质（钙、铁、锌、硒、镁、钾、钠）
- 维生素（A、D、E、K、B族、C）
- 特殊人群（孕妇、乳母、婴幼儿、儿童、老年人）

课件中涉及营养素推荐量时，应引用该数据并注明来源：
> "根据《中国居民膳食营养素参考摄入量（2023版）》，成人每日钙推荐摄入量（RNI）为 800mg"

---

## 七、引用格式（GB/T 7714-2015）

### 专著
```
主要责任者. 题名: 其他题名信息[文献类型标志]. 其他责任者. 版本项. 出版地: 出版者, 出版年: 引文页码.
```
示例：
```
中国营养学会. 中国居民膳食指南(2022)[M]. 北京: 人民卫生出版社, 2022.
```

### 期刊文献
```
主要责任者. 题名[文献类型标志]. 刊名, 年, 卷(期): 页码.
```
示例：
```
REYNOLDS A, MANN J, CUMMINGS J, et al. Carbohydrate quality and human health: a series of systematic reviews and meta-analyses[J]. The Lancet, 2019, 393(10170): 434-445.
```

### 电子文献
```
主要责任者. 题名[文献类型标志/文献载体标志]. (更新或修改日期)[引用日期]. 获取和访问路径.
```

---

## 八、课件结构模板（中文版）

每节标准课程包含以下页面结构（标准 9 页，含常见误区页）：

| 页码 | 页面类型 | 标题模板 | 内容说明 |
|------|---------|---------|---------|
| 1 | 封面 | 主题 | 主题 + 副标题 + 受众/时长 |
| 2 | 目录 | 课程概述 | 本课内容要点 |
| 3 | 内容 | 背景介绍 | 为什么要关注这个营养话题 |
| 4 | 内容 | 核心概念 | 核心术语定义 |
| 5 | 内容 | 科学证据（一） | 证据 + 数据 + 原理 |
| 6 | 内容 | 日常实践建议 | 实操建议 |
| 7 | 误区 | 常见误区 | 大众易犯的 3-5 个错误 |
| 8 | 总结 | 总结要点 | 3-5 条关键信息 |
| 9 | 参考文献 | 参考文献 | 带 PMID/来源的引用列表 |

> 涉及中医食养主题时，可插入「中医食养」页面类型（赭金强调色）。

---

## 九、CLI 用法

从项目根目录 `nutrition-lesson-generator-zh/` 运行。

### 默认离线 Mock 模式

```bash
python -m src.main generate \
  --topic "膳食纤维与肠道健康" \
  --audience "普通成年人" \
  --language zh \
  --duration 30 \
  --output-dir output
```

### 可选 PubMed 证据模式

```bash
python -m src.main generate \
  --topic "膳食纤维与肠道健康" \
  --audience "普通成年人" \
  --language zh \
  --duration 10 \
  --evidence-source pubmed \
  --max-results 10 \
  --output-dir output/pubmed-zh
```

### 仅检索 PubMed 文献（不生成课件）

```bash
python -m src.main retrieve \
  --topic "dietary fiber gut microbiota" \
  --max-results 10 \
  --output output/pubmed-preview
```

---

## 十、输出结构

### Mock 模式（离线）

```
output/
├── 课程规范.json          # 规范化 Pydantic 课程包
├── 课程大纲.md            # 逐页大纲
├── 讲稿.md                # 每页讲稿
├── 参考文献.md            # 完整引用及出处说明
├── 质量报告.md            # 结构化验证报告
└── 营养课程.pptx          # 可编辑 PowerPoint
```

### PubMed 模式

Mock 模式全部文件 +：
```
output/<run>/
├── 检索请求.json
├── 检索关键词.json
├── pubmed_raw.json
├── pubmed_records.json
├── 证据摘要.json
├── 证据可追溯性.json
├── 课程规范.json
├── 课程大纲.md
├── 讲稿.md
├── 参考文献.md
├── 质量报告.md
└── 营养课程.pptx
```

---

## 十一、验证关卡

1. `课程规范.json` 通过 Pydantic 模型校验
2. `营养课程.pptx` 非空、可被 `pptx.Presentation` 重新打开
3. 所有预期输出文件均存在
4. 质量报告来源于实际结构化声明和引用
5. 无疾病治疗或因果夸大问题（validator 错误级检查）
6. PubMed 模式下每个 PMID 可追溯
7. 特殊人群建议标注安全门、无羞耻化语言（validator 警告级检查）

---

## 十二、架构概要

- `src/schemas/lesson.py` — 规范化 Pydantic 模型（中文字段，含证据等级 A-E）
- `src/providers/` — 提供者接口 + MockProvider（中文指南 fixture）
- `src/pubmed/` — NCBI E-utilities 客户端及中文适配
- `src/pipeline/generator.py` — 编排生成、检索和导出
- `src/pipeline/validator.py` — 证据/安全质量检查（含特殊人群与羞耻化语言）
- `src/exporters/ppt.py` — PowerPoint 中文导出（千里江山图配色 + DRIs 参考框）
- `china_dris.json` — 中国居民膳食营养素参考摄入量（2023版）精选数据
- `references/quality_gates.md` — 质量门禁检查清单
- `templates/` — 中文课件样式模板
- `examples/` — 中文营养主题示例输出

---

## 十三、局限性

- 当前版本 MVP 支持中文（zh），英文/日文为后续版本功能
- Mock 模式使用预设 fixture（默认膳食纤维主题），任意主题使用安全占位课件
- PubMed 模式仅检索和模板化，不进行全文分析或临床评估
- 不包含 LLM 提供者、RAG 指南数据库、Web UI 或视频/语音/图片生成
- PPT 当前为简洁卡片式，不含信息图/图表自动生成（未来可扩展）
