import uuid as uuid_lib
from supabase import create_client
from config import settings

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
BUCKET = "resumes"


async def upload_file(contents: bytes, filename: str, user_id) -> str:
    try:
        path = f"{user_id}/{uuid_lib.uuid4()}_{filename}"
        response = supabase.storage.from_(BUCKET).upload(
            path,
            contents,
            {"content-type": "application/pdf"},
        )
        print(f"Supabase upload response: {response}")
        url = supabase.storage.from_(BUCKET).get_public_url(path)
        print(f"Supabase public URL: {url}")
        return url
    except Exception as e:
        print(f"Storage upload error: {type(e).__name__}: {e}")
        return ""