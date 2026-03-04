from services.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfig
from pathlib import Path

async def matrix_workflow(file_path, config):
    orchestrator = WorkflowOrchestrator(
        config=WorkflowConfig(...)
    )

    result = orchestrator.execute_complete_workflow(Path(file_path))
    return result