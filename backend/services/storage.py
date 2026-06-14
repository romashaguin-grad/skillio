import uuid as uuid_lib
from config import settings


async def upload_file(contents: bytes, filename: str, user_id) -> str:
    try:
        from supabase import create_client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        path = f"{user_id}/{uuid_lib.uuid4()}_{filename}"
        response = supabase.storage.from_("resumes").upload(
            path,
            contents,
            {"content-type": "application/pdf"},
        )
        print(f"Supabase upload response: {response}")
        url = supabase.storage.from_("resumes").get_public_url(path)
        print(f"Supabase public URL: {url}")
        return url
    except Exception as e:
        print(f"Storage upload error: {type(e).__name__}: {e}")
        return ""