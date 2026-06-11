from sentence_transformers import SentenceTransformer
import asyncio
from functools import lru_cache

# Load model once at startup -- all-MiniLM-L6-v2 is small (80MB) and fast
@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


async def generate_embedding(text: str) -> list[float]:
    """Generate a 384-dim embedding for the given text."""
    loop = asyncio.get_event_loop()
    model = get_model()
    # Run in thread pool to avoid blocking the event loop
    embedding = await loop.run_in_executor(
        None, lambda: model.encode(text, normalize_embeddings=True)
    )
    return embedding.tolist()
