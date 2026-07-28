"""计算器抽象基类与注册表。

所有具体量表在 calculators/ 下实现 `计算(输入) -> 筛查结果`，
并通过 REGISTRY 注册，供 CLI 与批量接口统一调度。
"""
from __future__ import annotations

from typing import Callable, Type

from ..schemas.screening import 筛查工具, 筛查结果

# 注册项：(输入模型, 计算函数)
RegistryEntry = tuple[Type, Callable]


class 筛查计算器:
    """统一接口占位（具体逻辑在各量表模块）。"""


REGISTRY: dict[筛查工具, RegistryEntry] = {}


def 注册(工具: 筛查工具, 输入模型: Type, 计算函数: Callable) -> None:
    REGISTRY[工具] = (输入模型, 计算函数)


def 调度(工具: 筛查工具, **kwargs) -> 筛查结果:
    if 工具 not in REGISTRY:
        raise ValueError(f"未注册的量表：{工具}")
    输入模型, 计算函数 = REGISTRY[工具]
    输入 = 输入模型(**kwargs)
    return 计算函数(输入)
