from myapp.models import Item


class TestItem:
    """Tests for the Item model."""

    def test_create_item(self) -> None:
        """Item can be created with required fields."""
        item = Item.objects.create(name="Test Item")
        assert item.name == "Test Item"
        assert item.is_active is True
        assert item.description == ""

    def test_str_representation(self) -> None:
        """String representation returns the item name."""
        item = Item(name="Widget")
        assert str(item) == "Widget"

    def test_filter_active_items(self) -> None:
        """Filtering by is_active works correctly."""
        Item.objects.create(name="Active", is_active=True)
        Item.objects.create(name="Inactive", is_active=False)

        active = Item.objects.filter(is_active=True)
        assert active.count() == 1
        assert active.first().name == "Active"

    def test_item_with_description(self) -> None:
        """Item can be created with a description."""
        item = Item.objects.create(name="Described", description="A useful item")
        item.refresh_from_db()
        assert item.description == "A useful item"
