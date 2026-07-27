"""NCBI E-utilities 客户端 —— 中文适配版"""

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

import httpx

from src.pubmed.models import PubMed检索请求, PubMed文献记录, 证据摘要

PMID_RE = re.compile(r"^[1-9]\d*$")


class PubMedError(Exception):
    """PubMed 检索安全失败"""


@dataclass
class 检索结果:
    """PubMed 检索产物的容器"""
    查询: PubMed检索请求
    原始搜索响应: dict
    原始提取响应: str
    文献列表: List[PubMed文献记录] = field(default_factory=list)
    证据摘要列表: List[证据摘要] = field(default_factory=list)


class PubMedClient:
    """NCBI E-utilities 同步客户端"""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, timeout: float = 30.0, api_key: Optional[str] = None):
        self.timeout = timeout
        self.api_key = api_key or os.getenv("NCBI_API_KEY")
        self._user_agent = self._构建UserAgent()

    def _构建UserAgent(self) -> str:
        ua = "NutritionLessonGeneratorZH/0.1.0 (NCBI-E-utilities-client)"
        contact = os.getenv("NCBI_EMAIL", "").strip()
        if contact:
            ua += f"; mailto:{contact}"
        return ua

    def _构建查询语句(self, 主题: str, 日期范围: tuple) -> str:
        """将中文主题转换为 PubMed 查询语句"""
        # 中英文双语检索策略
        中文关键词 = _提取中文关键词(主题)
        英文查询 = _转换为英文查询(主题)

        # 构建复合查询
        parts = [f'"{英文查询}"[Title/Abstract]']
        if 中文关键词:
            # 中文关键词也尝试在 title/abstract 中匹配
            for kw in 中文关键词:
                parts.append(f'"{kw}"[Title/Abstract]')

        # 限定 review, clinical trial, meta-analysis
        parts.append('(english[Language] OR chinese[Language])')

        query = " AND ".join(parts)

        # 日期范围
        start, end = 日期范围
        if start:
            query += f" AND (\"{start}\"[Date - Publication] : \"{end or '3000'}\"[Date - Publication])"

        return query

    def 搜索(self, 主题: str, max_results: int = 10, 日期范围: tuple = (None, None)) -> 检索结果:
        """执行 PubMed 搜索"""
        import secrets  # re-import here to avoid top-level import issues
        query_str = self._构建查询语句(主题, 日期范围)

        # 保存查询信息
        查询 = PubMed检索请求(
            主题=主题,
            最终查询语句=query_str,
            日期范围=日期范围,
            请求数量=max_results,
        )

        # ESearch
        params = {
            "db": "pubmed",
            "term": query_str,
            "retmax": str(max_results),
            "retmode": "json",
            "sort": "relevance",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        headers = {"User-Agent": self._user_agent}
        client = httpx.Client(timeout=self.timeout)

        # 注意 NCBI 速率限制：无 API key 时每秒最多 3 次请求
        if not self.api_key:
            time.sleep(0.4)

        try:
            resp = client.get(f"{self.BASE_URL}/esearch.fcgi", params=params, headers=headers)
            resp.raise_for_status()
            搜索结果 = resp.json()
        except httpx.HTTPError as e:
            # 自动降级：如果 PubMed 检索失败，返回空结果而非崩溃
            print(f"⚠️ PubMed 检索失败: {e}，返回空结果")
            return 检索结果(
                查询=查询,
                原始搜索响应={},
                原始提取响应="",
                文献列表=[],
                证据摘要列表=[],
            )

        id_list = 搜索结果.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            print("ℹ️ PubMed 检索无结果")
            return 检索结果(
                查询=查询,
                原始搜索响应=搜索结果,
                原始提取响应="",
                文献列表=[],
                证据摘要列表=[],
            )

        # EFetch —— 获取详细信息
        if not self.api_key:
            time.sleep(0.4)

        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml",
        }
        if self.api_key:
            fetch_params["api_key"] = self.api_key

        try:
            fetch_resp = client.get(f"{self.BASE_URL}/efetch.fcgi", params=fetch_params, headers=headers)
            fetch_resp.raise_for_status()
            xml_text = fetch_resp.text
        except httpx.HTTPError as e:
            print(f"⚠️ EFetch 失败: {e}，返回已有搜索结果")
            return 检索结果(
                查询=查询,
                原始搜索响应=搜索结果,
                原始提取响应="",
                文献列表=[],
                证据摘要列表=[],
            )

        # 解析 XML → 文献记录
        文献列表 = _解析EFetchXML(xml_text)

        # 生成证据摘要
        摘要列表 = []
        for 文献 in 文献列表:
            摘要列表.append(_生成证据摘要(文献, 主题))

        return 检索结果(
            查询=查询,
            原始搜索响应=搜索结果,
            原始提取响应=xml_text,
            文献列表=文献列表,
            证据摘要列表=摘要列表,
        )


def _提取中文关键词(主题: str) -> List[str]:
    """从中文主题中提取关键词"""
    import re as _re
    # 简单分词：取2-4字的中文词组
    chinese_chars = _re.findall(r'[\u4e00-\u9fff]{2,4}', 主题)
    return chinese_chars


def _转换为英文查询(主题: str) -> str:
    """将中文主题转换为英文 PubMed 查询关键词"""
    # 常见营养学术语映射
    翻译表 = {
        "膳食纤维": "dietary fiber",
        "肠道健康": "gut health",
        "肠道菌群": "gut microbiota",
        "益生菌": "probiotic",
        "维生素": "vitamin",
        "矿物质": "mineral",
        "蛋白质": "protein",
        "脂肪": "dietary fat",
        "碳水化合物": "carbohydrate",
        "糖尿病": "diabetes",
        "肥胖": "obesity",
        "高血压": "hypertension",
        "心血管": "cardiovascular",
        "骨质疏松": "osteoporosis",
        "痛风": "gout",
        "高尿酸": "hyperuricemia",
        "慢性肾病": "chronic kidney disease",
        "营养不良": "malnutrition",
        "儿童": "children",
        "青少年": "adolescent",
        "老年人": "elderly",
        "孕妇": "pregnancy",
        "母乳": "breastfeeding",
        "营养": "nutrition",
        "膳食": "diet",
        "食养": "dietary therapy",
        "体质": "constitution",
        "中医": "traditional Chinese medicine",
        "药膳": "medicinal food",
    }

    英文词列表 = []
    for 中文词, 英文词 in 翻译表.items():
        if 中文词 in 主题:
            英文词列表.append(英文词)

    if not 英文词列表:
        # 回退：直接用原主题（可能是英文）
        return 主题

    # 优先用英文词，同时尝试中文词的拼音
    return " OR ".join(f'"{w}"[Title/Abstract]' for w in 英文词列表[:5])


def _解析EFetchXML(xml_text: str) -> List[PubMed文献记录]:
    """解析 PubMed EFetch XML 响应"""
    import xml.etree.ElementTree as ET
    records = []

    try:
        root = ET.fromstring(xml_text)
        for article in root.findall(".//PubmedArticle"):
            medline = article.find(".//MedlineCitation")
            if medline is None:
                continue

            pmid_elem = medline.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else "unknown"
            if not PMID_RE.match(pmid):
                continue

            # 标题
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else None

            # 摘要
            abstract_parts = []
            for elem in article.findall(".//Abstract/AbstractText"):
                label = elem.get("Label", "")
                text = elem.text or ""
                abstract_parts.append(f"{label}: {text}" if label else text)
            摘要 = "\n".join(abstract_parts) if abstract_parts else None

            # 作者
            authors = []
            for author in article.findall(".//Author"):
                last = author.find("LastName")
                fore = author.find("ForeName")
                if last is not None:
                    name = last.text or ""
                    if fore is not None:
                        name = f"{fore.text or ''} {name}"
                    authors.append(name)
            作者 = ", ".join(authors[:6]) if authors else None

            # 期刊
            journal_elem = article.find(".//Journal/Title")
            期刊 = journal_elem.text if journal_elem is not None else None

            # 年份
            year_elem = article.find(".//PubDate/Year")
            年份 = int(year_elem.text) if year_elem is not None and year_elem.text else None

            # DOI
            for eid in article.findall(".//ELocationID"):
                if eid.get("EIdType") == "doi":
                    doi = eid.text
                    break
            else:
                doi = None

            # 出版类型
            出版类型 = [pt.text for pt in article.findall(".//PublicationType") if pt.text]

            # 语言
            lang_elem = medline.find(".//Language")
            语言 = lang_elem.text if lang_elem is not None else None

            records.append(PubMed文献记录(
                pmid=pmid,
                标题=title,
                摘要=摘要,
                作者=作者,
                期刊=期刊,
                出版年份=年份,
                出版类型=出版类型,
                doi=doi,
                语言=语言,
                来源URL=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            ))
    except ET.ParseError as e:
        print(f"⚠️ XML 解析失败: {e}")

    return records


def _生成证据摘要(文献: PubMed文献记录, 主题: str) -> 证据摘要:
    """从 PubMed 文献生成中文证据摘要"""
    # 判断研究类型
    研究类型 = "综述" if any("Review" in pt for pt in (文献.出版类型 or [])) else "研究"
    if any("Meta-Analysis" in pt for pt in (文献.出版类型 or [])):
        研究类型 = "Meta分析"
    elif any("Randomized Controlled Trial" in pt for pt in (文献.出版类型 or [])):
        研究类型 = "RCT"

    # 相关性判断（简单的关键词匹配）
    相关度 = 0
    summary_text = f"{文献.标题 or ''} {文献.摘要 or ''}".lower()
    for keyword in _提取中文关键词(主题):
        if keyword.lower() in summary_text:
            相关度 += 1

    return 证据摘要(
        证据ID=文献.引用ID,
        pmid=文献.pmid,
        研究类型=研究类型,
        关键发现=文献.标题 or "标题不可用",
        局限性="仅基于摘要分析，未进行全文评审",
        中文翻译摘要=f"[PMID:{文献.pmid}] {文献.标题}",
        可用于公众教育=相关度 > 0,
        与主题相关性="高度相关" if 相关度 > 1 else "一般相关" if 相关度 > 0 else "待确认",
    )
