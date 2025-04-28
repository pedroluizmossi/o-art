import json
import random
import re
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException, status

from core.db_core import get_db_session
from core.logging_core import setup_logger
from model.workflow_model import Workflow, WorkflowCreate, WorkflowUpdate
from service.workflow_service import (
    WorkflowNotFound,
    create_workflow,
    delete_workflow,
    get_all_workflows,
    get_workflow_by_id,
    update_workflow,
)

logger = setup_logger(__name__)

async def get_all_workflows_handler() -> list[Workflow]:
    """
    Handler to retrieve all workflows.
    """
    try:
        async with get_db_session() as session:
            workflows = await get_all_workflows(session)
        return workflows
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving workflows",
        )

async def get_workflow_by_id_handler(workflow_id: UUID) -> Optional[Workflow]:
    """
    Handler to retrieve a workflow by its ID.
    Returns the workflow or raises an HTTP 404 if not found.
    """
    try:
        async with get_db_session() as session:
            workflow = await get_workflow_by_id(session, workflow_id)
        return workflow
    except WorkflowNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow with ID %s not found." % workflow_id,
        )
    except Exception as e:
        logger.exception("Unhandled error retrieving workflow %s: %s", workflow_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving workflow with ID %s" % workflow_id,
        )


async def create_workflow_handler(workflow_data: WorkflowCreate) -> Workflow:
    """
    Handler to create a new workflow.
    """
    try:
        async with get_db_session() as session:
            workflow = await create_workflow(session, workflow_data)
        return workflow
    except Exception as e:
        logger.exception("Unhandled error creating workflow %s: %s", getattr(workflow_data, "name", ""), e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating workflow",
        )

async def update_workflow_handler(workflow_id: Workflow.id, workflow_update_data: WorkflowUpdate) -> Optional[Workflow]:
    """
    Handler to update a workflow by its ID.
    """
    try:
        workflow_update_data = workflow_update_data.model_dump(exclude_unset=True)
        async with get_db_session() as session:
            workflow = await update_workflow(session, workflow_id, workflow_update_data)
        return workflow
    except WorkflowNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID {workflow_id} not found.",
        )
    except ValueError as ve:
        logger.error("Validation error updating workflow %s: %s", workflow_id, ve)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {ve}",
        )
    except Exception as e:
        logger.exception("Unhandled error updating workflow %s: %s", workflow_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating workflow",
        )

async def delete_workflow_handler(workflow_id: Workflow.id) -> None:
    """
    Handler to delete a workflow by its ID.
    """
    try:
        async with get_db_session() as session:
            await delete_workflow(session, workflow_id)
    except WorkflowNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID {workflow_id} not found.",
        )
    except Exception as e:
        logger.exception("Unhandled error deleting workflow %s: %s", workflow_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting workflow",
        )

def replace_placeholders(obj, workflow_params, params):
    """Função recursiva para substituir placeholders em qualquer estrutura."""
    validate_workflow_params(workflow_params, params)
    # Validate and set the seed if not provided or invalid (0) generate a random one.
    params['seed'] = get_valid_seed(params.get('seed'))
    if isinstance(obj, dict):
        return {k: replace_placeholders(v,workflow_params, params) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_placeholders(item,workflow_params, params) for item in obj]
    elif isinstance(obj, str):
        match = re.fullmatch(r"\{\{(\w+)\}\}", obj)
        if match:
            key = match.group(1)
            return params.get(key, obj)
        else:

            def replacer(m):
                return str(params.get(m.group(1), m.group(0)))

            return re.sub(r"\{\{(\w+)\}\}", replacer, obj)
    else:
        return obj

def validate_workflow_params(workflow_params: dict, user_params: dict):
    """
    Validate if the parameters provided by the user match those defined in the workflow.
    :param workflow_params: Expected parameters from the workflow (from the database)
    :param user_params: Parameters sent by the user (from the API)
    :raise: HTTPException if there is any inconsistency
    """
    extra_keys = [k for k in user_params if k not in workflow_params]

    errors = []
    if extra_keys:
        errors.append(f"Unexpected parameters: {', '.join(extra_keys)}")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="; ".join(errors)
        )



async def load_and_populate_workflow(workflow_id: Workflow.id, params: dict[str, Any]) -> (dict[str, Any], str):
    """
    Load a workflow from the database and populate it with parameters.
    :param workflow_id:
    :param params:
    :return:
    """
    async with get_db_session() as session:
        workflow = await get_workflow_by_id(session, workflow_id)
    if not workflow:
        logger.error("Workflow with ID %s not found.", workflow_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID {workflow_id} not found.",
        )
    workflow_template = workflow.workflow_json
    workflow_params = workflow.parameters
    populated_workflow_dict = replace_placeholders(workflow_template, workflow_params, params)

    logger.debug(
        "Populated workflow for job %s: %s",
        params.get("job_id", "N/A"),
        json.dumps(populated_workflow_dict, indent=2),
    )

    output_node_id = None
    save_image_nodes = []
    for node_id, node_data in populated_workflow_dict.items():
        if (
            isinstance(node_data.get("_meta", {}).get("title"), str)
            and "{{output_node_id}}" in node_data["_meta"]["title"]
        ):
            if output_node_id is None:
                output_node_id = node_id
                logger.info(
                    "Designated output node '{{output_node_id}}' found: Node %s",
                    node_id,
                )
            else:
                logger.warning(
                    "Multiple nodes tagged with '{{output_node_id}}' found in workflow '%s'. Using the first one: %s",
                    workflow_id,
                    output_node_id,
                )
        if node_data.get("class_type") == "SaveImage":
            save_image_nodes.append(node_id)

    if not output_node_id:
        logger.warning(
            "No node explicitly marked with '{{output_node_id}}' in workflow '%s'. Will look for SaveImage nodes.",
            workflow_id,
        )
        if save_image_nodes:
            output_node_id = save_image_nodes[0]
            logger.info("Using first SaveImage node as output: Node %s", output_node_id)
        else:
            logger.error(
                "No '{{output_node_id}}' placeholder and no SaveImage nodes found in workflow '%s'. Cannot determine output.",
                workflow_id,
            )
            raise ValueError(
                f"Workflow '{workflow_id}' does not define an output node ('{{output_node_id}}' or SaveImage type)."
            )

    return populated_workflow_dict, output_node_id

def get_valid_seed(seed):
    """
    Validate and return a seed value if not provided or invalid (0) generate a random one.
    :param seed:
    :return:
    """
    if not seed or seed == 0:
        return random.randint(1, 2**32 - 1)
    return seed
