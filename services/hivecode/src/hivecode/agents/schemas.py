"""Pydantic schemas for agent outputs.

All agent outputs are validated against these schemas.
"""

from pydantic import BaseModel, Field


class Diagnosis(BaseModel):
    """Output schema for the analyst agent."""

    root_cause: str = Field(..., description="Clear description of the root cause")
    evidence: list[str] = Field(default_factory=list, description="List of evidence references")
    affected_files: list[str] = Field(default_factory=list, description="Files that need changes")
    proposed_changes: list["ProposedChange"] = Field(default_factory=list)
    validation_plan: list[str] = Field(default_factory=list)
    confidence: str = Field(default="medium", pattern="^(high|medium|low)$")


class ProposedChange(BaseModel):
    """A single proposed change."""

    file: str
    description: str
    change_type: str = Field(pattern="^(modify|add|delete)$")


class EditSet(BaseModel):
    """Output schema for the coder agent."""

    edits: list["Edit"] = Field(default_factory=list)
    new_files: list["NewFile"] = Field(default_factory=list)
    summary: str = ""


class Edit(BaseModel):
    """A single file edit."""

    file: str
    search_text: str
    replacement: str
    description: str


class NewFile(BaseModel):
    """A new file to create."""

    path: str
    content: str
    description: str


class ReviewFindings(BaseModel):
    """Output schema for the reviewer agent."""

    findings: list["Finding"] = Field(default_factory=list)
    overall_assessment: str = Field(pattern="^(approve|request_changes|block)$")
    summary: str = ""


class Finding(BaseModel):
    """A single review finding."""

    severity: str = Field(pattern="^(critical|high|medium|low|info)$")
    category: str
    file_path: str | None = None
    line: int | None = None
    message: str
    blocks_delivery: bool = False


class FailureClassification(BaseModel):
    """Output schema for the failure analyst agent."""

    classification: str = Field(pattern="^(patch_related|environmental|pre_existing|unknown)$")
    reasoning: str
    confidence: str = Field(pattern="^(high|medium|low)$")
    suggested_action: str = Field(pattern="^(repair|re-run|stop)$")


# Forward references
Diagnosis.model_rebuild()
EditSet.model_rebuild()
ReviewFindings.model_rebuild()
