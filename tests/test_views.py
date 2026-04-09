from django.test import Client
from django.urls import reverse

from myapp.models import Item


class TestListItems:
    """Tests for the list_items view."""

    def test_returns_active_items(self) -> None:
        """Only active items appear in the response."""
        Item.objects.create(name="Visible", is_active=True)
        Item.objects.create(name="Hidden", is_active=False)

        client = Client()
        response = client.get(reverse("list_items"))

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Visible"

    def test_empty_list(self) -> None:
        """Returns empty list when no items exist."""
        client = Client()
        response = client.get(reverse("list_items"))

        assert response.status_code == 200
        assert response.json() == {"items": []}
