from django.urls import path

from myapp.views import list_items

urlpatterns: list = [
    path("items/", list_items, name="list_items"),
]
