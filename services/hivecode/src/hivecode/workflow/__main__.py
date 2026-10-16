"""Workflow runner CLI entry point.

Usage: python -m hivecode.workflow <task_id>
"""

import asyncio
import sys
from uuid import UUID

from hivecode.workflow.runner import WorkflowRunner


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m hivecode.workflow <task_id>")
        sys.exit(1)

    task_id = UUID(sys.argv[1])
    runner = WorkflowRunner()
    result = await runner.run(task_id)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
