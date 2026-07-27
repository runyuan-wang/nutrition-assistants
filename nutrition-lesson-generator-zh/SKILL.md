---
name: nutrition-lesson-generator-zh
version: 0.1.0
last_changed_at: 2026-07-27T12:00:00+08:00
description: |
  中文营养课程生成器 —— 将营养主题转化为结构化的中文课件包，
  导出可编辑的 PowerPoint。支持离线 Mock 模式和 PubMed 证据检索模式。
  适配中国营养语境：卫健委食养指南、中国居民膳食指南、中医食养。
triggers:
  - 生成营养课程
  - 制作营养课件
  - 营养教育PPT
  - 做营养科普幻灯片
  - 膳食纤维课件
  - 循证营养课程
  - 生成中文营养讲稿
  - 营养课大纲
non_triggers:
  - 视频生成
  - 语音生成
  - 图片生成
  - 网页应用
  - 医学诊断
  - 处方开具
  - 补充剂剂量
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
    description: 证据来源 —— 'mock'（离线模式）或 'pubmed'（NCBI 实时检索）。
---

# 中文营养课程生成器 Skill

当用户要求生成中文营养教育课程、课件、讲稿或循证教学材料时使用。

## 调用时机

- 用户想要某个营养主题的中文课程（如膳食纤维、饮水健康、宏量营养素等）
- 用户想要给健康教育者、营养师或普通公众使用的中文 PowerPoint
- 用户想要结构化的中文讲稿和参考文献
- 用户明确要求中文学术证据支撑的营养课件
- 用户提到中国营养指南（中国居民膳食指南、卫健委食养指南等）

## 不调用时机

- 用户要求医学诊断、治疗方案、处方变更或补充剂剂量
- 用户要求视频/语音/图片生成或网页应用
- 用户要求为特定个人提供健康建议

## 与中国营养语境的适配

### 证据来源优先级

1. **中国权威指南**（优先引用）：
   - 国家卫生健康委食养指南系列（糖尿病/肥胖/痛风/高血压/高脂血症/CKD 等）
   - 《中国居民膳食指南（2022）》
   - 中华中医药学会指南（治未病干预系列）
   - 中国营养学会相关标准

2. **PubMed 国际文献**（补充引用）：
   - 中英文文献均可
   - 英文文献引用时需提供中文摘要翻译

### 中医食养内容适配

- 当主题涉及中医养生（如食疗、药膳、体质调理），优先使用 KPK 知识库中的食药物质数据
- 中医术语保持中文原词 + 必要的 pinyin 标注
- 体质辨识和辨证分型内容适配中国临床实际

### 中国公共卫生语境

- 数字使用中国统计口径（发病率用中国数据）
- 食物份量用中国传统单位（克、毫升、两），同时标注公制
- 食物举例以中国市场常见品种为主

## 安全证据规则

1. 每一条实质性健康声明必须引用参考文献
2. 观察性关联不得转化为因果声明
3. `证据描述`、`解释说明`、`实践建议` 三者分离
4. 不得包含疾病诊断、治疗承诺、处方、补充剂剂量或用药变更建议
5. 必须包含局限性和人群/适用性说明
6. 标记无支撑的数字声明
7. 仅使用已验证的引用；PubMed 模式使用 NCBI 实时检索记录
8. 不得编造 PMID、DOI、标题或作者名

## 输出结构

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

## 课件结构模板（中文版）

每节标准课程包含以下页面结构：

| 页码 | 标题模板 | 内容说明 |
|------|---------|---------|
| 1 | 封面页 | 主题 + 副标题 + 作者/日期 |
| 2 | 目录/概述 | 本课将要涵盖的内容要点 |
| 3 | 背景介绍 | 为什么要关注这个营养话题 |
| 4 | 关键概念 | 核心术语定义 |
| 5~8 | 主体内容（上） | 证据 + 数据 + 原理 |
| 9~12 | 主体内容（下） | 实操建议 + 案例 |
| 13 | 常见误区 | 大众易犯的 3-5 个错误 |
| 14 | 总结要点 | 3-5 条关键信息 |
| 15 | 参考文献 | 带 PMID/来源的引用列表 |
| 16 | 免责声明 | 标准免责 + 进一步阅读建议 |

## CLI 用法

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

## 验证关卡

1. `课程规范.json` 通过 Pydantic 模型校验
2. `营养课程.pptx` 非空、可被 `pptx.Presentation` 重新打开
3. 所有预期输出文件均存在
4. 质量报告来源于实际结构化声明和引用
5. 无疾病治疗或因果夸大问题
6. PubMed 模式下每个 PMID 可追溯

## 架构概要

- `src/schemas/lesson.py` — 规范化 Pydantic 模型（中文字段）
- `src/providers/` — 提供者接口 + MockProvider + 中文指南 Provider
- `src/pubmed/` — NCBI E-utilities 客户端及中文适配
- `src/pipeline/generator.py` — 编排生成、检索和导出
- `src/pipeline/validator.py` — 证据/安全质量检查
- `src/exporters/ppt.py` — PowerPoint 中文导出
- `templates/` — 中文课件样式模板
- `examples/` — 中文营养主题示例 fixture

## 局限性

- 当前版本 MVP 支持中文（zh），英文/日文为后续版本功能
- Mock 模式使用预设 fixture，任意主题使用安全占位课件
- PubMed 模式仅检索和模板化，不进行全文分析或临床评估
- 不包含 LLM 提供者、RAG 指南数据库、Web UI 或视频/语音/图片生成
