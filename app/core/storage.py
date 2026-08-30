"""Module for storage-related functionality."""

import os
import uuid
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET_NAME = os.getenv("SUPABASE_STORAGE_BUCKET")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_image(file_bytes: bytes, original_filename: str, folder: str) -> str:
    """
    Upload une image vers Supabase Storage et renvoie son URL publique.
    folder : sous-dossier logique, ex "stack", "projets", "profile", "articles"
    """
    extension = original_filename.split(".")[-1]
    unique_name = f"{folder}/{uuid.uuid4()}.{extension}"

    supabase.storage.from_(BUCKET_NAME).upload(
        path=unique_name,
        file=file_bytes,
        file_options={"content-type": f"image/{extension}"},
    )

    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(unique_name)
    return public_url
