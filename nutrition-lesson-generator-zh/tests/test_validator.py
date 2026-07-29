"""Focused safety and page-type tests for the Chinese lesson generator."""

import pytest
from pydantic import ValidationError

from src.pipeline.generator import 生成课程
from src.pipeline.validator import 标准免责声明, 验证课程
from src.schemas.lesson import 课程页面类型, 生成请求, 课件页面


@pytest.fixture
def generated_course():
    """Return the built-in offline generated lesson used by the package examples."""
    return 生成课程(生成请求(主题="膳食纤维与肠道健康"))


def _with_reference_page(course, *, 正文=None, 讲稿=None):
    pages = list(course.页面列表)
    index = next(
        i for i, page in enumerate(pages)
        if page.页面类型 == 课程页面类型.参考文献
    )
    reference = pages[index]
    pages[index] = reference.model_copy(
        update={
            "正文": reference.正文 if 正文 is None else 正文,
            "讲稿": reference.讲稿 if 讲稿 is None else 讲稿,
        }
    )
    return course.model_copy(update={"页面列表": pages})


def test_built_in_reference_page_with_exact_disclaimer_validates(generated_course):
    reference = next(
        page for page in generated_course.页面列表
        if page.页面类型 == 课程页面类型.参考文献
    )
    assert 标准免责声明 in reference.正文

    passed, problems = 验证课程(generated_course)

    assert passed, problems


def test_reference_page_extra_treatment_language_is_not_exempt(generated_course):
    reference = next(
        page for page in generated_course.页面列表
        if page.页面类型 == 课程页面类型.参考文献
    )
    course = _with_reference_page(
        generated_course,
        正文=reference.正文 + "\n额外内容：请自行治疗。",
    )

    passed, problems = 验证课程(course)

    assert not passed
    assert any("治疗" in problem for problem in problems)


@pytest.mark.parametrize(
    ("额外正文", "期望提示"),
    [
        ("额外内容：孕妇可自行调整饮食。", "特殊人群"),
        ("额外内容：不要把人称作胖子。胖子应该被责备。", "羞耻化语言"),
    ],
)
def test_reference_page_cannot_bypass_vulnerable_or_stigma_checks(
    generated_course, 额外正文, 期望提示
):
    reference = next(
        page for page in generated_course.页面列表
        if page.页面类型 == 课程页面类型.参考文献
    )
    course = _with_reference_page(
        generated_course,
        正文=reference.正文 + "\n" + 额外正文,
        讲稿="",
    )

    passed, problems = 验证课程(course)

    assert not passed
    assert any(期望提示 in problem for problem in problems)


def test_reference_page_speaker_notes_treatment_attack_is_rejected(generated_course):
    reference = next(
        page for page in generated_course.页面列表
        if page.页面类型 == 课程页面类型.参考文献
    )
    course = _with_reference_page(
        generated_course,
        讲稿="讲稿攻击：请自行治疗。",
    )

    passed, problems = 验证课程(course)

    assert 标准免责声明 in reference.正文
    assert not passed
    assert any("治疗" in problem for problem in problems)


def test_reference_page_speaker_notes_vulnerable_population_attack_is_rejected(generated_course):
    reference = next(
        page for page in generated_course.页面列表
        if page.页面类型 == 课程页面类型.参考文献
    )
    course = _with_reference_page(
        generated_course,
        讲稿="讲稿攻击：孕妇可以自行调整饮食。",
    )

    passed, problems = 验证课程(course)

    assert 标准免责声明 in reference.正文
    assert not passed
    assert any("特殊人群" in problem for problem in problems)


def test_reference_page_speaker_notes_stigma_attack_is_rejected(generated_course):
    reference = next(
        page for page in generated_course.页面列表
        if page.页面类型 == 课程页面类型.参考文献
    )
    course = _with_reference_page(
        generated_course,
        讲稿="讲稿攻击：胖子应该被责备。",
    )

    passed, problems = 验证课程(course)

    assert 标准免责声明 in reference.正文
    assert not passed
    assert any("羞耻化语言" in problem for problem in problems)


def test_unsupported_page_type_is_rejected():
    with pytest.raises(ValidationError):
        课件页面(
            页码=1,
            标题="测试",
            正文="正文",
            讲稿="讲稿",
            页面类型="未支持的页面类型",
        )
