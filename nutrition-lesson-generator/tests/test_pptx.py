"""Tests for PowerPoint export and OOXML validation."""

from __future__ import annotations

import zipfile
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from src.exporters.ppt import PptxExporter
from src.providers.mock_provider import MockProvider
from src.schemas.lesson import Language
from templates.ppt_template import BODY_TOP, DEFAULT_THEME, SLIDE_HEIGHT, SLIDE_WIDTH


def _generate_package():
    return MockProvider().generate(
        topic="Dietary Fiber and Gut Health",
        audience="general adults",
        language=Language.EN,
    )


def _export_to(path: Path):
    package = _generate_package()
    PptxExporter().export(package, path)
    return package


def test_pptx_export_and_reopen(tmp_path: Path):
    package = _generate_package()
    out = tmp_path / "lesson.pptx"
    PptxExporter().export(package, out)

    assert out.exists()
    assert out.stat().st_size > 0

    prs = Presentation(str(out))
    assert len(prs.slides) == len(package.slides)

    first_slide = prs.slides[0]
    assert first_slide.shapes


def test_pptx_is_valid_ooxml_zip(tmp_path: Path):
    package = _generate_package()
    out = tmp_path / "lesson.pptx"
    PptxExporter().export(package, out)

    with zipfile.ZipFile(out, "r") as zf:
        names = zf.namelist()
        assert "[Content_Types].xml" in names
        assert "ppt/presentation.xml" in names
        slide_parts = [n for n in names if n.startswith("ppt/slides/slide")]
        assert len(slide_parts) == len(package.slides)


def test_pptx_has_references_slide(tmp_path: Path):
    package = _generate_package()
    out = tmp_path / "lesson.pptx"
    PptxExporter().export(package, out)

    prs = Presentation(str(out))
    titles = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                titles.append(shape.text_frame.text.strip().split("\n")[0])
    assert any("Reference" in t for t in titles)


# ---------------------------------------------------------------------------
# Visual/layout contract tests
# ---------------------------------------------------------------------------
def test_pptx_uses_16x9_canvas(tmp_path: Path):
    out = tmp_path / "lesson.pptx"
    _export_to(out)

    prs = Presentation(str(out))
    assert prs.slide_width == SLIDE_WIDTH
    assert prs.slide_height == SLIDE_HEIGHT
    assert prs.slide_width == Inches(13.333333)
    assert prs.slide_height == Inches(7.5)


def test_pptx_all_shapes_within_slide_bounds(tmp_path: Path):
    out = tmp_path / "lesson.pptx"
    _export_to(out)

    prs = Presentation(str(out))
    for slide in prs.slides:
        for shape in slide.shapes:
            assert shape.left >= 0
            assert shape.top >= 0
            assert shape.left + shape.width <= prs.slide_width + 1
            assert shape.top + shape.height <= prs.slide_height + 1


def test_pptx_slide_numbers_visible(tmp_path: Path):
    out = tmp_path / "lesson.pptx"
    package = _export_to(out)

    prs = Presentation(str(out))
    for slide_pkg, slide in zip(package.slides, prs.slides):
        if slide_pkg.slide_type == "title":
            continue
        slide_texts = [
            shape.text_frame.text.strip()
            for shape in slide.shapes
            if shape.has_text_frame
        ]
        assert str(slide_pkg.slide_number) in slide_texts


def test_pptx_speaker_notes_preserved(tmp_path: Path):
    out = tmp_path / "lesson.pptx"
    package = _export_to(out)

    prs = Presentation(str(out))
    for slide_pkg, slide in zip(package.slides, prs.slides):
        notes_text = slide.notes_slide.notes_text_frame.text
        assert slide_pkg.speaker_notes in notes_text


def test_pptx_exact_pmid_footer_strings(tmp_path: Path):
    out = tmp_path / "lesson.pptx"
    package = _export_to(out)

    pmids = {r.citation_id: r.pmid for r in package.references if r.pmid}
    prs = Presentation(str(out))
    for slide_pkg, slide in zip(package.slides, prs.slides):
        if slide_pkg.slide_type == "references":
            continue
        texts = [
            shape.text_frame.text for shape in slide.shapes if shape.has_text_frame
        ]
        full_text = "\n".join(texts)
        for cid in slide_pkg.citation_ids:
            pmid = pmids.get(cid)
            if pmid:
                assert f"PMID: {pmid}" in full_text


def test_pptx_text_is_editable_and_semantic_text_preserved(tmp_path: Path):
    out = tmp_path / "lesson.pptx"
    package = _export_to(out)

    prs = Presentation(str(out))
    for slide_pkg, slide in zip(package.slides, prs.slides):
        slide_text = "\n".join(
            shape.text_frame.text for shape in slide.shapes if shape.has_text_frame
        )
        assert slide_pkg.title in slide_text
        # Title slides render only the title and subtitle, not key points.
        if slide_pkg.slide_type == "title":
            continue
        for point in slide_pkg.key_points:
            assert point in slide_text


def test_pptx_layout_routing(tmp_path: Path):
    out = tmp_path / "lesson.pptx"
    package = _export_to(out)

    prs = Presentation(str(out))
    texts_by_slide = []
    for slide in prs.slides:
        texts_by_slide.append(
            "\n".join(
                shape.text_frame.text for shape in slide.shapes if shape.has_text_frame
            )
        )

    # Title slide: no slide-number footer-only region, title + audience subtitle.
    title_text = texts_by_slide[0]
    assert package.slides[0].title in title_text
    assert package.metadata.audience in title_text

    # Learning objectives slide gets the section label.
    assert "OBJECTIVES" in texts_by_slide[1].upper()

    # Evidence-highlight slide gets readable, metadata-derived callouts.
    evidence_idx = next(
        i
        for i, s in enumerate(package.slides)
        if "evidence" in s.title.lower() and "limitation" in s.title.lower()
    )
    evidence_text = texts_by_slide[evidence_idx]
    assert "EVIDENCE STRENGTH" in evidence_text
    assert "LIMITATION" in evidence_text
    assert "systematic review / meta-analysis" in evidence_text

    # Summary / take-home slide gets the badge.
    summary_idx = next(
        i for i, s in enumerate(package.slides) if s.slide_type == "summary"
    )
    assert "Take-home" in texts_by_slide[summary_idx]

    # References slide keeps full references and drops the compact sources footer.
    ref_idx = next(
        i for i, s in enumerate(package.slides) if s.slide_type == "references"
    )
    ref_text = texts_by_slide[ref_idx]
    assert package.slides[ref_idx].key_points[0] in ref_text
    assert "Sources:" not in ref_text


def test_pptx_zip_crc_valid(tmp_path: Path):
    out = tmp_path / "lesson.pptx"
    _export_to(out)

    with zipfile.ZipFile(out, "r") as zf:
        assert zf.testzip() is None


def test_pptx_typography_hierarchy(tmp_path: Path):
    out = tmp_path / "lesson.pptx"
    package = _export_to(out)
    prs = Presentation(str(out))

    content_slide = prs.slides[2]
    title_shape = next(
        shape
        for shape in content_slide.shapes
        if shape.has_text_frame and shape.text_frame.text == package.slides[2].title
    )
    bullet_shape = next(
        shape
        for shape in content_slide.shapes
        if shape.has_text_frame
        and package.slides[2].key_points[0] in shape.text_frame.text
    )
    footer_shape = next(
        shape
        for shape in content_slide.shapes
        if shape.has_text_frame and shape.text_frame.text.startswith("Sources:")
    )

    assert title_shape.text_frame.paragraphs[0].font.size.pt == DEFAULT_THEME.title_font_size
    assert all(
        paragraph.font.size.pt == DEFAULT_THEME.body_font_size
        for paragraph in bullet_shape.text_frame.paragraphs
    )
    assert footer_shape.text_frame.paragraphs[0].font.size.pt == DEFAULT_THEME.footer_font_size
    assert title_shape.text_frame.paragraphs[0].font.name == DEFAULT_THEME.font_name

    reference_slide = prs.slides[-1]
    reference_body = next(
        shape
        for shape in reference_slide.shapes
        if shape.has_text_frame
        and package.slides[-1].key_points[0] in shape.text_frame.text
    )
    assert all(
        paragraph.font.size.pt == DEFAULT_THEME.secondary_font_size
        for paragraph in reference_body.text_frame.paragraphs
    )


def test_pptx_evidence_callouts_have_dedicated_body_space(tmp_path: Path):
    out = tmp_path / "lesson.pptx"
    package = _export_to(out)
    evidence_idx = next(
        i
        for i, slide in enumerate(package.slides)
        if "evidence" in slide.title.lower() and "limitation" in slide.title.lower()
    )
    evidence_slide = Presentation(str(out)).slides[evidence_idx]

    strength_label = next(
        shape
        for shape in evidence_slide.shapes
        if shape.has_text_frame and shape.text_frame.text == "EVIDENCE STRENGTH"
    )
    limitation_body = next(
        shape
        for shape in evidence_slide.shapes
        if shape.has_text_frame and "residual confounding" in shape.text_frame.text
    )

    assert strength_label.top >= BODY_TOP
    assert limitation_body.top >= BODY_TOP
    assert limitation_body.height >= Inches(2.0)
    assert limitation_body.left > SLIDE_WIDTH // 2


def test_pptx_summary_title_does_not_overlap_badge(tmp_path: Path):
    out = tmp_path / "lesson.pptx"
    package = _export_to(out)
    summary_idx = next(
        i for i, slide in enumerate(package.slides) if slide.slide_type == "summary"
    )
    summary_slide = Presentation(str(out)).slides[summary_idx]
    title_shape = next(
        shape
        for shape in summary_slide.shapes
        if shape.has_text_frame
        and shape.text_frame.text == package.slides[summary_idx].title
    )
    badge_shape = next(
        shape
        for shape in summary_slide.shapes
        if shape.has_text_frame and shape.text_frame.text == "Take-home"
    )

    assert title_shape.left + title_shape.width < badge_shape.left
