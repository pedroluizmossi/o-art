from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ParameterDetailEnum(Enum):
    randomize = "randomize"
    min_value = "min_value"
    max_value = "max_value"
    input_or_output = "input_or_output"

class ParameterDetailType(Enum):
    """
    Enum to represent the type of parameter.
    """
    TEXT = "TEXT"
    TEXT_AREA = "TEXT_AREA"
    SELECT = "SELECT"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    IMAGE = "IMAGE"
    FILE = "FILE"
    JSON = "JSON"
    IMAGE_UPLOAD = "IMAGE_UPLOAD"
    BASE64 = "BASE64"

class ParameterDetailInputOrOutputType(Enum):
    """
    Enum to represent the type of parameter for input or output.
    """
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


class ParameterDetail(BaseModel):
    """
    A class to represent the details of a parameter.
    """
    name: str = Field(..., description="Name of the parameter")
    description: str = Field(default=None, description="Description of the parameter")
    example: Any = Field(default=None, description="Example value for the parameter")
    type: ParameterDetailType = Field(
        default=ParameterDetailType.TEXT,
        description="Type of the parameter"
    )
    default: Any = Field(..., description="Default value of the parameter")
    required: bool = Field(..., description="Whether the parameter is required")
    order: int = Field(
        default=None,
        description="Order of the parameter in the workflow"
    )
    input_or_output: ParameterDetailInputOrOutputType = Field(
        default=ParameterDetailInputOrOutputType.INPUT,
        description="Whether the parameter is for input or output"
    )
    node_id: str = Field(
        default=None,
        description="ID of the node to which the parameter belongs"
    )
    min_value: Any = Field(
        default=None,
        description="Minimum value for the parameter, if applicable"
    )
    max_value: Any = Field(
        default=None,
        description="Maximum value for the parameter, if applicable"
    )
    randomize: bool = Field(
        default=False,
        description="Whether the parameter can be randomized"
    )


    @field_validator("name")
    def validate_name(cls, v):
        if not v:
            raise ValueError("Parameter name cannot be empty")
        return v

    @field_validator("order")
    def validate_order(cls, v):
        if v is not None and v < 0 or v == 0:
            raise ValueError("Order must be a positive integer")

    @field_validator("randomize")
    def validate_randomize(cls, v):
        if not isinstance(v, bool):
            raise ValueError("Randomize must be a boolean value")
        return v

