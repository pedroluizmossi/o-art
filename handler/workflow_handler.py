import random
import re
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException, status

from core.db_core import get_db_session
from core.logging_core import setup_logger
from handler.model_handler import get_model_by_id_handler
from model.map.model_parameter_mapping import ParameterDetailEnum
from model.model_model import Model
from model.workflow_model import Workflow, WorkflowCreate, WorkflowUpdate
from service.workflow_service import (
    create_workflow,
    delete_workflow,
    get_all_workflows,
    get_workflow_by_id,
    update_workflow,
)

logger = setup_logger(__name__)

def preprocess_workflow_params(workflow_params):
    workflow_defaults = {p["name"]: p.get("default") for p in workflow_params}
    allowed_params = set(workflow_defaults.keys())
    return workflow_defaults, allowed_params

async def handle_model_parameters(params, allowed_params, workflow_defaults):
    model: Model = await get_model_by_id_handler(params["MODEL_ID"])
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model with ID {params['MODEL_ID']} not found.",
        )
    model_params = {param["name"]: param.get("default") for param in model.parameters}
    allowed_params.update(model_params.keys())
    workflow_defaults.update(model_params)

    for param in model.parameters:
        if param.get("randomize"):
            min_value = param.get("min_value")
            max_value = param.get("max_value")
            if min_value is not None and max_value is not None:
                params[param["name"]] = random.randint(min_value, max_value)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Model parameter '{param['name']}' has randomize=True "
                        f"but no min_value or max_value defined."
                    ),
                )

def validate_extra_params(params, allowed_params):
    extra_params = set(params.keys()) - allowed_params
    if extra_params:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extra parameters provided: {', '.join(extra_params)}",
        )

def randomize_workflow_params(workflow_params, params):
    for param in workflow_params:
        if param.get(ParameterDetailEnum.randomize):
            min_value = param.get(ParameterDetailEnum.min_value)
            max_value = param.get(ParameterDetailEnum.max_value)
            if min_value is not None and max_value is not None:
                params[param["name"]] = random.randint(min_value, max_value)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Parameter '{param['name']}' has randomize=True "
                        f"but no min_value or max_value defined."
                    ),
                )

def create_placeholder_replacer(params, workflow_defaults):
    placeholder_pattern = re.compile(r"{{(.*?)}}")

    def replacer(value):
        def replace_match(match):
            placeholder = match.group(1)
            if placeholder in params:
                return str(params[placeholder])
            elif placeholder in workflow_defaults:
                return str(workflow_defaults[placeholder])
            return match.group(0)

        return placeholder_pattern.sub(replace_match, value)

    return replacer

async def process_object(obj, replacer):
    if isinstance(obj, dict):
        return {key: await process_object(value, replacer) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [await process_object(item, replacer) for item in obj]
    elif isinstance(obj, str):
        return replacer(obj)
    return obj

async def replace_placeholders(obj, workflow_params, params, plan_id, workflow_model_type):
    workflow_defaults, allowed_params = preprocess_workflow_params(workflow_params)

    if "MODEL_ID" in params:
        await handle_model_parameters(params, allowed_params, workflow_defaults)

    validate_extra_params(params, allowed_params)
    randomize_workflow_params(workflow_params, params)

    replacer = create_placeholder_replacer(params, workflow_defaults)
    return await process_object(obj, replacer)

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
        workflow_params = workflow.parameters,
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workflow '{workflow_id}' does not define an output node."
            )

    return populated_workflow_dict, output_node_id


async def create_workflow_handler(
    workflow_data: WorkflowCreate,
) -> Workflow:
    """
    Create a new workflow.
    """
    async with get_db_session() as session:
        workflow = await create_workflow(session, workflow_data)
    return workflow

async def update_workflow_handler(
    workflow_id: UUID,
    workflow_data: WorkflowUpdate,
) -> Workflow:
    """
    Update an existing workflow.
    """
    async with get_db_session() as session:
        workflow = await update_workflow(session, workflow_id, workflow_data)
    return workflow

async def delete_workflow_handler(
    workflow_id: UUID,
) -> None:
    """
    Delete a workflow by ID.
    """
    async with get_db_session() as session:
        await delete_workflow(session, workflow_id)

async def get_all_workflows_handler() -> list[Workflow]:
    """
    Get all workflows.
    """
    async with get_db_session() as session:
        workflows = await get_all_workflows(session)
    return workflows

async def get_workflow_by_id_handler(
    workflow_id: UUID,
) -> Optional[Workflow]:
    """
    Get a workflow by ID.
    """
    async with get_db_session() as session:
        workflow = await get_workflow_by_id(session, workflow_id)
    return workflow