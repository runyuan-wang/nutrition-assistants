"""提供者抽象接口 —— 中文版"""

from abc import ABC, abstractmethod
from typing import List
from src.schemas.lesson import 生成请求, 课件页面, 引用来源, 证据声明


class 课程提供者(ABC):
    """课程生成提供者基类"""

    @abstractmethod
    def 生成课件页面(self, 请求: 生成请求) -> List[课件页面]:
        """生成课件页面列表"""
        ...

    @abstractmethod
    def 生成引用(self, 请求: 生成请求) -> List[引用来源]:
        """生成引用列表"""
        ...

    @abstractmethod
    def 生成证据声明(self, 请求: 生成请求) -> List[证据声明]:
        """生成证据声明列表"""
        ...

    @abstractmethod
    def 获取提供者名称(self) -> str:
        """返回提供者名称"""
        ...
