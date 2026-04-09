import json

from django.test import RequestFactory

from myapp.models import Item
from myapp.views import list_items


class TestListItems:
    """Tests for the list_items view."""

    def test_returns_active_items(self) -> None:
        """Only active items appear in the response."""
        Item.objects.create(name="Visible", is_active=True)
        Item.objects.create(name="Hidden", is_active=False)

        factory = RequestFactory()
        request = factory.get("/items/")
        response = list_items(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Visible"

    def test_empty_list(self) -> None:
        """Returns empty list when no items exist."""
        factory = RequestFactory()
        request = factory.get("/items/")
        response = list_items(request)

        assert response.status_code == 200
        assert json.loads(response.content) == {"items": []}
