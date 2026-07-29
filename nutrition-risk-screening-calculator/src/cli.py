"""营养风险筛查计算器 — Typer 命令行入口。

用法：
  python -m src.cli nrs2002  --bmi 17.2 --weight-loss-pct 8 --weight-loss-months 2 \
                             --intake-pct 60 --disease-severity 2 --age 72
  python -m src.cli must     --bmi 17.0 --weight-loss-pct 8 --acute-no-intake
  python -m src.cli mna-sf   --appetite 1 --weight-loss 2 --mobility 1 --stress 0 --neuro 0 --bmi 21.5
  python -m src.cli strongkids --clinical 1 --high-risk-disease 2 --intake 1 --growth 1
加 --json 输出 JSON（便于系统集成）。
"""
from __future__ import annotations

import json
from typing import Optional

import typer

from .calculators import 调度
from .calculators.base import 筛查工具
from .schemas.screening import 筛查结果
from .validators.validator import 校验

app = typer.Typer(help="营养风险筛查计算器：NRS-2002 / MUST / MNA-SF / STRONGkids")


def _映射(工具: 筛查工具, opts: dict) -> dict:
    """英文选项名 → 中文 Pydantic 字段名，并丢弃 None 值。"""
    字段表 = {
        筛查工具.NRS2002: {
            "bmi": "bmi",
            "weight_loss_pct": "近三月体重下降百分比", "weight_loss_months": "体重下降观察月数",
            "intake_pct": "近一周进食量占正常百分比",
            "disease_severity": "疾病严重程度评分", "age": "年龄",
        },
        筛查工具.MUST: {
            "bmi": "bmi", "weight_loss_pct": "近3_6月体重下降百分比",
            "acute_no_intake": "急性疾病无进食超过5天",
        },
        筛查工具.MNA_SF: {
            "appetite": "食量下降", "weight_loss": "近三月体重下降", "mobility": "活动能力",
            "stress": "应激或急性疾病", "neuro": "神经心理问题",
            "bmi": "bmi", "calf_cm": "小腿围_cm",
        },
        筛查工具.STAMP: {
            "disease_risk": "疾病风险评分",
            "dietary_intake": "膳食摄入评分",
            "anthropometry": "人体测量评分",
        },
        筛查工具.STRONGKIDS: {
            "clinical": "主观临床评估", "high_risk_disease": "高危疾病",
            "intake": "营养摄入下降", "growth": "体重下降或生长迟缓",
        },
    }
    table = 字段表[工具]
    return {table[k]: v for k, v in opts.items() if v is not None}


def _打印(结果: 筛查结果, json_mode: bool) -> None:
    if json_mode:
        typer.echo(json.dumps(结果.model_dump(), ensure_ascii=False, indent=2))
        return
    typer.echo(f"\n🔍 营养风险筛查结果 — {结果.工具.value}")
    typer.echo("─" * 48)
    if 结果.维度分:
        typer.echo("维度分：")
        for k, v in 结果.维度分.items():
            typer.echo(f"  · {k}: {v}")
    if 结果.总分 is not None:
        typer.echo(f"总分：{结果.总分}")
    typer.echo(f"风险等级：{结果.风险等级.value}")
    typer.echo("─" * 48)
    typer.echo(f"风险说明：{结果.风险说明}")
    typer.echo(f"建议：{结果.建议}")
    typer.echo(f"免责声明：{结果.免责声明}")

    # 红线校验
    通过, 警告 = 校验(结果)
    for w in 警告:
        typer.echo(w)
    if 通过:
        typer.echo("✅ 红线校验通过（未越界到临床处置）。")


@app.command()
def nrs2002(
    bmi: Optional[float] = typer.Option(None, "--bmi", help="体质指数 kg/m²"),
    weight_loss_pct: Optional[float] = typer.Option(None, "--weight-loss-pct", help="近 X 月体重下降百分比"),
    weight_loss_months: Optional[int] = typer.Option(None, "--weight-loss-months", help="体重下降观察月数"),
    intake_pct: Optional[int] = typer.Option(None, "--intake-pct", help="近一周进食量占正常百分比"),
    disease_severity: int = typer.Option(..., "--disease-severity", help="疾病严重程度 0-3"),
    age: int = typer.Option(..., "--age", help="年龄（≥70 自动 +1）"),
    json_mode: bool = typer.Option(False, "--json", help="输出 JSON"),
):
    结果 = 调度(筛查工具.NRS2002, **_映射(筛查工具.NRS2002, dict(
        bmi=bmi, impaired_gc=impaired_gc, weight_loss_pct=weight_loss_pct,
        weight_loss_months=weight_loss_months, intake_pct=intake_pct,
        disease_severity=disease_severity, age=age)))
    _打印(结果, json_mode)


@app.command()
def must(
    bmi: float = typer.Option(..., "--bmi", help="体质指数 kg/m²"),
    weight_loss_pct: Optional[float] = typer.Option(None, "--weight-loss-pct", help="近 3-6 月体重下降百分比"),
    acute_no_intake: bool = typer.Option(False, "--acute-no-intake", help="急性病致 >5 天无进食"),
    json_mode: bool = typer.Option(False, "--json", help="输出 JSON"),
):
    结果 = 调度(筛查工具.MUST, **_映射(筛查工具.MUST, dict(
        bmi=bmi, weight_loss_pct=weight_loss_pct, acute_no_intake=acute_no_intake)))
    _打印(结果, json_mode)


@app.command("mna-sf")
def mna_sf(
    appetite: int = typer.Option(..., "--appetite", help="食量下降 0-2"),
    weight_loss: int = typer.Option(..., "--weight-loss", help="近三月体重下降 0-3"),
    mobility: int = typer.Option(..., "--mobility", help="活动能力 0-2"),
    stress: int = typer.Option(..., "--stress", help="应激或急性病 0-2"),
    neuro: int = typer.Option(..., "--neuro", help="神经心理问题 0-2"),
    bmi: Optional[float] = typer.Option(None, "--bmi", help="体质指数 kg/m²"),
    calf_cm: Optional[float] = typer.Option(None, "--calf-cm", help="小腿围 cm"),
    json_mode: bool = typer.Option(False, "--json", help="输出 JSON"),
):
    结果 = 调度(筛查工具.MNA_SF, **_映射(筛查工具.MNA_SF, dict(
        appetite=appetite, weight_loss=weight_loss, mobility=mobility,
        stress=stress, neuro=neuro, bmi=bmi, calf_cm=calf_cm)))
    _打印(结果, json_mode)


@app.command()
def stamp(
    disease_risk: int = typer.Option(..., "--disease-risk", help="疾病风险 0/2/3"),
    dietary_intake: int = typer.Option(..., "--dietary-intake", help="膳食摄入 0/2/3"),
    anthropometry: int = typer.Option(..., "--anthropometry", help="人体测量 0/1/3"),
    json_mode: bool = typer.Option(False, "--json", help="输出 JSON"),
):
    结果 = 调度(筛查工具.STAMP, **_映射(筛查工具.STAMP, dict(
        disease_risk=disease_risk, dietary_intake=dietary_intake, anthropometry=anthropometry)))
    _打印(结果, json_mode)


@app.command()
def strongkids(
    clinical: int = typer.Option(..., "--clinical", help="主观临床评估 0/1"),
    high_risk_disease: int = typer.Option(..., "--high-risk-disease", help="高危疾病 0/2"),
    intake: int = typer.Option(..., "--intake", help="营养摄入或损失 0/1"),
    growth: int = typer.Option(..., "--growth", help="体重下降或生长迟缓 0/1"),
    json_mode: bool = typer.Option(False, "--json", help="输出 JSON"),
):
    结果 = 调度(筛查工具.STRONGKIDS, **_映射(筛查工具.STRONGKIDS, dict(
        clinical=clinical, high_risk_disease=high_risk_disease, intake=intake, growth=growth)))
    _打印(结果, json_mode)


if __name__ == "__main__":
    app()
