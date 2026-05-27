import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class JobSourceKind(StrEnum):
    url = "url"
    pasted = "pasted"


class JobStatus(StrEnum):
    pending = "pending"
    scraping = "scraping"
    extracting = "extracting"
    ready = "ready"
    failed = "failed"


class RemotePolicy(StrEnum):
    onsite = "onsite"
    hybrid = "hybrid"
    remote = "remote"
    unspecified = "unspecified"


class Seniority(StrEnum):
    junior = "junior"
    mid = "mid"
    senior = "senior"
    lead = "lead"
    principal = "principal"
    unspecified = "unspecified"


class RequirementCategory(StrEnum):
    required = "required"
    nice_to_have = "nice_to_have"
    responsibility = "responsibility"


class ExtractedRequirement(BaseModel):
    text: str = Field(
        description=(
            "One requirement, responsibility, or nice-to-have item from the "
            "posting. Quote the posting verbatim — paraphrasing loses the "
            "specific terminology that drives good matches against the CV."
        )
    )
    category: RequirementCategory = Field(
        description=(
            "'required' for must-have qualifications, 'nice_to_have' for "
            "bonus items, 'responsibility' for what the role does day-to-day."
        )
    )


class JobExtraction(BaseModel):
    title: str | None = Field(
        description="The job title as written in the posting. Null if not clearly stated."
    )
    company: str | None = Field(
        description="Company name as written in the posting. Null if not stated."
    )
    location: str | None = Field(
        description="City and/or region as written. Null if not stated."
    )
    remote_policy: RemotePolicy = Field(
        default=RemotePolicy.unspecified,
        description=(
            "Remote work policy if stated. 'unspecified' when the posting "
            "doesn't say."
        ),
    )
    seniority: Seniority = Field(
        default=Seniority.unspecified,
        description=(
            "Seniority level if implied by title or requirements. "
            "'unspecified' when not clearly indicated."
        ),
    )
    tech_stack: list[str] = Field(
        default_factory=list,
        description=(
            "Technologies, languages, frameworks, libraries, tools, cloud "
            "providers mentioned as required or used. Lowercase. "
            "Deduplicated. Exclude soft skills like 'communication'."
        ),
    )
    salary_range: str | None = Field(
        description=(
            "Salary range as written, e.g. '€60-80k', '$120k-$150k base'. "
            "Null if not stated."
        )
    )
    summary: str | None = Field(
        description=(
            "One-paragraph plain summary of the role. No marketing language "
            "('rockstar', 'ninja', 'passionate', 'thrilled'). Null if no "
            "meaningful summary can be drawn."
        )
    )
    requirements: list[ExtractedRequirement] = Field(
        description=(
            "One item per clause. Split bulleted lists so each item is its "
            "own requirement entry."
        )
    )


class CreateJobFromText(BaseModel):
    raw_text: str = Field(min_length=1, description="The job posting text, pasted as-is.")
    source_url: str | None = Field(
        default=None,
        description="Optional source URL the text was copied from.",
    )


class CreateJobFromUrl(BaseModel):
    source_url: HttpUrl = Field(description="The URL of the job posting to scrape.")


class JobRequirementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    category: RequirementCategory
    embedding_model: str | None
    created_at: datetime


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_url: str | None
    source_kind: JobSourceKind
    raw_text: str
    status: JobStatus
    error_message: str | None
    title: str | None
    company: str | None
    location: str | None
    remote_policy: RemotePolicy
    seniority: Seniority
    tech_stack: list[str]
    salary_range: str | None
    summary: str | None
    requirements: list[JobRequirementRead]
    created_at: datetime
    updated_at: datetime


class JobListItem(BaseModel):
    """Slim representation for list endpoints — omits raw_text and requirements."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_url: str | None
    source_kind: JobSourceKind
    status: JobStatus
    title: str | None
    company: str | None
    location: str | None
    remote_policy: RemotePolicy
    seniority: Seniority
    tech_stack: list[str]
    created_at: datetime
    updated_at: datetime
