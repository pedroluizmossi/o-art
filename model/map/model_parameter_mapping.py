import random

import pydantic
from pydantic import BaseModel, Field, field_validator

from model.enum.model_type import Model
from model.enum.sampler_type import Sampler


class ParameterDetail(BaseModel):
    ALLOWED: bool | None = Field(
        default=None,
        description="Whether the model is allowed to be used in this plan"
    )
    POSITIVE_PROMPT: str | None = Field(
        default=None,
        description="Prompt to be used for the model"
    )
    NEGATIVE_PROMPT: str | None = Field(
        default=None,
        description="Negative prompt to be used for the model"
    )
    WIDTH: int | None = Field(default=None, description="Width in pixels")
    HEIGHT: int | None = Field(default=None, description="Height in pixels")
    SAMPLERS: list[Sampler] | None = Field(default=None, description="List of supported samplers")
    STEPS: int | None = Field(default=None, description="Number of steps for the model to run")
    CFG: float | None = Field(default=None, description="Classifier-Free Guidance scale")
    SEED: int | None = Field(
        default_factory=lambda: random.randint(1, 2**32 - 1),
        description="Random seed for reproducibility"
    )
    MODEL_ID: Model | None = Field(
        default=None,
        description="Model ID to be used for the generation"
    )

    @field_validator("POSITIVE_PROMPT")
    def validate_prompts(cls, value: str) -> str:
        if value is None or not value.strip():
            raise ValueError("Positive prompt cannot be empty.")
        return value

    @field_validator("WIDTH", "HEIGHT")
    def validate_dimensions(cls, value: int) -> int:
        if value is not None and value <= 0:
            raise ValueError("Width and height must be positive integers.")
        return value
    
    @field_validator("SEED")
    def validate_seed(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Seed must be a non-negative integer or 0 for random generation.")
        if value == 0 or value is None:
            value = random.randint(1, 2**32 - 1)
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