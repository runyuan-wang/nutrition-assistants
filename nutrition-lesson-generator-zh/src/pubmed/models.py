"""PubMed 证据检索模型 —— 中文适配版"""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, timezone
from typing import Tuple, Optional, List
import re


_DATE_RE = re.compile(r"^\d{4}(?:/\d{2}/\d{2})?$")


def _date_sort_value(value: str, *, end: bool) -> datetime:
    if not _DATE_RE.fullmatch(value):
        raise ValueError("日期格式必须为 YYYY 或 YYYY/MM/DD")
    if len(value) == 4:
        suffix = "/12/31" if end else "/01/01"
        value = f"{value}{suffix}"
    try:
        return datetime.strptime(value, "%Y/%m/%d")
    except ValueError as exc:
        raise ValueError("日期必须是真实的日历日期") from exc


class PubMed检索请求(BaseModel):
    """PubMed 检索请求"""
    主题: str = Field(..., min_length=1)
    最终查询语句: str = Field(..., min_length=1)
    日期范围: Tuple[Optional[str], Optional[str]] = Field(
        default=(None, None),
        description="可选的 (起始日期, 结束日期) 过滤"
    )
    请求数量: int = Field(..., ge=1, le=200)
    检索时间: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("主题", "最终查询语句")
    @classmethod
    def _去除空白(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("值不能为空")
        return value

    @field_validator("日期范围")
    @classmethod
    def _验证日期范围(cls, value) -> Tuple[Optional[str], Optional[str]]:
        start, end = value
        start = start.strip() if start else None
        end = end.strip() if end else None
        sv = _date_sort_value(start, end=False) if start else None
        ev = _date_sort_value(end, end=True) if end else None
        if sv and ev and sv > ev:
            raise ValueError("起始日期不能晚于结束日期")
        return start, end

    model_config = {"extra": "forbid"}


class PubMed文献记录(BaseModel):
    """标准化 PubMed 文献记录"""
    pmid: str = Field(..., pattern=r"^[1-9]\d*$")
    标题: Optional[str] = None
    摘要: Optional[str] = None
    作者: Optional[str] = None
    期刊: Optional[str] = None
    出版年份: Optional[int] = Field(None, ge=1800, le=2100)
    出版类型: List[str] = Field(default_factory=list)
    doi: Optional[str] = None
    MeSH词汇: List[str] = Field(default_factory=list)
    语言: Optional[str] = None
    来源URL: str = Field(..., min_length=1)
    检索时间: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("标题", "摘要", "作者", "期刊", "doi", "语言")
    @classmethod
    def _空白转None(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("doi")
    @classmethod
    def _验证doi(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.startswith("10."):
            raise ValueError("DOI 必须以 '10.' 开头")
        return value

    @property
    def 引用ID(self) -> str:
        return f"PMID_{self.pmid}"

    model_config = {"extra": "forbid"}


class 证据摘要(BaseModel):
    """保守的结构化证据视图"""
    证据ID: str = Field(..., min_length=1)
    pmid: str = Field(..., pattern=r"^[1-9]\d*$")
    研究类型: str = Field(default="未报告")
    研究人群: str = Field(default="未报告")
    干预或暴露: str = Field(default="未报告")
    对照组: str = Field(default="未报告")
    结局指标: str = Field(default="未报告")
    关键发现: str = Field(default="未报告")
    局限性: str = Field(default="未报告")
    证据等级: str = Field(default="未报告")
    与主题相关性: str = Field(default="未报告")
    可用于公众教育: bool = Field(default=False)
    中文翻译摘要: Optional[str] = Field(default=None, description="对英文摘要的中文翻译")

    @model_validator(mode="after")
    def _证据ID匹配PMID(self):
        expected = f"PMID_{self.pmid}"
        if self.证据ID != expected:
            raise ValueError(f"证据ID '{self.证据ID}' 必须等于 '{expected}'")
        return self

    model_config = {"extra": "forbid"}
