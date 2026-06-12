from django.urls import path
from . import views

urlpatterns = [
    path("items/",      views.items_list,   name="item-list"),
    path("items/create/", views.create_item, name="item-create"),
    path("items/<int:pk>/", views.item_detail, name="item-detail"),
]
