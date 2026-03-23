from django.core.paginator import Paginator

class PaginationService:
    """
    Reusable pagination utility using Django 6's get_page() —
    handles out of range, invalid, and negative page numbers automatically.

    Usage:
        result = PaginationService.paginate(
            queryset=notifications,
            request=request,
            serializer=cls._serialize,
        )
        return ResponseProvider.success(data=result)

    Query params:
        ?page=1        — page number (default: 1)
        ?page_size=20  — records per page (default: 20, max: 100)
    """
    DEFAULT_PAGE_SIZE=20
    MAX_PAGE_SIZE=100

    @classmethod
    def paginate(cls, queryset, request,serializer)-> dict:

        """

        Args:
            queryset:   Django QuerySet or list to paginate.
            request:    HTTP request — reads ?page and ?page_size.
            serializer: Callable that serializes a single object → dict.

        Returns:
            dict with pagination metadata and serialized results.
        """

        # ── Read and validate query params ────────────────
        try:
            # reads ?page_size=20 from URL → 20
            page_size = int(request.GET.get('page_size', cls.DEFAULT_PAGE_SIZE))
        except (ValueError, TypeError):
            page_size = cls.DEFAULT_PAGE_SIZE

        # caps it at 100 so no one can request 10000 records
        page_size = max(1, min(page_size, cls.MAX_PAGE_SIZE))
        # caps it at 100 so no one can request 10000 records
        page_number = request.GET.get('page',1)

        # ── Paginate using get_page() ─────────────────────
        # get_page() handles: non-integer, negative, out of range
        # — never raises, always returns a valid page
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        return {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page.number,
            "page_size": page_size,
            "has_next": page.has_next(),
            "has_previous": page.has_previous(),
            "next_page": page.next_page_number() if page.has_next() else None,
            "previous_page": page.previous_page_number() if page.has_previous() else None,
            "results": [serializer(obj) for obj in page.object_list],
        }