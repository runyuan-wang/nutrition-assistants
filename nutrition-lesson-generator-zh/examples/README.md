# 示例课件

本目录包含「膳食纤维与肠道健康」主题的真实生成输出（Mock 模式），由本 Skill 的 CLI 自动生成。

## 复现命令

```bash
pip install -r requirements.txt

python -m src.main generate \
  --topic "膳食纤维与肠道健康" \
  --audience "普通成年人" \
  --duration 30 \
  --output-dir examples/膳食纤维与肠道健康
```

## 输出文件

```
examples/膳食纤维与肠道健康/
├── 课程规范.json    # 规范化 Pydantic 课程包
├── 课程大纲.md      # 逐页大纲
├── 讲稿.md          # 每页讲稿
├── 参考文献.md      # 完整引用（GB/T 7714）
├── 质量报告.md      # 验证报告
└── 营养课程.pptx    # 可编辑 PowerPoint（9 页，千里江山图配色）
```

## 设计要点（本示例体现）

- 第 3~6 页内容页右上角渲染**证据等级徽章**（A级系统综述 / D级指南）
- 第 3 页底部渲染**中国 DRIs 参考框**（膳食纤维 25–30 g/d，来自 `china_dris.json`）
- 第 7 页为**常见误区**页（❌误区 / ✅事实 对照）
- 第 9 页为**参考文献**页（含 PMID 与 GB/T 7714 格式）

> 质量检查：🟢 全部通过（无 error / warning 级问题）。
