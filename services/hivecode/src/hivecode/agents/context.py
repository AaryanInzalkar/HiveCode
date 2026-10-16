"""Context assembly for agents.

Uses ripgrep-style search and Python AST symbol lookup, not embeddings.
Log excerpts keep head, tail, and failing-test sections within a token budget.
"""

from dataclasses import dataclass, field

from hivecode.tools.read_only import ReadOnlyTools


@dataclass
class ContextBudget:
    """Token budget for context assembly."""

    max_tokens: int = 32000
    max_file_lines: int = 500
    max_search_matches: int = 50
    max_log_lines: int = 200


@dataclass
class AssembledContext:
    """Assembled context for an LLM call."""

    files: list[str] = field(default_factory=list)
    search_results: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    estimated_tokens: int = 0


class ContextAssembler:
    """Assembles context for LLM calls within a token budget."""

    def __init__(self, tools: ReadOnlyTools, budget: ContextBudget = ContextBudget()):
        self.tools = tools
        self.budget = budget

    def assemble_for_diagnosis(
        self,
        issue_description: str,
        affected_files: list[str] | None = None,
        search_patterns: list[str] | None = None,
    ) -> AssembledContext:
        """Assemble context for the diagnosis phase.

        Includes:
        - Issue description
        - Affected files (or top-level files if none specified)
        - Search results for relevant patterns
        - Symbol lookups for key functions/classes
        """
        context = AssembledContext()
        estimated = 0

        # Add affected files
        if affected_files:
            for file_path in affected_files:
                result = self.tools.read_file(file_path)
                if result.success:
                    context.files.append(f"--- {file_path} ---\n{result.content}")
                    estimated += len(result.content) // 4  # Rough token estimate
        else:
            # Show top-level structure
            result = self.tools.list_files(".")
            if result.success:
                context.files.append(f"--- Repository Structure ---\n{result.content}")
                estimated += len(result.content) // 4

            # Show key Python files
            result = self.tools.search("^(class|def|async def)", ".", "*.py")
            if result.success and result.content != "No matches found":
                context.files.append(f"--- Python Symbols ---\n{result.content}")
                estimated += len(result.content) // 4

        # Add search results
        if search_patterns:
            for pattern in search_patterns:
                result = self.tools.search(pattern, ".", "*.py")
                if result.success and result.content != "No matches found":
                    context.search_results.append(
                        f"--- Search: {pattern} ---\n{result.content}"
                    )
                    estimated += len(result.content) // 4

        context.estimated_tokens = estimated
        return context

    def assemble_for_patch(
        self,
        diagnosis: str,
        plan: str,
        target_files: list[str],
    ) -> AssembledContext:
        """Assemble context for the patch generation phase.

        Includes:
        - Diagnosis and plan
        - Target files (full content)
        - Related test files
        """
        context = AssembledContext()
        estimated = 0

        # Add diagnosis and plan
        context.files.append(f"--- Diagnosis ---\n{diagnosis}")
        estimated += len(diagnosis) // 4

        context.files.append(f"--- Plan ---\n{plan}")
        estimated += len(plan) // 4

        # Add target files
        for file_path in target_files:
            result = self.tools.read_file(file_path)
            if result.success:
                context.files.append(f"--- {file_path} ---\n{result.content}")
                estimated += len(result.content) // 4

        # Find related test files
        for file_path in target_files:
            test_path = file_path.replace("src/", "tests/test_").replace(".py", ".py")
            result = self.tools.read_file(test_path)
            if result.success:
                context.files.append(f"--- {test_path} ---\n{result.content}")
                estimated += len(result.content) // 4

        context.estimated_tokens = estimated
        return context

    def assemble_for_review(
        self,
        objective: str,
        diff: str,
        changed_files: list[str],
    ) -> AssembledContext:
        """Assemble context for the review phase.

        Includes:
        - Original objective
        - Full diff
        - Changed files
        """
        context = AssembledContext()
        estimated = 0

        context.files.append(f"--- Objective ---\n{objective}")
        estimated += len(objective) // 4

        context.files.append(f"--- Diff ---\n{diff}")
        estimated += len(diff) // 4

        for file_path in changed_files:
            result = self.tools.read_file(file_path)
            if result.success:
                context.files.append(f"--- {file_path} ---\n{result.content}")
                estimated += len(result.content) // 4

        context.estimated_tokens = estimated
        return context

    def assemble_for_failure_analysis(
        self,
        failure_output: str,
        baseline_failures: list[str],
        patch: str,
        edited_files: list[str],
    ) -> AssembledContext:
        """Assemble context for failure analysis.

        Includes:
        - Failure output (truncated to budget)
        - Baseline failures for comparison
        - Patch summary
        - Edited files
        """
        context = AssembledContext()
        estimated = 0

        # Truncate failure output to budget
        lines = failure_output.splitlines()
        if len(lines) > self.budget.max_log_lines:
            # Keep head, tail, and look for failing test sections
            head = lines[:50]
            tail = lines[-50:]
            failure_lines = [
                line for line in lines if "FAILED" in line or "ERROR" in line
            ]
            truncated = "\n".join(head + failure_lines[:50] + tail)
            context.logs.append(f"--- Failure Output (truncated) ---\n{truncated}")
        else:
            context.logs.append(f"--- Failure Output ---\n{failure_output}")
        estimated += len(failure_output) // 4

        context.logs.append(f"--- Baseline Failures ---\n" + "\n".join(baseline_failures))
        estimated += len("\n".join(baseline_failures)) // 4

        context.files.append(f"--- Patch ---\n{patch}")
        estimated += len(patch) // 4

        for file_path in edited_files:
            result = self.tools.read_file(file_path)
            if result.success:
                context.files.append(f"--- {file_path} ---\n{result.content}")
                estimated += len(result.content) // 4

        context.estimated_tokens = estimated
        return context
