"""Workflow graph — LangGraph StateGraph definition.

The workflow is a directed graph with deterministic routing decisions.
Any node may exit directly to the verdict node with a Blocked or Failed outcome.
"""

from hivecode.workflow.nodes import (
    classify_failure,
    deliver,
    diagnose_and_plan,
    evaluate_checks,
    final_verdict,
    generate_patch,
    independent_review,
    intake_and_validate,
    prepare_workspace,
    scope_and_policy_gate,
    validate_in_sandbox,
)


def create_workflow_graph() -> dict:
    """Create the LangGraph StateGraph for task execution.

    Graph structure:
        intake → prepare → diagnose → patch → scope_gate → validate → evaluate
            ├─ all pass → review → verdict → deliver
            ├─ mandatory fail → classify → repair (patch) or stop
            └─ any node → verdict (blocked/failed)
    """
    # TODO: Implement LangGraph StateGraph
    # This requires langgraph to be installed
    # For now, return a placeholder

    # The graph will be:
    # 1. intake_and_validate
    # 2. prepare_workspace
    # 3. diagnose_and_plan
    # 4. generate_patch (attempt n)
    # 5. scope_and_policy_gate
    # 6. validate_in_sandbox
    # 7. evaluate_checks
    # 8. classify_failure (if checks failed)
    # 9. independent_review (if checks passed)
    # 10. final_verdict
    # 11. deliver

    # Routing decisions (nodes 5, 7, 8, 10) are deterministic code.
    # Any node may exit directly to node 10 with a Blocked or Failed outcome.

    return {
        "nodes": {
            "intake": intake_and_validate,
            "prepare": prepare_workspace,
            "diagnose": diagnose_and_plan,
            "patch": generate_patch,
            "scope_gate": scope_and_policy_gate,
            "validate": validate_in_sandbox,
            "evaluate": evaluate_checks,
            "classify": classify_failure,
            "review": independent_review,
            "verdict": final_verdict,
            "deliver": deliver,
        },
        "edges": [
            ("intake", "prepare"),
            ("prepare", "diagnose"),
            ("diagnose", "patch"),
            ("patch", "scope_gate"),
            ("scope_gate", "validate"),
            ("validate", "evaluate"),
            ("evaluate", "review"),  # all pass
            ("evaluate", "classify"),  # mandatory fail
            ("classify", "patch"),  # repair
            ("classify", "verdict"),  # stop
            ("review", "verdict"),
            ("verdict", "deliver"),
        ],
    }
