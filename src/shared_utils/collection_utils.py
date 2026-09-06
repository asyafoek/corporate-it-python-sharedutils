
def deduplicate_dicts(items, key_func=None):
    """
    Verwijder duplicaten uit een lijst van dicts.

    Parameters
    ----------
    items : list[dict]
    key_func : callable, optional
        Functie die een unieke sleutel teruggeeft.

    Returns
    -------
    list[dict]
    """
    seen = set()
    result = []

    for item in items:
        key = key_func(item) if key_func else tuple(sorted(item.items()))

        if key not in seen:
            seen.add(key)
            result.append(item)

    return result
