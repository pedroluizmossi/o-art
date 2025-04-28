import pydantic
from pydantic import BaseModel, Field

from model.enum.workflow_segment_type import WorkflowSegment


class WorkflowSegmentDetail(BaseModel):
    allowed: bool = Field(
        default=True,
        description="Whether the segment is allowed in the current plan."
    )

_example_mapping = {
    segment.name: {
        "allowed": True
    }
    for segment in WorkflowSegment
}


class WorkflowSegment(pydantic.RootModel[dict[WorkflowSegment, WorkflowSegmentDetail]]):
    """
    Maps model names (e.g., "SDXL", "FLUX") to their parameter definitions.
    """
    model_config = {
        "json_schema_extra": {
            "example": _example_mapping
        }
    }