from ..models import Claim, Evidence


def validate_claims(claims: list[Claim], evidence: list[Evidence]) -> list[Claim]:
    valid = []
    for claim in claims:
        if claim.evidence_ids and all(0 <= index < len(evidence) for index in claim.evidence_ids):
            valid.append(claim)
    return valid

