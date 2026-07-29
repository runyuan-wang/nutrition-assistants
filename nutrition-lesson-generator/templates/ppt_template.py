"""Presentation theme and slide layout helpers for python-pptx.

This module keeps styling concerns separate from the exporter.  It provides a
restrained, modern 16:9 theme with simple geometric cues and a clear hierarchy
for nutrition-education decks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.slide import Slide
from pptx.util import Inches, Pt


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
SLIDE_WIDTH = Inches(13.333333)
SLIDE_HEIGHT = Inches(7.5)
MARGIN = Inches(0.75)
CONTENT_WIDTH = SLIDE_WIDTH - 2 * MARGIN

TITLE_TOP = Inches(0.55)
TITLE_HEIGHT = Inches(0.9)
SECTION_LABEL_TOP = Inches(0.22)

BODY_TOP = Inches(1.7)
BODY_HEIGHT = Inches(5.0)

FOOTER_HEIGHT = Inches(0.4)
FOOTER_TOP = SLIDE_HEIGHT - FOOTER_HEIGHT - Inches(0.1)
FOOTER_TEXT_WIDTH = CONTENT_WIDTH - Inches(0.7)
SLIDE_NUM_LEFT = SLIDE_WIDTH - MARGIN - Inches(0.6)


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
DARK_NAVY = RGBColor(0x1A, 0x3C, 0x5A)          # headings
NUTRITION_GREEN = RGBColor(0x2E, 0xA3, 0x6B)     # primary accent
SOFT_CORAL = RGBColor(0xE8, 0x7A, 0x5A)          # secondary accent
DARK_TEXT = RGBColor(0x33, 0x33, 0x33)           # body
LIGHT_SURFACE = RGBColor(0xF8, 0xFA, 0xFB)       # very light gray
CARD_FILL = RGBColor(0xF0, 0xF4, 0xF3)           # soft card background
MUTED_TEXT = RGBColor(0x66, 0x76, 0x82)          # footer / secondary
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


@dataclass(frozen=True)
class PresentationTheme:
    """Color, font, and size theme for the deck."""

    heading_color: RGBColor = DARK_NAVY
    text_color: RGBColor = DARK_TEXT
    primary_accent: RGBColor = NUTRITION_GREEN
    secondary_accent: RGBColor = SOFT_CORAL
    background_color: RGBColor = LIGHT_SURFACE
    card_fill: RGBColor = CARD_FILL
    muted_color: RGBColor = MUTED_TEXT
    font_name: str = "Arial"
    title_font_size: int = 30
    subtitle_font_size: int = 18
    body_font_size: int = 22
    secondary_font_size: int = 16
    footer_font_size: int = 10
    badge_font_size: int = 11


DEFAULT_THEME = PresentationTheme()


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def _set_slide_background(slide: Slide, color: RGBColor) -> None:
    """Apply a solid background color to a slide."""
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_textbox(
    slide: Slide,
    left,
    top,
    width,
    height,
    text: str,
    font_size: int,
    color: RGBColor,
    font_name: str = DEFAULT_THEME.font_name,
    bold: bool = False,
    italic: bool = False,
    align: PP_ALIGN = PP_ALIGN.LEFT,
):
    """Add a single-paragraph text box with explicit styling."""
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    font = p.font
    font.name = font_name
    font.size = Pt(font_size)
    font.color.rgb = color
    font.bold = bold
    font.italic = italic
    p.line_spacing = 1.15
    return box


def _add_bullet_box(
    slide: Slide,
    left,
    top,
    width,
    height,
    bullets: Sequence[str],
    theme: PresentationTheme,
    font_size: int | None = None,
    marker: str = "•",
):
    """Add a multi-paragraph bulleted text box."""
    size = font_size if font_size is not None else theme.body_font_size
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for idx, bullet in enumerate(bullets):
        p = tf.paragraphs[idx] if idx < len(tf.paragraphs) else tf.add_paragraph()
        p.text = f"{marker} {bullet}"
        p.level = 0
        p.alignment = PP_ALIGN.LEFT
        font = p.font
        font.name = theme.font_name
        font.size = Pt(size)
        font.color.rgb = theme.text_color
        p.space_after = Pt(size * 0.45)
        p.line_spacing = 1.25
    return box


def _add_accent_line(
    slide: Slide,
    left,
    top,
    width,
    color: RGBColor,
    thickness=Pt(2.5),
) -> None:
    """Add a horizontal line."""
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, left, top, width, thickness
    )
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()


def _add_left_bar(
    slide: Slide,
    top,
    height,
    color: RGBColor,
    bar_width=Inches(0.08),
) -> None:
    """Add a vertical accent bar flush with the left margin."""
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, MARGIN, top, bar_width, height
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()


def _add_rounded_card(
    slide: Slide,
    left,
    top,
    width,
    height,
    fill_color: RGBColor,
) -> None:
    """Add a subtle rounded-rectangle card behind content."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = fill_color
    card.line.color.rgb = fill_color
    card.line.width = Pt(0.5)


def _add_badge(
    slide: Slide,
    left,
    top,
    width,
    height,
    text: str,
    fill_color: RGBColor,
    text_color: RGBColor,
    theme: PresentationTheme,
    font_size: int | None = None,
) -> None:
    """Add a small rounded badge (e.g. 'Evidence note')."""
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    badge.fill.solid()
    badge.fill.fore_color.rgb = fill_color
    badge.line.fill.background()

    tf = badge.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = PP_ALIGN.LEFT
    font = p.font
    font.name = theme.font_name
    font.size = Pt(font_size if font_size is not None else theme.badge_font_size)
    font.color.rgb = text_color
    font.bold = True


def _add_footer_region(
    slide: Slide,
    footer: str,
    slide_number: int | None,
    theme: PresentationTheme,
) -> None:
    """Render footer text and slide number in a consistent bottom region."""
    if footer:
        footer_box = slide.shapes.add_textbox(
            MARGIN, FOOTER_TOP, FOOTER_TEXT_WIDTH, FOOTER_HEIGHT
        )
        tf = footer_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = footer
        p.alignment = PP_ALIGN.LEFT
        p.font.name = theme.font_name
        p.font.size = Pt(theme.footer_font_size)
        p.font.color.rgb = theme.muted_color

    if slide_number is not None:
        num_box = slide.shapes.add_textbox(
            SLIDE_NUM_LEFT, FOOTER_TOP, Inches(0.6), FOOTER_HEIGHT
        )
        tf = num_box.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.text = str(slide_number)
        p.alignment = PP_ALIGN.RIGHT
        p.font.name = theme.font_name
        p.font.size = Pt(theme.footer_font_size)
        p.font.color.rgb = theme.muted_color


def _add_section_label(
    slide: Slide,
    label: str,
    theme: PresentationTheme,
) -> None:
    """Small uppercase label above the slide title."""
    _add_textbox(
        slide,
        MARGIN,
        SECTION_LABEL_TOP,
        CONTENT_WIDTH,
        Inches(0.25),
        label.upper(),
        font_size=theme.footer_font_size + 1,
        color=theme.primary_accent,
        font_name=theme.font_name,
        bold=True,
        align=PP_ALIGN.LEFT,
    )


# ---------------------------------------------------------------------------
# Slide layouts
# ---------------------------------------------------------------------------
def apply_title_slide(
    slide: Slide,
    title: str,
    subtitle: str,
    theme: PresentationTheme = DEFAULT_THEME,
) -> None:
    """Style a title slide: bold heading, subtitle, and simple geometric cues."""
    _set_slide_background(slide, theme.background_color)

    # Clear any default placeholders so they do not show through.
    for shape in list(slide.shapes):
        if shape.has_text_frame and shape.placeholder_format is not None:
            shape.text = ""

    # Decorative circle in the lower-right corner.
    circle = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        SLIDE_WIDTH - Inches(2.0),
        SLIDE_HEIGHT - Inches(2.0),
        Inches(1.25),
        Inches(1.25),
    )
    circle.fill.solid()
    circle.fill.fore_color.rgb = theme.card_fill
    circle.line.color.rgb = theme.card_fill

    title_left = MARGIN
    title_top = Inches(2.1)
    title_width = CONTENT_WIDTH
    title_height = Inches(1.4)

    _add_textbox(
        slide,
        title_left,
        title_top,
        title_width,
        title_height,
        title,
        font_size=theme.title_font_size,
        color=theme.heading_color,
        font_name=theme.font_name,
        bold=True,
        align=PP_ALIGN.LEFT,
    )

    _add_accent_line(
        slide,
        title_left,
        title_top + title_height - Inches(0.25),
        Inches(2.8),
        theme.primary_accent,
    )

    if subtitle:
        _add_textbox(
            slide,
            title_left,
            title_top + title_height + Inches(0.15),
            Inches(8.5),
            Inches(1.0),
            subtitle,
            font_size=theme.subtitle_font_size,
            color=theme.muted_color,
            font_name=theme.font_name,
            align=PP_ALIGN.LEFT,
        )


def apply_objectives_slide(
    slide: Slide,
    title: str,
    bullets: Sequence[str],
    footer: str,
    theme: PresentationTheme = DEFAULT_THEME,
    slide_number: int | None = None,
) -> None:
    """Style a learning-objectives slide with a soft card and numbered cues."""
    _set_slide_background(slide, theme.background_color)
    _add_section_label(slide, "Objectives", theme)

    # Title
    _add_textbox(
        slide,
        MARGIN,
        TITLE_TOP,
        CONTENT_WIDTH,
        TITLE_HEIGHT,
        title,
        font_size=theme.title_font_size,
        color=theme.heading_color,
        font_name=theme.font_name,
        bold=True,
    )

    _add_accent_line(
        slide,
        MARGIN,
        TITLE_TOP + TITLE_HEIGHT + Inches(0.05),
        Inches(1.5),
        theme.primary_accent,
    )

    # Card behind bullets
    card_top = BODY_TOP - Inches(0.15)
    card_height = BODY_HEIGHT + Inches(0.3)
    _add_rounded_card(
        slide,
        MARGIN,
        card_top,
        CONTENT_WIDTH,
        card_height,
        theme.card_fill,
    )

    _add_left_bar(
        slide,
        card_top + Inches(0.2),
        card_height - Inches(0.4),
        theme.primary_accent,
    )

    _add_bullet_box(
        slide,
        MARGIN + Inches(0.2),
        BODY_TOP,
        CONTENT_WIDTH - Inches(0.4),
        BODY_HEIGHT,
        bullets,
        theme,
    )

    _add_footer_region(slide, footer, slide_number, theme)


def apply_content_slide(
    slide: Slide,
    title: str,
    bullets: Sequence[str],
    footer: str,
    theme: PresentationTheme = DEFAULT_THEME,
    slide_number: int | None = None,
) -> None:
    """Style a standard content slide."""
    _set_slide_background(slide, theme.background_color)

    _add_textbox(
        slide,
        MARGIN,
        TITLE_TOP,
        CONTENT_WIDTH,
        TITLE_HEIGHT,
        title,
        font_size=theme.title_font_size,
        color=theme.heading_color,
        font_name=theme.font_name,
        bold=True,
    )

    _add_accent_line(
        slide,
        MARGIN,
        TITLE_TOP + TITLE_HEIGHT + Inches(0.05),
        CONTENT_WIDTH,
        theme.primary_accent,
    )

    _add_left_bar(
        slide,
        BODY_TOP + Inches(0.1),
        BODY_HEIGHT - Inches(0.2),
        theme.primary_accent,
    )

    _add_bullet_box(
        slide,
        MARGIN + Inches(0.18),
        BODY_TOP,
        CONTENT_WIDTH - Inches(0.18),
        BODY_HEIGHT,
        bullets,
        theme,
    )

    _add_footer_region(slide, footer, slide_number, theme)


def apply_evidence_slide(
    slide: Slide,
    title: str,
    bullets: Sequence[str],
    footer: str,
    evidence_strength: str,
    limitation: str,
    theme: PresentationTheme = DEFAULT_THEME,
    slide_number: int | None = None,
) -> None:
    """Style evidence content with a readable, metadata-derived side panel."""
    _set_slide_background(slide, theme.background_color)
    _add_section_label(slide, "Evidence", theme)

    _add_textbox(
        slide,
        MARGIN,
        TITLE_TOP,
        CONTENT_WIDTH,
        TITLE_HEIGHT,
        title,
        font_size=theme.title_font_size,
        color=theme.heading_color,
        font_name=theme.font_name,
        bold=True,
    )

    _add_accent_line(
        slide,
        MARGIN,
        TITLE_TOP + TITLE_HEIGHT + Inches(0.05),
        Inches(2.4),
        theme.secondary_accent,
    )

    panel_width = Inches(3.65)
    panel_gap = Inches(0.35)
    main_width = CONTENT_WIDTH - panel_width - panel_gap
    panel_left = MARGIN + main_width + panel_gap

    _add_left_bar(
        slide,
        BODY_TOP + Inches(0.1),
        BODY_HEIGHT - Inches(0.2),
        theme.secondary_accent,
    )
    _add_bullet_box(
        slide,
        MARGIN + Inches(0.18),
        BODY_TOP,
        main_width - Inches(0.18),
        BODY_HEIGHT,
        bullets,
        theme,
    )

    # Keep evidence metadata out of the title band: the previous compact badge
    # could clip a long limitation.  This side panel gives both cues enough room
    # while preserving the existing slide facts and citations.
    _add_rounded_card(
        slide,
        panel_left,
        BODY_TOP,
        panel_width,
        BODY_HEIGHT,
        WHITE,
    )
    inner_left = panel_left + Inches(0.28)
    inner_width = panel_width - Inches(0.56)

    _add_textbox(
        slide,
        inner_left,
        BODY_TOP + Inches(0.28),
        inner_width,
        Inches(0.28),
        "EVIDENCE STRENGTH",
        font_size=theme.badge_font_size,
        color=theme.primary_accent,
        font_name=theme.font_name,
        bold=True,
    )
    _add_textbox(
        slide,
        inner_left,
        BODY_TOP + Inches(0.65),
        inner_width,
        Inches(0.9),
        evidence_strength,
        font_size=theme.secondary_font_size,
        color=theme.heading_color,
        font_name=theme.font_name,
        bold=True,
    )

    _add_accent_line(
        slide,
        inner_left,
        BODY_TOP + Inches(1.72),
        inner_width,
        theme.card_fill,
        thickness=Pt(1.5),
    )

    _add_textbox(
        slide,
        inner_left,
        BODY_TOP + Inches(1.95),
        inner_width,
        Inches(0.28),
        "LIMITATION",
        font_size=theme.badge_font_size,
        color=theme.secondary_accent,
        font_name=theme.font_name,
        bold=True,
    )
    _add_textbox(
        slide,
        inner_left,
        BODY_TOP + Inches(2.32),
        inner_width,
        Inches(2.25),
        limitation,
        font_size=theme.secondary_font_size,
        color=theme.text_color,
        font_name=theme.font_name,
    )

    _add_footer_region(slide, footer, slide_number, theme)


def apply_summary_slide(
    slide: Slide,
    title: str,
    bullets: Sequence[str],
    footer: str,
    theme: PresentationTheme = DEFAULT_THEME,
    slide_number: int | None = None,
) -> None:
    """Style a take-home / summary slide with a highlight card."""
    _set_slide_background(slide, theme.background_color)

    # Reserve the top-right area for the badge so even a longer summary title
    # cannot render underneath it.
    badge_width = Inches(2.0)
    _add_textbox(
        slide,
        MARGIN,
        TITLE_TOP,
        CONTENT_WIDTH - badge_width - Inches(0.35),
        TITLE_HEIGHT,
        title,
        font_size=theme.title_font_size,
        color=theme.heading_color,
        font_name=theme.font_name,
        bold=True,
    )

    _add_accent_line(
        slide,
        MARGIN,
        TITLE_TOP + TITLE_HEIGHT + Inches(0.05),
        Inches(2.5),
        theme.secondary_accent,
    )

    # Take-home badge
    _add_badge(
        slide,
        SLIDE_WIDTH - MARGIN - badge_width,
        TITLE_TOP,
        badge_width,
        Inches(0.38),
        "Take-home",
        theme.secondary_accent,
        WHITE,
        theme,
        font_size=theme.badge_font_size,
    )

    # Highlight card
    card_top = BODY_TOP - Inches(0.15)
    card_height = BODY_HEIGHT + Inches(0.3)
    _add_rounded_card(
        slide,
        MARGIN,
        card_top,
        CONTENT_WIDTH,
        card_height,
        theme.card_fill,
    )
    _add_left_bar(
        slide,
        card_top + Inches(0.2),
        card_height - Inches(0.4),
        theme.secondary_accent,
    )

    _add_bullet_box(
        slide,
        MARGIN + Inches(0.2),
        BODY_TOP,
        CONTENT_WIDTH - Inches(0.4),
        BODY_HEIGHT,
        bullets,
        theme,
    )

    _add_footer_region(slide, footer, slide_number, theme)


def apply_references_slide(
    slide: Slide,
    title: str,
    bullets: Sequence[str],
    theme: PresentationTheme = DEFAULT_THEME,
    slide_number: int | None = None,
) -> None:
    """Style the final references slide as a clean, readable list."""
    _set_slide_background(slide, theme.background_color)

    _add_textbox(
        slide,
        MARGIN,
        TITLE_TOP,
        CONTENT_WIDTH,
        TITLE_HEIGHT,
        title,
        font_size=theme.title_font_size,
        color=theme.heading_color,
        font_name=theme.font_name,
        bold=True,
    )

    _add_accent_line(
        slide,
        MARGIN,
        TITLE_TOP + TITLE_HEIGHT + Inches(0.05),
        Inches(1.8),
        theme.primary_accent,
    )

    _add_left_bar(
        slide,
        BODY_TOP + Inches(0.1),
        BODY_HEIGHT - Inches(0.2),
        theme.primary_accent,
    )

    # Two-column layout when the list is long enough to benefit.
    count = len(bullets)
    if count > 6:
        col_width = (CONTENT_WIDTH - Inches(0.3)) / 2
        mid = (count + 1) // 2
        _add_bullet_box(
            slide,
            MARGIN + Inches(0.18),
            BODY_TOP,
            col_width,
            BODY_HEIGHT,
            bullets[:mid],
            theme,
            font_size=theme.secondary_font_size,
        )
        _add_bullet_box(
            slide,
            MARGIN + col_width + Inches(0.3),
            BODY_TOP,
            col_width,
            BODY_HEIGHT,
            bullets[mid:],
            theme,
            font_size=theme.secondary_font_size,
        )
    else:
        _add_bullet_box(
            slide,
            MARGIN + Inches(0.18),
            BODY_TOP,
            CONTENT_WIDTH - Inches(0.18),
            BODY_HEIGHT,
            bullets,
            theme,
            font_size=theme.secondary_font_size,
        )

    _add_footer_region(slide, "", slide_number, theme)
