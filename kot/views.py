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
    Customer,
    Outlet,
    Employee,
    OutletAccess,
    KOTDevice,
)

from rest_framework.authtoken.models import Token

from .serializers import (
    OrderSerializer,
    CustomUserCounterLoginSerializer
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
    operation_description="KOT device login with device binding",
    manual_parameters=[
        openapi.Parameter('device_id', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('outlet_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    ],
    request_body=CustomUserCounterLoginSerializer,
    responses={
        200: openapi.Response(description="KOT login success"),
        400: "Bad Request",
        403: "Forbidden"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def kot_login(request):
    try:
        device_id = request.GET.get("device_id")

        if not device_id:
            return Response({
                "error": True,
                "message": "device_id is required"
            }, status=400)

        serializer = CustomUserCounterLoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "error": True,
                "message": "Invalid credentials"
            }, status=400)

        user = serializer.validated_data["user"]
        employee = Employee.objects.get(user=user)

        # ✅ Device logic
        device = KOTDevice.objects.filter(device_id=device_id).first()

        if device:
            # mark login
            device.is_logged_in = True
            device.registered_by = employee
            device.save()
        else:
            # register new device
            device = KOTDevice.objects.create(
                device_id=device_id,
                registered_by=employee,
                is_logged_in=True
            )

        # ✅ Token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "error": False,
            "message": "KOT login successful",
            "token": token.key,
            "device_id": device.device_id,
            "is_logged_in": device.is_logged_in
        })

    except Exception as e:
        return Response({
            "error": True,
            "details": str(e)
        }, status=500)









@swagger_auto_schema(
    method='post',
    operation_description="Deregister KOT device",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['outlet_id'],
        properties={
            'outlet_id': openapi.Schema(type=openapi.TYPE_INTEGER)
        }
    ),
    responses={200: openapi.Response(description="Device removed")}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def deregister_kot_device(request):
    try:
        device_id = request.data.get("device_id")

        if not device_id:
            return Response({
                "error": True,
                "message": "device_id is required"
            }, status=400)

        device = KOTDevice.objects.filter(device_id=device_id).first()

        if not device:
            return Response({
                "error": True,
                "message": "Device not found"
            }, status=404)

        device.delete()

        return Response({
            "error": False,
            "message": "Device deregistered successfully"
        })

    except Exception as e:
        return Response({
            "error": True,
            "details": str(e)
        }, status=500)




@swagger_auto_schema(
    method='get',
    operation_description="Check KOT device login status",
    manual_parameters=[
        openapi.Parameter('device_id', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('outlet_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    ],
    responses={
        200: openapi.Response(description="KOT status fetched"),
        404: "Device not found"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def check_kot_status(request):
    try:
        device_id = request.GET.get("device_id")

        if not device_id:
            return Response({
                "error": True,
                "message": "device_id is required"
            }, status=400)

        try:
            device = KOTDevice.objects.get(device_id=device_id)
        except KOTDevice.DoesNotExist:
            return Response({
                "error": True,
                "message": "Device not registered"
            }, status=404)

        return Response({
            "error": False,
            "device_id": device.device_id,
            "is_logged_in": device.is_logged_in,
            "is_active": device.is_active
        })

    except Exception as e:
        return Response({
            "error": True,
            "details": str(e)
        }, status=500)







