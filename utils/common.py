import json
from django.http import QueryDict


def parse_request_body(request) -> dict:
    """Parse raw request data based on content type."""
    try:
        content_type = request.META.get('CONTENT_TYPE', '')

        if 'application/json' in content_type:
            return json.loads(request.body) if request.body else {}
        elif 'multipart/form-data' in content_type:
            return request.POST.dict()
        elif request.method == 'GET':
            return request.GET.dict()
        elif request.method == 'POST':
            return request.POST.dict()
        return {}
    except json.JSONDecodeError:
        return {}


def clean_data(
    data: dict,
    required_fields: set = None,
    allowed_fields: set = None,
) -> dict:
    """
    Sanitize and validate a data dictionary.
    - Strips whitespace from strings
    - Converts empty strings to None
    - Filters to allowed_fields if provided
    - Raises ValueError if required_fields are missing
    """
    cleaned = {}

    for key, value in data.items():
        if allowed_fields and key not in allowed_fields:
            continue
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                value = None
        cleaned[key] = value

    if required_fields:
        missing = [f for f in required_fields if not cleaned.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

    return cleaned

def get_clean_request_data(
    request,
    required_fields: set = None,
    allowed_fields: set = None,
) -> dict:
    """
    One-shot helper: parse the request then clean the result.
    Use this in views.
    required_fields — fields that must be present or we reject the request. e.g. you can't submit an expense without amount.
    allowed_fields — fields that are permitted to be processed. Anything outside this list gets silently dropped even if the user sends it.
    """
    raw = parse_request_body(request)
    return clean_data(raw, required_fields=required_fields, allowed_fields=allowed_fields)