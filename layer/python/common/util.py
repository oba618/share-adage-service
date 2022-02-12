def is_empty(item: any) -> bool:
    """空の判定

    Args:
        item (any): アイテム

    Returns:
        bool: 空か否か
    """
    if item == {}:
        return True

    if item == []:
        return True

    if item == '':
        return True

    if item == None:
        return True

    return False