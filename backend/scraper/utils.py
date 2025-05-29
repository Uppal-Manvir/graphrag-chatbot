# utils.py
#Used when splitting pages into chunks to categorize each chunk so when we seach we dont seach all pages only 
#domain closest to the question 
def infer_domain_from_url(url: str) -> str:
    u = url.lower()
    if "/recipe" in u or "/recipes" in u or "flavours" in u or "blog" in u:
        return "recipe"
    if "/privacy-policy" in u or "/terms" in u or "about" in u or "sustainability" in u:
        return "policy"
    # fallback everything else to product
    return "product"
