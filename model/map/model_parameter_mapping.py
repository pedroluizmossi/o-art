import pydantic
from pydantic import BaseModel, Field, field_validator

from model.enum.model_type import Model
from model.enum.sampler_type import Sampler


class ParameterDetail(BaseModel):
    ALLOWED: bool = Field(
        default=True,
        description="Whether the model is allowed to be used in this plan"
    )
    WIDTH: int = Field(..., gt=0, description="Width in pixels")
    HEIGHT: int = Field(..., gt=0, description="Height in pixels")
    SAMPLERS: list[Sampler] = Field(..., description="List of supported samplers")
    STEPS: int = Field(default=20, gt=0, description="Number of steps for the model to run")
    CFG: float = Field(default=7.5, gt=0, description="Classifier-Free Guidance scale")
    SEED: int = Field(default=0, description="Random seed for reproducibility")

    @field_validator("STEPS", "CFG", "SEED", "WIDTH", "HEIGHT")
    def validate_positive(cls, value: int) -> int:
        if value < 0:
            raise ValueError("The value must be greater than or equal to zero.")
        return value

    @field_validator("SAMPLERS")
    def validate_samplers(cls, value: list[Sampler]) -> list[Sampler]:
        if not value:
            raise ValueError("The list of samplers cannot be empty.")
        return value


_DEFAULT_WIDTH = 1024
_DEFAULT_HEIGHT = 1024


_example_mapping = {
    model.name: {
        "ALLOWED": True,
        "WIDTH": _DEFAULT_WIDTH,
        "HEIGHT": _DEFAULT_HEIGHT,
        "SAMPLERS": [
            sampler.name for sampler in Sampler
        ],
        "STEPS": 20,
        "CFG": 7.5,
        "SEED": 0
    }
    for model in Model
}


class Parameters(pydantic.RootModel[dict[Model, ParameterDetail]]):
    """
    Maps model names (e.g., "SDXL", "FLUX") to their parameter definitions.
    """
    model_config = {
        "json_schema_extra": {
            "example": _example_mapping
        }
    }