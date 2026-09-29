def page_count(total, size):
    if not isinstance(total, int) or isinstance(total, bool):
        raise ValueError("total must be an integer, excluding booleans")
    if not isinstance(size, int) or isinstance(size, bool):
        raise ValueError("size must be an integer, excluding booleans")
    if total < 0:
        raise ValueError("total must be non-negative")
    if size <= 0:
        raise ValueError("size must be positive")

    return (total + size - 1) // size