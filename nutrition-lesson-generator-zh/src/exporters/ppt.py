"""中文 PowerPoint 导出器 —— 基于 python-pptx

设计要点：
- 中国传统配色：千里江山图风格（青蓝 / 苍绿 / 赭金）
- 内容页支持 Markdown 项目符号渲染、证据等级徽章、中国 DRIs 参考框
- 支持页面类型：封面 / 目录 / 内容 / 误区 / 总结 / 参考文献 / 中医食养
"""

import json
import re
from pathlib import Path
from typing import List, Optional

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

from src.schemas.lesson import 课件页面, 课程规范, 证据等级


class 中文PPT导出器:
    """中文 PowerPoint 导出器"""

    # 中国传统配色 —— 千里江山图风格
    主题色_青 = RGBColor(0x2E, 0x75, 0xB6)      # 主色：青蓝色
    主题色_绿 = RGBColor(0x5B, 0x8C, 0x5A)      # 辅助色：苍绿色
    主题色_金 = RGBColor(0xE8, 0xA8, 0x3E)      # 强调色：赭金色
    主题色_灰 = RGBColor(0x4A, 0x4A, 0x4A)      # 正文深灰
    主题色_浅灰 = RGBColor(0xF5, 0xF5, 0xF0)    # 背景浅米
    主题色_白 = RGBColor(0xFF, 0xFF, 0xFF)
    主题色_注 = RGBColor(0x70, 0x70, 0x70)      # 注释灰

    # 证据等级 → 配色
    等级配色 = {
        "A级": RGBColor(0xE8, 0xA8, 0x3E),   # 金
        "B级": RGBColor(0x5B, 0x8C, 0x5A),   # 绿
        "C级": RGBColor(0x9C, 0x9C, 0x9C),   # 灰
        "D级": RGBColor(0x2E, 0x75, 0xB6),   # 青
        "E级": RGBColor(0x2E, 0x75, 0xB6),   # 青
    }

    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)   # 16:9 宽屏
        self.prs.slide_height = Inches(7.5)
        self._dris = self._加载DRIs()

    # ---------- DRIs 数据 ----------
    def _加载DRIs(self) -> dict:
        """加载中国 DRIs 精选数据（china_dris.json）"""
        路径 = Path(__file__).resolve().parent.parent.parent / "china_dris.json"
        try:
            if 路径.exists():
                return json.loads(路径.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    # 营养素中文名 → 参考值展示（来自 china_dris.json，缺失时回退硬编码）
    _DRI_展示 = {
        "膳食纤维": "25–30 g/d（AI）",
        "蛋白质": "男 65 / 女 55 g/d（RNI）",
        "钙": "800 mg/d（RNI，50岁以上1000）",
        "铁": "男 12 / 女 18 mg/d（RNI）",
        "锌": "男 12.5 / 女 7.5 mg/d",
        "硒": "60 μg/d",
        "镁": "330 mg/d",
        "钾": "2000 mg/d（AI）",
        "钠": "<1500 mg/d（AI），食盐<5g",
        "维生素A": "男 800 / 女 700 μgRAE/d",
        "维生素D": "10 μg/d（65岁以上15）",
        "维生素C": "100 mg/d",
        "维生素E": "14 mgα-TE/d",
        "维生素K": "80 μg/d",
        "维生素B1": "男 1.4 / 女 1.2 mg/d",
        "维生素B2": "男 1.4 / 女 1.2 mg/d",
        "维生素B6": "1.4 mg/d",
        "维生素B12": "2.4 μg/d",
        "叶酸": "400 μgDFE/d",
        "烟酸": "男 15 / 女 12 mgNE/d",
        "饮水": "1500–1700 mL/d",
    }

    def _提取DRI提示(self, 文本: str) -> List[str]:
        """从课件文本中提取命中的 DRIs 参考值"""
        命中 = []
        for 名称, 值 in self._DRI_展示.items():
            if 名称 in 文本:
                命中.append(f"{名称} {值}")
        return 命中[:4]   # 最多展示 4 条，避免拥挤

    # ---------- 基础绘制 ----------
    def _设置幻灯片背景(self, slide, 颜色):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = 颜色

    def _添加文本框(self, slide, left, top, width, height, text, font_size=18,
                    bold=False, color=None, alignment=PP_ALIGN.LEFT, font_name="微软雅黑",
                    italic=False):
        txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.name = font_name
        p.font.bold = bold
        p.font.italic = italic
        p.font.color.rgb = color or self.主题色_灰
        p.alignment = alignment
        return tf

    @staticmethod
    def _去标记(text: str) -> str:
        """去除 Markdown 粗体/标题符号，保留 emoji"""
        return text.replace("**", "").replace("`", "")

    def _渲染正文(self, slide, left, top, width, height, md_text: str,
                  base_size=15, 标题色=None):
        """将 Markdown 正文渲染为带项目符号的文本框"""
        tf = slide.shapes.add_textbox(
            Inches(left), Inches(top), Inches(width), Inches(height)
        ).text_frame
        tf.word_wrap = True
        first = True
        for raw in md_text.split("\n"):
            line = raw.rstrip()
            if not line.strip():
                continue
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            if line.startswith("## "):
                p.text = self._去标记(line[3:].strip())
                p.font.size = Pt(20); p.font.bold = True
                p.font.color.rgb = 标题色 or self.主题色_青
                p.space_before = Pt(6); p.space_after = Pt(4)
            elif line.startswith("# "):
                p.text = self._去标记(line[2:].strip())
                p.font.size = Pt(22); p.font.bold = True
                p.font.color.rgb = 标题色 or self.主题色_青
                p.space_after = Pt(4)
            elif line.startswith("> "):
                p.text = self._去标记(line[2:].strip())
                p.font.size = Pt(13); p.font.italic = True
                p.font.color.rgb = self.主题色_注
                p.space_after = Pt(4)
            elif line.startswith("- ") or line.startswith("* "):
                p.text = "• " + self._去标记(line[2:].strip())
                p.font.size = Pt(base_size); p.font.color.rgb = self.主题色_灰
                p.space_after = Pt(4)
            elif re.match(r"^\d+\.\s", line):
                p.text = self._去标记(line)
                p.font.size = Pt(base_size); p.font.color.rgb = self.主题色_灰
                p.space_after = Pt(4)
            elif line.startswith("|"):
                p.text = line.replace("|", " ").strip()
                p.font.size = Pt(12); p.font.color.rgb = self.主题色_注
                p.space_after = Pt(2)
            else:
                p.text = self._去标记(line)
                p.font.size = Pt(base_size); p.font.color.rgb = self.主题色_灰
                p.space_after = Pt(4)
        return tf

    def _添加分隔线(self, slide, top, color, left=0.5, width=12.0):
        line = slide.shapes.add_shape(1, Inches(left), Inches(top), Inches(width), Inches(0.03))
        line.fill.solid()
        line.fill.fore_color.rgb = color
        line.line.fill.background()
        return line

    def _添加证据徽章(self, slide, 页面: 课件页面, 课程: 课程规范):
        """在内容页右上角渲染证据等级徽章"""
        if not 页面.引用编号:
            return
        等级集 = set()
        for rid in 页面.引用编号:
            for ref in 课程.引用列表:
                if ref.编号 == rid:
                    等级集.add(ref.证据等级.value)
                    break
        if not 等级集:
            return
        x = 10.3
        for 等级 in sorted(等级集):
            color = self.等级配色.get(等级, self.主题色_灰)
            box = slide.shapes.add_textbox(Inches(x), Inches(0.35), Inches(2.5), Inches(0.4))
            tf = box.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = f"证据等级 {等级}"
            p.font.size = Pt(11); p.font.bold = True
            p.font.color.rgb = color
            p.alignment = PP_ALIGN.RIGHT
            x -= 2.6

    def _添加DRI提示框(self, slide, 提示列表: List[str]):
        """页面底部渲染中国 DRIs 参考框"""
        if not 提示列表:
            return
        top = 6.05
        height = 0.9
        # 浅色底框
        box = slide.shapes.add_shape(1, Inches(0.5), Inches(top), Inches(12.3), Inches(height))
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(0xEC, 0xF2, 0xF7)
        box.line.color.rgb = self.主题色_青
        box.line.width = Pt(0.75)
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.15); tf.margin_top = Inches(0.05)
        p = tf.paragraphs[0]
        p.text = "📊 中国 DRIs 参考：" + "　|　".join(提示列表)
        p.font.size = Pt(11); p.font.color.rgb = self.主题色_青
        p.font.bold = True

    def _添加页脚(self, slide, 页码: int, 总页: int = 0):
        self._添加文本框(
            slide, 0.5, 7.05, 6, 0.3,
            f"第{页码}页" + (f" / 共{总页}页" if 总页 else ""),
            font_size=10, color=RGBColor(0x99, 0x99, 0x99),
        )

    # ---------- 各页面 ----------
    def _创建封面页(self, slide, 页面: 课件页面):
        self._设置幻灯片背景(slide, self.主题色_青)
        # 解析副标题 / 受众 / 时长
        副标题 = "基于循证营养学的科普课程"
        受众 = ""
        时长 = ""
        for ln in 页面.正文.split("\n"):
            if "副标题" in ln:
                副标题 = ln.split("：", 1)[-1].strip().strip("*")
            if "授课对象" in ln:
                受众 = ln.split("：", 1)[-1].strip()
            if ln.strip().startswith("时长"):
                时长 = ln.split("：", 1)[-1].strip()
        self._添加文本框(slide, 1, 1.6, 11.3, 1.6, 页面.标题,
                         font_size=40, bold=True, color=self.主题色_白,
                         alignment=PP_ALIGN.CENTER)
        self._添加文本框(slide, 1, 3.4, 11.3, 0.8, 副标题,
                         font_size=20, color=RGBColor(0xE0, 0xE8, 0xF0),
                         alignment=PP_ALIGN.CENTER)
        if 受众 or 时长:
            info = f"授课对象：{受众}" + (f"　·　时长：{时长}" if 时长 else "")
            self._添加文本框(slide, 1, 4.5, 11.3, 0.5, info,
                             font_size=14, color=RGBColor(0xC0, 0xD0, 0xE0),
                             alignment=PP_ALIGN.CENTER)
        self._添加文本框(slide, 1, 6.4, 11.3, 0.5,
                         "营养课程生成器 · 中文版 · 千里江山图配色",
                         font_size=11, color=RGBColor(0xB0, 0xC0, 0xD0),
                         alignment=PP_ALIGN.CENTER)

    def _创建目录页(self, slide, 页面: 课件页面):
        self._设置幻灯片背景(slide, self.主题色_浅灰)
        self._添加文本框(slide, 0.6, 0.4, 12, 0.8, 页面.标题,
                         font_size=30, bold=True, color=self.主题色_青)
        self._添加分隔线(slide, 1.25, self.主题色_青)
        # 目录项
        items = []
        for ln in 页面.正文.split("\n"):
            ln = ln.strip()
            m = re.match(r"^(\d+)\.\s+(.*)$", ln)
            if m:
                items.append(f"{m.group(1)}. {self._去标记(m.group(2))}")
            elif ln.startswith("- "):
                items.append("• " + self._去标记(ln[2:]))
        tf = slide.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.5), Inches(5.0)).text_frame
        tf.word_wrap = True
        first = True
        for it in items:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.text = it
            p.font.size = Pt(18); p.font.color.rgb = self.主题色_灰
            p.space_after = Pt(10)
        self._添加页脚(slide, 页面.页码)

    def _创建内容页(self, slide, 页面: 课件页面, 课程: 课程规范):
        self._设置幻灯片背景(slide, self.主题色_浅灰)
        self._添加文本框(slide, 0.5, 0.3, 9.5, 0.8, 页面.标题,
                         font_size=28, bold=True, color=self.主题色_青)
        self._添加分隔线(slide, 1.15, self.主题色_青)
        self._添加证据徽章(slide, 页面, 课程)
        # 正文（留出底部 DRI 框空间）
        self._渲染正文(slide, 0.7, 1.35, 11.8, 4.4, 页面.正文)
        # DRIs 参考框
        dri = self._提取DRI提示(页面.标题 + " " + 页面.正文 + " " + 页面.讲稿)
        self._添加DRI提示框(slide, dri)
        self._添加页脚(slide, 页面.页码, len(课程.页面列表))

    def _创建误区页(self, slide, 页面: 课件页面, 课程: 课程规范):
        self._设置幻灯片背景(slide, self.主题色_浅灰)
        self._添加文本框(slide, 0.5, 0.3, 12, 0.8, 页面.标题,
                         font_size=28, bold=True, color=self.主题色_金)
        self._添加分隔线(slide, 1.15, self.主题色_金)
        self._渲染正文(slide, 0.7, 1.35, 11.8, 5.0, 页面.正文, base_size=16)
        self._添加页脚(slide, 页面.页码, len(课程.页面列表))

    def _创建中医食养页(self, slide, 页面: 课件页面, 课程: 课程规范):
        """中医食养专题页 —— 赭金强调色"""
        self._设置幻灯片背景(slide, RGBColor(0xFB, 0xF6, 0xEC))
        self._添加文本框(slide, 0.5, 0.3, 12, 0.8, "🍃 " + 页面.标题,
                         font_size=28, bold=True, color=self.主题色_金)
        self._添加分隔线(slide, 1.15, self.主题色_金)
        self._添加证据徽章(slide, 页面, 课程)
        self._渲染正文(slide, 0.7, 1.35, 11.8, 5.0, 页面.正文,
                       base_size=15, 标题色=self.主题色_金)
        self._添加页脚(slide, 页面.页码, len(课程.页面列表))

    def _创建总结页(self, slide, 页面: 课件页面, 课程: 课程规范):
        self._设置幻灯片背景(slide, self.主题色_浅灰)
        self._添加文本框(slide, 0.5, 0.3, 12, 0.8, 页面.标题,
                         font_size=28, bold=True, color=self.主题色_金)
        self._添加分隔线(slide, 1.15, self.主题色_金)
        self._渲染正文(slide, 0.7, 1.35, 11.8, 5.0, 页面.正文, base_size=16)
        self._添加页脚(slide, 页面.页码, len(课程.页面列表))

    def _创建参考文献页(self, slide, 页面: 课件页面, 课程: 课程规范):
        self._设置幻灯片背景(slide, self.主题色_浅灰)
        self._添加文本框(slide, 0.5, 0.3, 12, 0.8, 页面.标题,
                         font_size=28, bold=True, color=self.主题色_青)
        self._添加分隔线(slide, 1.15, self.主题色_青)
        # 引用列表原文（已在 正文 中含完整列表）
        self._渲染正文(slide, 0.7, 1.35, 11.8, 5.0, 页面.正文, base_size=13)
        self._添加页脚(slide, 页面.页码, len(课程.页面列表))

    def 导出(self, 课程: 课程规范, 输出路径: str = "营养课程.pptx"):
        """导出完整的 PPTX 文件"""
        for 页面 in 课程.页面列表:
            slide_layout = self.prs.slide_layouts[6]   # 空白布局
            slide = self.prs.slides.add_slide(slide_layout)

            t = 页面.页面类型
            if t == "封面":
                self._创建封面页(slide, 页面)
            elif t == "目录":
                self._创建目录页(slide, 页面)
            elif t == "误区":
                self._创建误区页(slide, 页面, 课程)
            elif t == "中医食养":
                self._创建中医食养页(slide, 页面, 课程)
            elif t in ("总结", "参考文献"):
                if t == "总结":
                    self._创建总结页(slide, 页面, 课程)
                else:
                    self._创建参考文献页(slide, 页面, 课程)
            else:
                self._创建内容页(slide, 页面, 课程)

        self.prs.save(输出路径)
        return 输出路径
