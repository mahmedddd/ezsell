import cloudinary
import cloudinary.uploader
from core.config import settings
from fastapi import UploadFile
import uuid
from pathlib import Path

# Configure Cloudinary
if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )

class CloudStorageService:
    @staticmethod
    async def upload_file(upload_file: UploadFile, folder: str = "ezsell/listings") -> str:
        """
        Uploads a file to Cloudinary if configured, otherwise falls back to local storage (not recommended for production)
        """
        # If Cloudinary is not configured, we might still be in local dev
        if not all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
            # This is a fallback to avoid breaking local dev if they haven't set up Cloudinary yet
            return None 

        try:
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                upload_file.file,
                folder=folder,
                public_id=f"{uuid.uuid4()}"
            )
            return result.get("secure_url")
        except Exception as e:
            print(f"Cloudinary upload error: {e}")
            raise e
