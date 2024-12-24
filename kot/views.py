from django.shortcuts import render

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from drf_yasg.utils import swagger_auto_schema

from v1.models import (
    Order
)

from .serializers import (
    OrderSerializer
)
# Create your views here.

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve orders with PENDING status.",
    responses={200: OrderSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_orders_for_kot(request):
    # You can filter the orders as needed, for example by status or outlet
    orders = Order.objects.filter(status='PENDING')  # Example filter, adjust as needed

    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)




@swagger_auto_schema(
    method='patch',
    operation_description="Change the status of an order to 'PROCESSING'.",
    responses={
        200: OrderSerializer(),
        404: 'Order not found'
    }
)
@api_view(['PATCH'])
@permission_classes([AllowAny])
def change_order_status_to_processing(request, order_id):
    try:
        # Fetch the order by ID
        order = Order.objects.get(id=order_id)

        # Update the status to 'PROCESSING'
        order.status = 'PROCESSING'
        order.save()

        # Serialize the updated order
        serializer = OrderSerializer(order)

        # Return the success response in the desired format
        return Response({
            'error': False,
            'detail': 'Order status updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({
            'error': True,
            'detail': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    



@swagger_auto_schema(
    method='patch',
    operation_description="Change the status of an order to 'COMPLETED'.",
    responses={
        200: OrderSerializer(),
        404: 'Order not found'
    }
)
@api_view(['PATCH'])
@permission_classes([AllowAny])
def change_order_status_to_completed(request, order_id):
    try:
        # Fetch the order by ID
        order = Order.objects.get(id=order_id)

        # Update the status to 'COMPLETED'
        order.status = 'COMPLETED'
        order.save()

        # Serialize the updated order
        serializer = OrderSerializer(order)

        # Return the success response in the desired format
        return Response({
            'error': False,
            'detail': 'Order status updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({
            'error': True,
            'detail': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)