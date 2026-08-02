import os
import uuid

MEDIA_DIR = "media"

from src.models.exercise import ExerciseType
from src.bot.formatters import parse_set_input, format_set_text

def generate_image_path(extension: str = ".jpg") -> str:
    """
    Generates a unique path for saving an image in the media directory.
    """
    if not os.path.exists(MEDIA_DIR):
        os.makedirs(MEDIA_DIR)
    filename = f"{uuid.uuid4().hex}{extension}"
    return os.path.join(MEDIA_DIR, filename)
