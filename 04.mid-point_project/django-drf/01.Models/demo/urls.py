from django.urls import path
from . import views

urlpatterns = [
    path("products/",      views.products_list_or_create,   name="products-list-or-create"),
    path("products/<int:pk>/", views.product_detail_or_update_or_delete, name="product-detail-or-update-or-delete"),
]
