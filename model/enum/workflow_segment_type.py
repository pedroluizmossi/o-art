from enum import Enum


class WorkflowSegment(Enum):
    UPSCALE = "upscale"
    IMAGE_TO_IMAGE = "image_to_image"
    TEXT_TO_IMAGE = "text_to_image"
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"