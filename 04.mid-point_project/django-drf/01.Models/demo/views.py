from rest_framework.decorators import api_view 
from rest_framework.response import Response
from .models import Product 
from .serializers import ProductModelSerializer
from rest_framework import status


@api_view(["GET", "POST"])
def products_list_or_create(request):
    if request.method == "GET":
        products = Product.objects.all()
        serializer = ProductModelSerializer(products, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        serializer = ProductModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()#will auto call create() method of serializer and save to db
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(["GET", "PUT" ,"DELETE"])
def product_detail_or_update_or_delete(request,pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = ProductModelSerializer(product)
        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = ProductModelSerializer(product, data=request.data)#instance argument is the existing object to update, data argument is the new data to update with
        if serializer.is_valid():
            serializer.save() #will auto call update() method of serializer and save to db
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)