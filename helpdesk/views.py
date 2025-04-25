from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes,permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .models import Ticket
from .serializers import TicketSerializer

from users.models import CustomUser
from v1.models import Outlet

from rest_framework.parsers import MultiPartParser, FormParser

# Create your views here.

@swagger_auto_schema(
    method='post',
    request_body=TicketSerializer,
    responses={
        201: TicketSerializer,
        400: 'Bad Request',
    },
)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([AllowAny])
def create_ticket(request, user_id, outlet_id):
    """
    API view to raise a new ticket.
    """
    try:
        user = CustomUser.objects.get(id=user_id)
        outlet = Outlet.objects.get(id=outlet_id)
    except (CustomUser.DoesNotExist, Outlet.DoesNotExist) as e:
        return Response({
            'error': True,
            'details': str(e)
        }, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    data['raised_by'] = user.id
    data['outlet'] = outlet.id

    serializer = TicketSerializer(data=data)
    if serializer.is_valid():
        ticket = serializer.save()

        # Build full media URL if media exists
        ticket_data = serializer.data.copy()
        if ticket.media:
            ticket_data['media'] = request.build_absolute_uri(ticket.media.url)

        return Response({
            'error': False,
            'details': 'Ticket created successfully.',
            'ticket': ticket_data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'error': True,
        'details': 'Invalid data.',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)













@swagger_auto_schema(
    method='get',
    responses={
        200: TicketSerializer(many=True),
    },
)
@api_view(['GET'])
def list_tickets(request, outlet_id):
    """
    API view to list all tickets for a specific outlet.
    """
    try:
        outlet = Outlet.objects.get(id=outlet_id)  # Get the outlet by outlet_id
    except Outlet.DoesNotExist:
        return Response({
            'error': True,
            'details': 'Outlet not found.'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        tickets = Ticket.objects.filter(outlet=outlet)  # Filter tickets by outlet
        
        # Include media URL if present
        ticket_data = []
        for ticket in tickets:
            ticket_info = TicketSerializer(ticket).data
            # Add media information to each ticket (if media exists)
            ticket_info['media'] = [media.url for media in ticket.media.all()] if ticket.media.exists() else []
            ticket_data.append(ticket_info)

        return Response({
            'error': False,
            'details': 'Tickets retrieved successfully.',
            'tickets': ticket_data
        })