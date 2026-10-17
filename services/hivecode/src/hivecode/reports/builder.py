"""Verification report builder — deterministic templates from stored evidence.

The report's check table, PR body, and API fields are all generated
from the same stored evidence by deterministic templates (WF-10).
Model-written summaries appear only in a separately labeled narrative section.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


@dataclass
class ReportSection:
    """A section of the verification report."""

    title: str
    content: str


@dataclass
class VerificationReport:
    """The complete verification report for a task."""

    task_id: UUID
    outcome: str
    policy_version: str
    generated_at: datetime
    sections: list[ReportSection] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render the report as Markdown."""
        lines = [
            "# Verification Report",
            "",
            f"**Outcome:** {self.outcome}",
            f"**Policy version:** {self.policy_version}",
            f"**Generated:** {self.generated_at.isoformat()}",
            "",
        ]

        for section in self.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Render the report as a dict."""
        return {
            "task_id": str(self.task_id),
            "outcome": self.outcome,
            "policy_version": self.policy_version,
            "generated_at": self.generated_at.isoformat(),
            "sections": [
                {"title": s.title, "content": s.content}
                for s in self.sections
            ],
        }


class ReportBuilder:
    """Builds verification reports from stored evidence."""

    def build(
        self,
        task_id: UUID,
        outcome: str,
        policy_version: str,
        title: str,
        objective: str,
        changed_files: list[str],
        check_results: list[dict],
        attempts_used: int,
        max_attempts: int,
        cost_usd: float,
        duration_s: float,
        verdict_reasons: list[str],
        evidence: dict,
    ) -> VerificationReport:
        """Build a verification report.

        All content is generated deterministically from the provided evidence.
        No LLM-generated content is included.
        """
        now = datetime.now(UTC)
        sections = []

        # Summary section
        summary = f"Fixed: {title}\n\n{objective}"
        sections.append(ReportSection(title="Summary", content=summary))

        # Changed files section
        files_content = "\n".join(f"- `{f}`" for f in changed_files) if changed_files else "No files changed."
        sections.append(ReportSection(title="Changed Files", content=files_content))

        # Check results section
        check_lines = []
        for check in check_results:
            status_icon = self._status_icon(check.get("status", "unknown"))
            check_lines.append(
                f"- {status_icon} **{check.get('check_key', 'unknown')}** "
                f"({check.get('status', 'unknown')})"
            )
        sections.append(ReportSection(title="Check Results", content="\n".join(check_lines)))

        # Metrics section
        metrics = f"""- **Outcome:** {outcome}
- **Attempts used:** {attempts_used}/{max_attempts}
- **Cost:** ${cost_usd:.2f}
- **Duration:** {duration_s:.0f}s
- **Policy version:** {policy_version}"""
        sections.append(ReportSection(title="Metrics", content=metrics))

        # Reasons section
        reasons_content = "\n".join(f"- `{r}`" for r in verdict_reasons)
        sections.append(ReportSection(title="Verdict Reasons", content=reasons_content))

        return VerificationReport(
            task_id=task_id,
            outcome=outcome,
            policy_version=policy_version,
            generated_at=now,
            sections=sections,
        )

    def build_pr_body(
        self,
        title: str,
        report: VerificationReport,
        diff_url: str | None = None,
    ) -> str:
        """Build the pull request body.

        Includes the verification report summary and links to evidence.
        """
        lines = [
            "## HiveCode Verification Report",
            "",
            f"**Outcome:** {report.outcome}",
            f"**Policy version:** {report.policy_version}",
            "",
            "### Summary",
            "",
            report.sections[0].content if report.sections else "No summary available.",
            "",
            "### Changed Files",
            "",
        ]

        # Add changed files from report
        for section in report.sections:
            if section.title == "Changed Files":
                lines.append(section.content)
                break

        lines.extend([
            "",
            "### Check Results",
            "",
        ])

        for section in report.sections:
            if section.title == "Check Results":
                lines.append(section.content)
                break

        if diff_url:
            lines.extend([
                "",
                "### Evidence",
                "",
                f"- [Full diff]({diff_url})",
            ])

        lines.extend([
            "",
            "---",
            "*This PR was created by HiveCode. Verification does not guarantee correctness.*",
        ])

        return "\n".join(lines)

    def _status_icon(self, status: str) -> str:
        """Get an icon for a check status."""
        icons = {
            "passed": "✓",
            "failed": "✗",
            "error": "⚠",
            "timed_out": "⏱",
            "skipped": "⊘",
            "unavailable": "?",
            "cancelled": "⊘",
        }
        return icons.get(status, "?")
