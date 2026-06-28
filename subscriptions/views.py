import razorpay
from django.conf import settings
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from v1.models import Plan
from .models import SubscriptionTransaction

@swagger_auto_schema(
    method='post',
    operation_description="Create a Razorpay order for plan subscription",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['plan_id'],
        properties={
            'plan_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'email': openapi.Schema(type=openapi.TYPE_STRING, description="Required if user not logged in"),
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Alternative to email if not logged in"),
        }
    ),
    responses={200: "Order created successfully", 400: "Bad Request"}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_subscription_order(request):
    plan_id = request.data.get('plan_id')
    email = request.data.get('email')
    phone_number = request.data.get('phone_number')

    if not plan_id:
        return Response({"error": True, "message": "plan_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
    if not email and not phone_number and not request.user.is_authenticated:
        return Response({"error": True, "message": "Either email or phone_number is required for unauthenticated users."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        return Response({"error": True, "message": "Invalid plan_id."}, status=status.HTTP_404_NOT_FOUND)

    # Initialize Razorpay client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Create order
    # amount is in paise
    amount_in_paise = int(plan.plan_price * 100)
    
    order_data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": f"plan_rcptid_{plan.id}",
    }

    try:
        razorpay_order = client.order.create(data=order_data)
        
        # Save transaction
        transaction = SubscriptionTransaction.objects.create(
            email=email,
            phone_number=phone_number,
            plan=plan,
            razorpay_order_id=razorpay_order['id'],
            amount=plan.plan_price,
            user=request.user if request.user.is_authenticated else None
        )
        
        return Response({
            "error": False,
            "order_id": razorpay_order['id'],
            "amount": razorpay_order['amount'],
            "currency": razorpay_order['currency'],
            "key": settings.RAZORPAY_KEY_ID
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": True, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_description="Verify Razorpay payment signature",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature'],
        properties={
            'razorpay_order_id': openapi.Schema(type=openapi.TYPE_STRING),
            'razorpay_payment_id': openapi.Schema(type=openapi.TYPE_STRING),
            'razorpay_signature': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={200: "Payment verified successfully", 400: "Bad Request"}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_subscription_payment(request):
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_signature = request.data.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return Response({"error": True, "message": "Missing payment details."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        transaction = SubscriptionTransaction.objects.get(razorpay_order_id=razorpay_order_id)
    except SubscriptionTransaction.DoesNotExist:
        return Response({"error": True, "message": "Invalid razorpay_order_id."}, status=status.HTTP_404_NOT_FOUND)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
        
        # Mark as success
        transaction.status = 'SUCCESS'
        transaction.razorpay_payment_id = razorpay_payment_id
        transaction.razorpay_signature = razorpay_signature
        transaction.save()

        # If user is already authenticated (logged in user buying plan), we can assign it immediately.
        # But for unauthenticated users, they will be assigned during the signup flow.
        
        return Response({"error": False, "message": "Payment verified successfully."}, status=status.HTTP_200_OK)
        
    except razorpay.errors.SignatureVerificationError:
        transaction.status = 'FAILED'
        transaction.save()
        return Response({"error": True, "message": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": True, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def subscription_flow_docs(request):
    return render(request, 'subscriptions/flow_docs.html')
