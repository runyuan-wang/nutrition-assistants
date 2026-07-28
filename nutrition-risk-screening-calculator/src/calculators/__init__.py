# calculators 包 — 注册四种量表
from __future__ import annotations

from .base import REGISTRY, 注册, 筛查计算器, 调度
from . import nrs2002, must, mna_sf, strongkids
from ..schemas.screening import (
    筛查工具, NRS2002输入, MUST输入, MNA_SF输入, STRONGkids输入,
)

注册(筛查工具.NRS2002, NRS2002输入, nrs2002.计算)
注册(筛查工具.MUST, MUST输入, must.计算)
注册(筛查工具.MNA_SF, MNA_SF输入, mna_sf.计算)
注册(筛查工具.STRONGKIDS, STRONGkids输入, strongkids.计算)

__all__ = ["REGISTRY", "注册", "调度", "筛查计算器"]
