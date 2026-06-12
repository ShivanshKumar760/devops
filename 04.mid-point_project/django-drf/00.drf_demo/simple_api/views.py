from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Create your views here.

ITEMS = [
    {"id": 1, "name": "Laptop",  "price": 50000},
    {"id": 2, "name": "Monitor", "price": 15000},
]

@api_view(["GET"])
def items_list(request):
    return Response(ITEMS)


@api_view(["POST"])
def create_item(request):
    name = request.data.get("name")
    price = request.data.get("price")
    if not name or not price:
        return Response({"error": "Name and price are required."}, status=status.HTTP_400_BAD_REQUEST)
    new_item = {
        "id": len(ITEMS) + 1,
        "name": name,
        "price": price
    }

    ITEMS.append(new_item)
    return Response(new_item, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def item_detail(request,pk):
    #Find the item or 404
    global ITEMS
    item = next((item for item in ITEMS if item["id"]==pk),None)
    if item is None:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(item)
    
    if request.method == "PUT":
        item["name"] = request.data.get("name")
        item["price"] = request.data.get("price")
        return Response(item)
    
    if request.method == "PATCH":
        # Partial update — only provided fields change
        if "name"  in request.data: item["name"]  = request.data["name"]
        if "price" in request.data: item["price"] = request.data["price"]
        return Response(item)

    if request.method == "DELETE":
        ITEMS.remove(item)
        return Response(status=status.HTTP_204_NO_CONTENT)