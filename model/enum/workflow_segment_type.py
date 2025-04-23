from enum import Enum


class WorkflowSegment(Enum):
    UPSCALE = "UPSCALE"
    IMAGE_TO_IMAGE = "IMAGE_TO_IMAGE"
    TEXT_TO_IMAGE = "TEXT_TO_IMAGE"
    TEXT_TO_VIDEO = "TEXT_TO_VIDEO"
    IMAGE_TO_VIDEO = "IMAGE_TO_VIDEO"