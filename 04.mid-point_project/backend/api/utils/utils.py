import re
import uuid


def slugify(text: str) -> str:
    """Convert store name to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def generate_store_link(store_name: str) -> str:
    slug = slugify(store_name)
    unique_suffix = uuid.uuid4().hex[:6]
    return f"{slug}-{unique_suffix}"