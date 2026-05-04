# src/corporate_it_sharedutils/strings.py
def slugify(text: str) -> str:
    return text.lower().strip().replace(" ", "-")
