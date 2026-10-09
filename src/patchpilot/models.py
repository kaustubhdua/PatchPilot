from pydantic import BaseModel, ConfigDict, Field

class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(default="Untitled change", min_length=1, max_length=200)
    base_ref: str = Field(default="base", min_length=1, max_length=128)
    head_ref: str = Field(default="head", min_length=1, max_length=128)
    diff: str = Field(min_length=1, max_length=500_000)

class FileChange(BaseModel):
    path: str
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    is_test: bool

class Finding(BaseModel):
    rule_id: str
    severity: str
    title: str
    detail: str
    evidence: list[str] = Field(default_factory=list)

class AnalyzeResponse(BaseModel):
    title: str
    base_ref: str
    head_ref: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: str
    summary: str
    files_changed: int
    additions: int
    deletions: int
    files: list[FileChange]
    findings: list[Finding]
    recommended_tests: list[str]
    disclaimer: str
