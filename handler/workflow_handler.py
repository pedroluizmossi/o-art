import re
from typing import Any, Optional, Union
from uuid import UUID

from fastapi import HTTPException, status

from core.db_core import get_db_session
from core.logging_core import setup_logger
from handler.plan_handler import get_plan_by_id_handler
from model.map.model_parameter_mapping import ParameterDetail
from model.plan_model import Plan
from model.workflow_model import Workflow, WorkflowCreate, WorkflowUpdate
from service.workflow_service import (
    create_workflow,
    delete_workflow,
    get_all_workflows,
    get_workflow_by_id,
    update_workflow,
)

logger = setup_logger(__name__)

def handle_exception(detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
    """
    Utility function to handle exceptions and raise HTTPException.
    """
    def wrapper(func):
        async def wrapped(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"{detail}: {e}")
                raise HTTPException(status_code=status_code, detail=detail) from e
        return wrapped
    return wrapper

@handle_exception("Error retrieving workflows")
async def get_all_workflows_handler() -> list[Workflow]:
    async with get_db_session() as session:
        return await get_all_workflows(session)

@handle_exception("Error retrieving workflow")
async def get_workflow_by_id_handler(workflow_id: UUID) -> Optional[Workflow]:
    async with get_db_session() as session:
        return await get_workflow_by_id(session, workflow_id)

@handle_exception("Error creating workflow")
async def create_workflow_handler(workflow_data: WorkflowCreate) -> Workflow:
    async with get_db_session() as session:
        return await create_workflow(session, workflow_data)

@handle_exception("Error updating workflow")
async def update_workflow_handler(
        workflow_id: UUID,
        workflow_update_data: WorkflowUpdate
) -> Optional[Workflow]:
    workflow_update_data = workflow_update_data.model_dump(exclude_unset=True)
    async with get_db_session() as session:
        return await update_workflow(session, workflow_id, workflow_update_data)

@handle_exception("Error deleting workflow")
async def delete_workflow_handler(workflow_id: UUID) -> None:
    async with get_db_session() as session:
        await delete_workflow(session, workflow_id)

async def replace_placeholders(
    obj: Union[dict, list, str],
    workflow_params: dict,
    params: dict,
    user_params_detail: Optional[ParameterDetail] = None,
    plan_id: Optional[UUID] = None,
    workflow_model_type: Optional[str] = None
) -> Union[dict, list, str]:
    """
    Replace placeholders in the workflow template with actual parameter values.
    """
    if user_params_detail is None:
        await validate_workflow_params(workflow_params, params, plan_id, workflow_model_type)
        user_params_detail = ParameterDetail(**params)

    def get_param_value(key: str) -> Any:
        return getattr(user_params_detail, key, workflow_params.get(key, f"{{{{{key}}}}}"))

    if isinstance(obj, dict):
        return {k: await replace_placeholders(v, workflow_params, params, user_params_detail)
                for k, v in obj.items()}
    elif isinstance(obj, list):
        return [await replace_placeholders(item, workflow_params, params, user_params_detail)
                for item in obj]
    elif isinstance(obj, str):
        return re.sub(r"\{\{(\w+)\}\}", lambda m: str(get_param_value(m.group(1))), obj)
    return obj

async def validate_user_params(user_params: dict, plan_params: dict):
    """
    Validate if the user parameters exceed the maximum values defined in the plan.
    """
    for key, max_value in plan_params.items():
        if key in user_params and user_params[key] > max_value:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Parameter '{key}' exceeds maximum value of {max_value} for plan.",
            )

async def validate_workflow_params(
    workflow_params: dict,
    user_params: dict,
    plan_id: Optional[UUID] = None,
    workflow_model_type: Optional[str] = None
):
    """
    Validate if the parameters provided by the user match those defined in the workflow.
    """
    plan: Optional[Plan] = await get_plan_by_id_handler(plan_id) if plan_id else None
    await validate_user_params(user_params, plan.model_parameters[workflow_model_type])
    extra_keys = [k for k in user_params if k not in workflow_params]
    if extra_keys:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unexpected parameters: {', '.join(extra_keys)}"
        )

async def load_and_populate_workflow(
    workflow_id: UUID,
    params: dict[str, Any],
    plan_id: Optional[UUID] = None
) -> tuple[dict[str, Any], str]:
    """
    Load a workflow from the database and populate it with parameters.
    """
    async with get_db_session() as session:
        workflow = await get_workflow_by_id(session, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID {workflow_id} not found.",
        )

    populated_workflow_dict = await replace_placeholders(
        obj=workflow.workflow_json,
        workflow_params=workflow.parameters,
        params=params,
        plan_id=plan_id,
        workflow_model_type=workflow.model_type.value
    )

    output_node_id = next(
        (node_id for node_id, node_data in populated_workflow_dict.items()
         if node_data.get("_meta", {}).get("title") == "{{output_node_id}}"),
        None
    )

    if not output_node_id:
        save_image_nodes = [
            node_id for node_id, node_data in populated_workflow_dict.items()
            if node_data.get("class_type") == "SaveImage"
        ]
        if save_image_nodes:
            output_node_id = save_image_nodes[0]
        else:
            raise ValueError(f"Workflow '{workflow_id}' does not define an output node.")

    return populated_workflow_dict, output_node_id