"""Fully offline MockProvider.

MockProvider returns deterministic lesson content. It includes a verified
development fixture for the canonical "Dietary Fiber and Gut Health" topic.
For other topics it produces a safe generic educational outline that explicitly
states when evidence is unavailable and does not fabricate citations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.providers.base import LessonProvider, ProviderError
from src.schemas.lesson import (
    CitationRecord,
    GenerationMetadata,
    HealthClaim,
    Language,
    LessonMetadata,
    LessonPackage,
    LessonSlide,
    ReferenceType,
)

_FIXTURE_PATH = Path(__file__).resolve().parents[2] / "examples" / "dietary_fiber_evidence_fixture.json"


class MockProvider(LessonProvider):
    """Offline provider with a curated dietary-fiber fixture and a safe generic fallback."""

    name = "mock"
    version = "0.1.1"
    requires_api_key = False

    def __init__(self) -> None:
        self._fixture: dict[str, Any] | None = None

    def _load_fixture(self) -> dict[str, Any]:
        if self._fixture is None:
            if not _FIXTURE_PATH.exists():
                raise ProviderError(
                    f"Dietary fiber fixture not found at {_FIXTURE_PATH}. "
                    "Cannot generate canonical offline example."
                )
            with _FIXTURE_PATH.open("r", encoding="utf-8") as fh:
                self._fixture = json.load(fh)
        return self._fixture

    def generate(
        self,
        topic: str,
        audience: str,
        language: Language,
        duration_minutes: int = 30,
    ) -> LessonPackage:
        if language != Language.EN:
            raise ProviderError("MockProvider only supports English (en) in this MVP.")

        normalized_topic = topic.strip().lower()
        if "dietary fiber" in normalized_topic or "fiber and gut" in normalized_topic:
            return self._generate_dietary_fiber(topic, audience, duration_minutes)

        return self._generate_generic(topic, audience, duration_minutes)

    def _generate_dietary_fiber(
        self, topic: str, audience: str, duration_minutes: int
    ) -> LessonPackage:
        fixture = self._load_fixture()
        references = [CitationRecord(**r) for r in fixture["references"]]

        claims: list[HealthClaim] = []
        for c in fixture["claims"]:
            claims.append(
                HealthClaim(
                    claim_id=c["claim_id"],
                    claim_text=c["claim_text"],
                    slide_numbers=[],  # filled after slides are built
                    citation_ids=self._claim_to_citations(c["claim_id"]),
                    evidence_statement=c["evidence_statement"],
                    interpretation=c["interpretation"],
                    practical_advice=c["practical_advice"],
                    evidence_level=c["evidence_level"],
                    is_causal=c["is_causal"],
                    is_disease_treatment_claim=c["is_disease_treatment_claim"],
                    study_design=c.get("study_design"),
                    population=c.get("population"),
                    limitations=c.get("limitations"),
                )
            )

        slides = self._build_fiber_slides(claims)

        # Map claims to slide numbers deterministically.
        for claim in claims:
            claim.slide_numbers = [
                s.slide_number for s in slides if claim.claim_id in s.speaker_notes
            ]

        metadata = LessonMetadata(
            title="Dietary Fiber and Gut Health: An Evidence-Informed Introduction",
            topic=topic,
            audience=audience,
            language=Language.EN,
            duration_minutes=duration_minutes,
            learning_objectives=[
                "Define dietary fiber and identify common food sources.",
                "Describe the association between fiber intake and gut microbiota diversity.",
                "Interpret observational evidence on fiber and cardiometabolic outcomes without overstating causality.",
                "Apply practical, food-based strategies to increase fiber intake gradually.",
            ],
        )

        generation = GenerationMetadata(
            provider_name=self.name,
            provider_version=self.version,
            generation_mode="offline",
            is_deterministic_fixture=True,
            prompt_used=f"topic={topic}; audience={audience}; language=en",
        )

        return LessonPackage(
            metadata=metadata,
            generation=generation,
            slides=slides,
            claims=claims,
            references=references,
        )

    def _claim_to_citations(self, claim_id: str) -> list[str]:
        mapping = {
            "fiber_definition": ["Slavin2013", "USDA2020"],
            "fiber_microbiota_association": ["Makki2018", "Slavin2013"],
            "fiber_cvd_mortality_association": ["Reynolds2019"],
            "fiber_intake_gap": ["USDA2020", "Quagliani2017"],
            "fiber_practical_guidance": ["USDA2020"],
        }
        return mapping.get(claim_id, [])

    def _build_fiber_slides(self, claims: list[HealthClaim]) -> list[LessonSlide]:
        claim_by_id = {c.claim_id: c for c in claims}

        slides: list[LessonSlide] = [
            LessonSlide(
                slide_number=1,
                title="Dietary Fiber and Gut Health",
                slide_type="title",
                key_points=[
                    "An evidence-informed introduction for nutrition professionals and health educators.",
                ],
                speaker_notes="Introduce the lesson, the target audience, and emphasize that this is educational content, not medical advice.",
                citation_ids=[],
            ),
            LessonSlide(
                slide_number=2,
                title="Learning Objectives",
                slide_type="content",
                key_points=[
                    "Define dietary fiber and identify common food sources.",
                    "Describe fiber–gut microbiota associations.",
                    "Interpret observational evidence cautiously.",
                    "Apply practical, food-based guidance.",
                ],
                speaker_notes="Set expectations: the lesson focuses on associations and practical patterns, not treatment promises.",
                citation_ids=[],
            ),
            LessonSlide(
                slide_number=3,
                title="What Is Dietary Fiber?",
                slide_type="content",
                key_points=[
                    "Nondigestible carbohydrates and lignin intrinsic to plants.",
                    "Includes soluble and insoluble forms.",
                    "Found in vegetables, fruits, legumes, whole grains, nuts, and seeds.",
                ],
                speaker_notes=f"Claim: fiber_definition. {claim_by_id['fiber_definition'].evidence_statement}",
                citation_ids=["Slavin2013", "USDA2020"],
            ),
            LessonSlide(
                slide_number=4,
                title="Fiber and the Gut Microbiota",
                slide_type="content",
                key_points=[
                    "Fiber provides fermentable substrates for gut microbes.",
                    "Higher fiber intake is associated with greater microbial diversity.",
                    "Short-chain fatty acids (e.g., butyrate) are produced by fermentation.",
                ],
                speaker_notes=f"Claim: fiber_microbiota_association. {claim_by_id['fiber_microbiota_association'].evidence_statement} Stress 'associated with', not 'causes'.",
                citation_ids=["Makki2018", "Slavin2013"],
            ),
            LessonSlide(
                slide_number=5,
                title="Fiber and Health Outcomes",
                slide_type="content",
                key_points=[
                    "Higher fiber intake is associated with lower cardiovascular disease risk.",
                    "Prospective cohorts also report lower all-cause mortality with higher fiber intake.",
                    "These are associations; randomized trials on hard endpoints are limited.",
                ],
                speaker_notes=f"Claim: fiber_cvd_mortality_association. {claim_by_id['fiber_cvd_mortality_association'].evidence_statement} Emphasize observational nature and residual confounding.",
                citation_ids=["Reynolds2019"],
            ),
            LessonSlide(
                slide_number=6,
                title="The Fiber Intake Gap",
                slide_type="content",
                key_points=[
                    "Dietary guidelines recommend fiber-rich eating patterns.",
                    "Many adults fall short of recommended intake.",
                    "Food-based strategies can help close the gap without relying on supplements.",
                ],
                speaker_notes=f"Claim: fiber_intake_gap. {claim_by_id['fiber_intake_gap'].evidence_statement}",
                citation_ids=["USDA2020", "Quagliani2017"],
            ),
            LessonSlide(
                slide_number=7,
                title="Practical Guidance",
                slide_type="content",
                key_points=[
                    "Choose vegetables, fruits, whole grains, legumes, nuts, and seeds.",
                    "Use small food swaps, such as whole grains for refined grains.",
                    "Prioritize varied whole-plant foods over isolated supplements.",
                    "Individual needs and tolerance vary.",
                ],
                speaker_notes=f"Claim: fiber_practical_guidance. {claim_by_id['fiber_practical_guidance'].evidence_statement} Note medical conditions may require tailored advice.",
                citation_ids=["USDA2020"],
            ),
            LessonSlide(
                slide_number=8,
                title="Evidence and Limitations",
                slide_type="content",
                key_points=[
                    "Most long-term evidence is observational.",
                    "Associations do not prove causation.",
                    "Individual responses to fiber differ based on microbiota, diet, and health status.",
                ],
                speaker_notes="Reinforce conservative interpretation. No disease treatment promises are made.",
                citation_ids=["Reynolds2019"],
            ),
            LessonSlide(
                slide_number=9,
                title="Summary",
                slide_type="summary",
                key_points=[
                    "Dietary fiber is a plant-derived nutrient with diverse food sources.",
                    "Higher fiber intake is associated with beneficial gut microbial patterns and health outcomes.",
                    "Practical, varied, food-based changes are the safest educational message.",
                ],
                speaker_notes="Close by restating the educational purpose and disclaimer.",
                citation_ids=["Reynolds2019", "Makki2018"],
            ),
            LessonSlide(
                slide_number=10,
                title="References",
                slide_type="references",
                key_points=[
                    "Makki et al., 2018 — Cell Host & Microbe",
                    "Reynolds et al., 2019 — The Lancet",
                    "Slavin, 2013 — Nutrients",
                    "USDA/HHS, 2020 — Dietary Guidelines for Americans",
                    "Quagliani & Felt-Gunderson, 2017 — American Journal of Lifestyle Medicine",
                ],
                speaker_notes="Direct learners to the full references document for titles, DOIs, and limitations.",
                citation_ids=[
                    "Makki2018",
                    "Reynolds2019",
                    "Slavin2013",
                    "USDA2020",
                    "Quagliani2017",
                ],
            ),
        ]
        return slides

    def _generate_generic(
        self, topic: str, audience: str, duration_minutes: int
    ) -> LessonPackage:
        """Safe generic offline fallback.

        Does NOT fabricate citations. The only reference is a placeholder that
        explicitly states evidence was unavailable offline.
        """
        placeholder_ref = CitationRecord(
            citation_id="NO_EVIDENCE_OFFLINE",
            title=None,
            authors="MockProvider",
            year=2026,
            journal_or_org="Nutrition Lesson Generator",
            doi=None,
            pmid=None,
            url=None,
            evidence_level="unverified / provider-generated",
            reference_type=ReferenceType.PROVIDER_GENERATED,
            provenance_note=(
                "MockProvider generic fallback. No fixture exists for this topic; "
                "no verified citations were generated. Add a curated fixture or use "
                "a retrieval-capable provider for evidence-informed content."
            ),
        )

        metadata = LessonMetadata(
            title=f"{topic}: An Introductory Overview",
            topic=topic,
            audience=audience,
            language=Language.EN,
            duration_minutes=duration_minutes,
            learning_objectives=[
                f"Introduce the topic '{topic}' at a high level.",
                "Identify where verified evidence is currently unavailable offline.",
                "Outline safe, general educational next steps.",
            ],
        )

        generation = GenerationMetadata(
            provider_name=self.name,
            provider_version=self.version,
            generation_mode="offline",
            is_deterministic_fixture=False,
            prompt_used=f"topic={topic}; audience={audience}; language=en",
        )

        slides = [
            LessonSlide(
                slide_number=1,
                title=metadata.title,
                slide_type="title",
                key_points=["Introductory lesson generated offline."],
                speaker_notes="Explain that this is a generic outline without verified evidence for the requested topic.",
            ),
            LessonSlide(
                slide_number=2,
                title="Scope and Evidence Status",
                slide_type="content",
                key_points=[
                    "This topic does not have a curated offline evidence fixture.",
                    "No health claims with fabricated citations are included.",
                    "Add a fixture or switch to an online provider for evidence-informed content.",
                ],
                speaker_notes="Be transparent about the offline limitation. Do not invent citations.",
                citation_ids=["NO_EVIDENCE_OFFLINE"],
            ),
            LessonSlide(
                slide_number=3,
                title="General Educational Approach",
                slide_type="content",
                key_points=[
                    "Start with definitions and food sources.",
                    "Review mechanisms and biological plausibility.",
                    "Summarize the strength and limitations of available evidence.",
                    "Provide food-based, non-prescriptive practical guidance.",
                ],
                speaker_notes="Recommend using the dietary fiber fixture as a template for future topics.",
            ),
            LessonSlide(
                slide_number=4,
                title="References",
                slide_type="references",
                key_points=[
                    "No verified references available for this generic offline lesson.",
                    placeholder_ref.provenance_note,
                ],
                speaker_notes="Cite the placeholder honestly.",
                citation_ids=["NO_EVIDENCE_OFFLINE"],
            ),
        ]

        return LessonPackage(
            metadata=metadata,
            generation=generation,
            slides=slides,
            claims=[],
            references=[placeholder_ref],
        )
