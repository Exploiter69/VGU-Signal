from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class VerificationState(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    CONFLICTING = "CONFLICTING"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"
    REMOVED = "REMOVED"


class RelationshipKind(StrEnum):
    SAME_CONTENT = "SAME_CONTENT"
    URL_REPLACEMENT = "URL_REPLACEMENT"
    SIMILAR = "SIMILAR"
    SUPERSEDES = "SUPERSEDES"
    CORRECTS = "CORRECTS"
    CONFLICTS = "CONFLICTS"


class EvidenceClaim(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    normalized_statement: str = Field(min_length=1)
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    state: VerificationState = VerificationState.UNVERIFIED
    first_seen_at: datetime
    last_seen_at: datetime
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    supersedes_claim_id: str | None = None
    correction_of_claim_id: str | None = None


class EvidenceLink(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    role: str = Field(min_length=1)


class ClaimRelationship(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    left_claim_id: str = Field(min_length=1)
    right_claim_id: str = Field(min_length=1)
    kind: RelationshipKind
    created_at: datetime
    reason: str = Field(min_length=1)
    similarity: float | None = Field(default=None, ge=0, le=1)


class VerificationDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim_id: str = Field(min_length=1)
    state: VerificationState
    evidence_ids: tuple[str, ...] = ()
    reason: str = Field(min_length=1)
    decided_at: datetime


class Provenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim_id: str = Field(min_length=1)
    state: VerificationState
    source_id: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    observed_at: datetime
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    supersedes_claim_id: str | None = None
    correction_of_claim_id: str | None = None

    def human_summary(self) -> str:
        state = self.state.value.lower().replace("_", " ")
        validity = ""
        if self.effective_from or self.effective_until:
            validity = (
                f"; effective {self.effective_from or 'unknown'} "
                f"to {self.effective_until or 'open-ended'}"
            )
        return (
            f"{state} claim {self.claim_id} from {self.source_id}; "
            f"evidence {self.evidence_id} ({self.evidence_hash[:12]}…){validity}; "
            f"source: {self.source_url}"
        )
