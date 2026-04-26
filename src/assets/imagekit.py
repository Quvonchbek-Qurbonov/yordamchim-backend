from imagekitio import ImageKit

from src.core.config import settings

client = ImageKit(
    private_key=settings.IMAGE_KIT_PRIVATE
)
