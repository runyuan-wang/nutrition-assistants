"""中文营养课程规范化 Pydantic 模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class 证据等级(str, Enum):
    """证据等级（中文）"""
    A_级 = "A级"        # 系统评价/Meta分析
    B_级 = "B级"        # RCT
    C_级 = "C级"        # 观察性研究
    D_级 = "D级"        # 专家共识/指南
    E_级 = "E级"        # 权威机构建议


class 引用来源(BaseModel):
    """单条引用"""
    编号: int
    作者: str
    标题: str
    期刊: Optional[str] = None
    年份: Optional[int] = None
    PMID: Optional[str] = None
    DOI: Optional[str] = None
    证据等级: 证据等级
    摘要: Optional[str] = None
    局限性: Optional[str] = None


class 证据声明(BaseModel):
    """一条循证声明"""
    声明ID: str
    声明内容: str
    证据摘要: str
    解释说明: str
    实践建议: str
    引用: List[int]  # 引用编号列表
    适用人群: Optional[str] = None
    局限说明: Optional[str] = None


class 课件页面(BaseModel):
    """单页课件"""
    页码: int
    标题: str
    正文: str  # Markdown 格式
    讲稿: str
    引用编号: List[int] = []
    页面类型: str  # 封面/目录/内容/误区/总结/参考文献
    图片提示: Optional[str] = None  # 建议配图描述


class 课程规范(BaseModel):
    """完整课程规范"""
    # 基本信息
    主题: str
    副标题: Optional[str] = None
    目标听众: str
    语言: str = "zh"
    课时分钟: int

    # 课程结构
    学习目标: List[str]
    关键词: List[str]
    页面列表: List[课件页面]

    # 证据体系
    引用列表: List[引用来源]
    证据声明列表: List[证据声明]

    # 元数据
    作者: str = "营养课程生成器"
    生成日期: str
    证据模式: str  # mock / pubmed
    版本: str = "0.1.0"


class 生成请求(BaseModel):
    """课程生成请求"""
    主题: str
    目标听众: str = "普通成年人"
    语言: str = "zh"
    课时分钟: int = 30
    输出目录: str = "output"
    证据来源: str = "mock"  # mock / pubmed
    max_results: int = 10
