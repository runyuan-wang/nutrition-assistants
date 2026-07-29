"""Quality validator enforcing the evidence and safety contract."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from src.schemas.lesson import (
    EvidenceLevel,
    LessonPackage,
    QualityIssue,
    QualityReport,
    ReferenceType,
)


class QualityValidator:
    """Validate a LessonPackage against the project's evidence contract."""

    # Heuristic patterns that suggest causal overstatement.
    CAUSAL_WORDS = [
        "causes",
        "prevents",
        "cures",
        "treats",
        "eliminates",
        "will reduce",
        "will increase",
        "leads to",
        "results in",
    ]

    # Patterns suggesting disease treatment promises.
    DISEASE_TREATMENT_WORDS = [
        "treat",
        "cure",
        "diagnose",
        "prescribe",
        "medication",
        "dose",
        "mg",
        "supplement regimen",
        "stop taking",
    ]

    # Numeric claims need a citation containing a year/DOI/PMID to be considered supported.
    NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|g|mg|mcg|kg|lb|oz|kcal|cal|per|/|fold|x)(?:\b|$|\s)")

    def validate(self, package: LessonPackage) -> QualityReport:
        issues: list[QualityIssue] = []

        # Counts
        total_slides = len(package.slides)
        total_claims = len(package.claims)
        total_citations = len(package.references)
        claims_with_citations = sum(1 for c in package.claims if c.citation_ids)
        causal_claims = sum(1 for c in package.claims if c.is_causal)
        disease_treatment_claims = sum(
            1 for c in package.claims if c.is_disease_treatment_claim
        )
        unverified_citations = sum(
            1
            for r in package.references
            if r.reference_type == ReferenceType.PROVIDER_GENERATED
            or r.evidence_level == EvidenceLevel.UNVERIFIED
        )

        # 1. Every substantive health claim has a citation.
        for claim in package.claims:
            if not claim.citation_ids:
                issues.append(
                    QualityIssue(
                        severity="error",
                        rule="claim_requires_citation",
                        claim_id=claim.claim_id,
                        message=f"Claim '{claim.claim_id}' has no citations.",
                        suggestion="Add at least one verified citation or remove the claim.",
                    )
                )

        # 2. Do not turn observational association into causal claims.
        for claim in package.claims:
            if claim.is_causal and claim.evidence_level in {
                EvidenceLevel.OBSERVATIONAL,
                EvidenceLevel.UNVERIFIED,
            }:
                issues.append(
                    QualityIssue(
                        severity="error",
                        rule="no_causal_overstatement",
                        claim_id=claim.claim_id,
                        message=(
                            f"Claim '{claim.claim_id}' is marked causal but is backed "
                            f"by {claim.evidence_level.value} evidence."
                        ),
                        suggestion="Rephrase as an association or strengthen evidence.",
                    )
                )

        # 3. Separate evidence, interpretation, and practical advice.
        for claim in package.claims:
            for field, label in [
                (claim.evidence_statement, "evidence_statement"),
                (claim.interpretation, "interpretation"),
                (claim.practical_advice, "practical_advice"),
            ]:
                if not field or len(field) < 3:
                    issues.append(
                        QualityIssue(
                            severity="error",
                            rule="separate_evidence_interpretation_advice",
                            claim_id=claim.claim_id,
                            message=f"Claim '{claim.claim_id}' has an empty {label}.",
                            suggestion="Populate evidence, interpretation, and practical advice distinctly.",
                        )
                    )

        # 4. No disease treatment promises.
        for claim in package.claims:
            if claim.is_disease_treatment_claim:
                issues.append(
                    QualityIssue(
                        severity="error",
                        rule="no_disease_treatment_claims",
                        claim_id=claim.claim_id,
                        message=f"Claim '{claim.claim_id}' appears to promise diagnosis or treatment.",
                        suggestion="Rephrase as educational information and add a disclaimer.",
                    )
                )

        # 5. Include limitations and population/applicability.
        for claim in package.claims:
            if not claim.limitations or not claim.population:
                issues.append(
                    QualityIssue(
                        severity="warning",
                        rule="include_limitations_and_population",
                        claim_id=claim.claim_id,
                        message=f"Claim '{claim.claim_id}' is missing limitations or population notes.",
                        suggestion="Add study limitations and applicable population.",
                    )
                )

        # 6. Flag unsupported numerical claims.
        unsupported_numerical_claims = 0
        for claim in package.claims:
            if self.NUMBER_PATTERN.search(claim.claim_text):
                if not self._has_verified_reference(claim.citation_ids, package):
                    unsupported_numerical_claims += 1
                    issues.append(
                        QualityIssue(
                            severity="warning",
                            rule="unsupported_numerical_claim",
                            claim_id=claim.claim_id,
                            message=f"Claim '{claim.claim_id}' contains a numerical statement without verified citation metadata.",
                            suggestion="Add a verified DOI/PMID/year citation or remove the number.",
                        )
                    )

        # 7. Distinguish verified fixtures from provider-generated citations.
        for ref in package.references:
            if ref.reference_type == ReferenceType.PROVIDER_GENERATED:
                issues.append(
                    QualityIssue(
                        severity="info",
                        rule="provider_generated_citation",
                        message=f"Citation '{ref.citation_id}' is provider-generated and unverified.",
                        suggestion="Verify DOI/PMID/title through official sources before publication.",
                    )
                )

        # 8. Do not fabricate DOI/PMID/title/organization.
        for ref in package.references:
            if ref.reference_type == ReferenceType.DEVELOPMENT_FIXTURE:
                if ref.doi and not ref.doi.startswith("10."):
                    issues.append(
                        QualityIssue(
                            severity="error",
                            rule="no_fabricated_doi",
                            claim_id=None,
                            message=f"Fixture citation '{ref.citation_id}' has an invalid DOI.",
                            suggestion="DOI must begin with '10.'.",
                        )
                    )

        pass_gate = not any(i.severity == "error" for i in issues)

        summary_parts = [
            f"Validated {total_claims} claims across {total_slides} slides with {total_citations} references.",
            f"Causal claims: {causal_claims}; disease/treatment claims: {disease_treatment_claims}; unsupported numbers: {unsupported_numerical_claims}.",
            f"Quality gate {'passed' if pass_gate else 'failed'} with {len(issues)} issue(s).",
        ]

        return QualityReport(
            package_title=package.metadata.title,
            generated_at=datetime.now(timezone.utc),
            total_slides=total_slides,
            total_claims=total_claims,
            total_citations=total_citations,
            claims_with_citations=claims_with_citations,
            causal_claims=causal_claims,
            disease_treatment_claims=disease_treatment_claims,
            unsupported_numerical_claims=unsupported_numerical_claims,
            unverified_citations=unverified_citations,
            issues=issues,
            summary=" ".join(summary_parts),
            pass_quality_gate=pass_gate,
        )

    @staticmethod
    def _has_verified_reference(citation_ids: list[str], package: LessonPackage) -> bool:
        ref_by_id = {r.citation_id: r for r in package.references}
        for cid in citation_ids:
            ref = ref_by_id.get(cid)
            if ref and ref.reference_type in {
                ReferenceType.DEVELOPMENT_FIXTURE,
                ReferenceType.PUBMED_RETRIEVED,
            }:
                if ref.doi or ref.pmid or ref.year:
                    return True
        return False
