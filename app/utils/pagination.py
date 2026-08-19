from flask import request

PAGE_DEFAULT = 1
PER_PAGE_DEFAULT = 10
PER_PAGE_MAX = 100


def get_page_params(default_page: int = PAGE_DEFAULT, default_per_page: int = PER_PAGE_DEFAULT, max_per_page: int = PER_PAGE_MAX):
    """Parse and clamp pagination query params (?page=&per_page=).

    Returns:
        tuple: (page, per_page) or (None, None) if neither was supplied in query params.
    """
    raw_page = request.args.get('page', None, type=int)
    raw_per_page = request.args.get('per_page', None, type=int)

    if raw_page is None and raw_per_page is None:
        return None, None

    page = max(default_page, raw_page) if raw_page is not None else default_page
    per_page = min(max_per_page, max(1, raw_per_page)) if raw_per_page is not None else default_per_page
    return page, per_page
