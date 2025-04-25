from rest_framework import serializers
from .models import Ticket

class TicketSerializer(serializers.ModelSerializer):
    media = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'description', 'media',
            'outlet', 'raised_by', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

