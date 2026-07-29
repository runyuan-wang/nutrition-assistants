# 示例 (Examples)

以下为四个量表的典型输入与输出，可直接复制运行。

## NRS-2002（住院成人，高危示例）

```bash
python -m src.cli nrs2002 --bmi 17.2 --weight-loss-pct 8 --weight-loss-months 2 \
    --intake-pct 60 --disease-severity 2 --age 72
```
- 维度分：A=2, B=2, 年龄附加=1 → 总分 5
- 风险等级：**高危**（≥3 分）

## MUST（通用，高危示例）

```bash
python -m src.cli must --bmi 17.0 --weight-loss-pct 8 --acute-no-intake
```
- 维度分：BMI=2, 体重下降=1, 急性病=2 → 合计 5
- 风险等级：**高危**（任一项=2）

## MNA-SF（老年，营养不良示例）

```bash
python -m src.cli mna-sf --appetite 1 --weight-loss 2 --mobility 1 \
    --stress 0 --neuro 0 --bmi 21.5
```
- 总分 5/14
- 风险等级：**高危（营养不良）**

## STRONGkids（儿童，高危示例）

```bash
python -m src.cli strongkids --clinical 1 --high-risk-disease 2 --intake 1 --growth 1
```
- 总分 5/5
- 风险等级：**高危**（≥4）

## JSON 输出（系统对接）

```bash
python -m src.cli nrs2002 --bmi 16.8 --disease-severity 3 --age 65 --json
```

> ⚠️ 所有结果仅为营养风险筛查，不能替代临床营养诊断与医师面诊。
