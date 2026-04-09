from django.http import JsonResponse

from myapp.models import Item


def list_items(request: object) -> JsonResponse:
    """Return all active items as JSON."""
    items = list(Item.objects.filter(is_active=True).values("name", "description"))
    return JsonResponse({"items": items})
