def map_category(description: str, rules: list[dict]) -> tuple[str, str]:
    """
    Return (category, subcategory) for a transaction description.
    Rules are evaluated in order; first match wins.
    Falls back to ("Uncategorized", "").
    """
    lowered = description.lower()
    for rule in rules:
        keyword = rule.get("keyword", "").lower()
        if keyword and keyword in lowered:
            return rule.get("category", "Uncategorized"), rule.get("subcategory", "")
    return "Uncategorized", ""
