from django.shortcuts import render

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from v1.models import (
    Order,
    OrderItem,
    FCMToken,
    Customer,
    Outlet
)

from .serializers import (
    OrderSerializer,
    FCMTokenSerializer
)
# Create your views here.

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all the pending and comfirmed orders of a specific outlet.",
    responses={200: OrderSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_orders_for_kot(request, outlet_id):
    orders = Order.objects.filter(
        outlet_id=outlet_id,
        status__in=['PENDING', 'CONFIRMED']
    ).order_by('-order_date')

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
        
        




@swagger_auto_schema(
    method='post',
    operation_summary="Register or update FCM token for an outlet",
    operation_description="""
This endpoint registers or updates an FCM token for a specific outlet.
- If the token already exists and is the same, it does nothing.
- If a different token exists, it updates it.
- If no token exists, it creates a new one.
""",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['token'],
        properties={
            'token': openapi.Schema(type=openapi.TYPE_STRING, description='The FCM token')
        }
    ),
    responses={
        200: openapi.Response(description="Token already registered or updated"),
        201: openapi.Response(description="Token registered successfully"),
        400: openapi.Response(description="Invalid input"),
        404: openapi.Response(description="Outlet not found"),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_fcm_token(request, outlet_id):
    try:
        outlet = Outlet.objects.get(id=outlet_id)
    except Outlet.DoesNotExist:
        return Response({'error':True, 'detail': 'Outlet not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = FCMTokenSerializer(data=request.data)
    if serializer.is_valid():
        new_token = serializer.validated_data['token']

        existing_token = FCMToken.objects.filter(outlet=outlet).first()

        if existing_token:
            if existing_token.token == new_token:
                # Same token already exists for this outlet
                return Response({'error':False, 'detail': 'Token already registered successfully'}, status=status.HTTP_200_OK)
            else:
                # Different token exists — update it
                existing_token.token = new_token
                existing_token.save()
                return Response({'error':False, 'detail': 'Token updated successfully'}, status=status.HTTP_200_OK)
        else:
            # No token exists for this outlet — create it
            FCMToken.objects.create(outlet=outlet, token=new_token)
            return Response({'error':False, 'detail': 'Token registered successfully'}, status=status.HTTP_201_CREATED)
    
    return Response({'error':True, 'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)