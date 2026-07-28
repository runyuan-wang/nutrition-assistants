"""营养风险筛查计算器 — 数据模型 (Pydantic v2)

所有字段使用中文命名，与临床语境一致；范围约束由 Pydantic 兜底，
业务级"红线"由 validators/validator.py 处理。
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class 筛查工具(str, Enum):
    NRS2002 = "NRS-2002"       # 住院成人（ESPEN / 中国住院患者首选）
    MUST = "MUST"              # 通用（英国 BAPEN）
    MNA_SF = "MNA-SF"          # 老年（≥65 岁）精简版
    STRONGKIDS = "STRONGkids"  # 儿童（儿科）


class 风险等级(str, Enum):
    无风险 = "无风险"
    低危 = "低危"
    中危 = "中危"
    高危 = "高危"


# ---------------------------------------------------------------------------
# 各量表输入模型
# ---------------------------------------------------------------------------

class NRS2002输入(BaseModel):
    bmi: float | None = Field(default=None, description="体质指数 kg/m²（可选）")
    近三月体重下降百分比: float | None = Field(default=None, ge=0, le=100, description="近 X 月体重下降百分比")
    体重下降观察月数: int | None = Field(default=None, ge=1, le=24, description="体重下降观察月数")
    近一周进食量占正常百分比: int | None = Field(default=None, ge=0, le=100, description="近一周进食量占正常的百分比")
    疾病严重程度评分: int = Field(..., ge=0, le=3, description="0 正常 / 1 轻度慢性 / 2 中度如大手术·卒中·重症肺炎 / 3 重度如 ICU·移植")
    年龄: int = Field(..., ge=0, le=120, description="年龄，≥70 自动 +1")


class MUST输入(BaseModel):
    bmi: float = Field(..., gt=0, le=100, description="体质指数 kg/m²")
    近3_6月体重下降百分比: float | None = Field(default=None, ge=0, le=100, description="近 3–6 月体重下降百分比")
    急性疾病无进食超过5天: bool = Field(default=False, description="急性疾病致 >5 天无营养摄入")


class MNA_SF输入(BaseModel):
    食量下降: int = Field(..., ge=0, le=2, description="0 无/良好 / 1 适中 / 2 严重")
    近三月体重下降: int = Field(..., ge=0, le=3, description="0 无 / 1 不知 / 2 1–3kg / 3 >3kg")
    活动能力: int = Field(..., ge=0, le=2, description="0 外出 / 1 室内 / 2 卧床")
    应激或急性疾病: int = Field(..., ge=0, le=2, description="0 无 / 1 有（近 3 月应激或急性病）")
    神经心理问题: int = Field(..., ge=0, le=2, description="0 无 / 1 有（痴呆/抑郁等）")
    bmi: float | None = Field(default=None, gt=0, le=100, description="体质指数 kg/m²")
    小腿围_cm: float | None = Field(default=None, gt=0, le=80, description="小腿围 cm（≥31 计 0 分；BMI 缺失时代替）")


class STRONGkids输入(BaseModel):
    主观临床评估: int = Field(..., ge=0, le=2, description="0 良好 / 2 可疑营养不良")
    高危疾病: int = Field(..., ge=0, le=2, description="0 无 / 2 有（肿瘤/心肺/消化/肾/神经/代谢病等）")
    营养摄入下降: int = Field(..., ge=0, le=2, description="0 无 / 1 减少 / 2 严重不足")
    体重下降或生长迟缓: int = Field(..., ge=0, le=2, description="0 无 / 1 有 / 2 明显")


# ---------------------------------------------------------------------------
# 统一结果模型
# ---------------------------------------------------------------------------

class 筛查结果(BaseModel):
    工具: 筛查工具
    总分: float | None = Field(default=None, description="量表总分（部分量表无单一总分则用 None）")
    维度分: dict = Field(default_factory=dict, description="各维度得分明细")
    风险等级: 风险等级
    风险说明: str = ""
    建议: str = ""
    免责声明: str = (
        "本结果仅为营养风险筛查，不能替代临床营养诊断与医师面诊；"
        "阳性结果需由临床营养师/医师结合综合评估确认。"
    )
