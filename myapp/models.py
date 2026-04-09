from django.db import models


class Item(models.Model):
    """A simple model to demonstrate that migrations and tests work."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Return the item name."""
        return self.name
