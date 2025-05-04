from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.logging_core import setup_logger
from model.image_model import Image

logger = setup_logger(__name__)

async def create_image(session: AsyncSession, image_data: Image) -> Image:
    """Adds a new image to the database."""
    try:
        if not image_data.created_at:
            image_data.created_at = datetime.now(timezone.utc)
        image_data.updated_at = image_data.created_at

        session.add(image_data)
        await session.commit()
        await session.refresh(image_data)
        logger.info("Image created successfully: %s", image_data.id)
        return image_data
    except Exception as e:
        await session.rollback()
        logger.exception("Error creating image %s: %s", getattr(image_data, "name", ""), e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating image",
        ) from e

async def get_all_images(session: AsyncSession) -> list[Image]:
    """Retrieves all images from the database."""
    try:
        statement = select(Image)
        images = await session.exec(statement)
        images = images.all()
        return images
    except Exception as e:
        logger.exception("Error retrieving all images: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving all images",
        ) from e

async def get_all_images_by_user_id(session: AsyncSession, user_id: UUID) -> list[Image]:
    """Retrieves all images for a specific user from the database."""
    try:
        statement = select(Image).where(Image.user_id == user_id)
        images = await session.exec(statement)
        images = images.all()
        return images
    except Exception as e:
        logger.exception("Error retrieving images for user %s: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving images for user {user_id}",
        ) from e

async def get_image_by_id(session: AsyncSession, image_id: UUID) -> Optional[Image]:
    """Retrieves an image by its ID."""
    try:
        statement = select(Image).where(Image.id == image_id)
        image = await session.exec(statement)
        image = image.first()
        return image
    except Exception as e:
        logger.exception("Error retrieving image by ID %s: %s", image_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving image with ID {image_id}",
        ) from e