import pydantic
from pydantic import BaseModel, Field

from model.enum.workflow_type import Workflow


class WorkflowTypeDetail(BaseModel):
    allowed: bool = Field(
        default=True,
        description="Whether the segment is allowed in the current plan."
    )

_example_mapping = {
    worflow_type.name: {
        "allowed": True
    }
    for worflow_type in Workflow
}


class WorkflowType(pydantic.RootModel[dict[Workflow, WorkflowTypeDetail]]):
    """
    Maps model names (e.g., "SDXL", "FLUX") to their parameter definitions.
    """
    model_config = {
        "json_schema_extra": {
            "example": _example_mapping
        }
    }