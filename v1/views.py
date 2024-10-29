from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from .models import Company, Outlet
from .serializers import OutletSerializer
from django.contrib.auth import get_user_model
from .models import Outlet, OutletAccess

@api_view(['POST'])
def create_outlet(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    outlet_data = request.data
    outlet_data['company'] = company.id
    serializer = OutletSerializer(data=outlet_data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def grant_access(request, outlet_id, user_id):
    outlet = get_object_or_404(Outlet, id=outlet_id)
    user = get_object_or_404(get_user_model(), id=user_id)

    permissions = request.data.get('permissions', {})

    outlet_access, created = OutletAccess.objects.update_or_create(
        user=user,
        outlet=outlet,
        defaults={'permissions': permissions}
    )

    if created:
        return Response({"message": "Access granted successfully.", "permissions": permissions}, status=status.HTTP_201_CREATED)
    else:
        return Response({"message": "Access updated successfully.", "permissions": permissions}, status=status.HTTP_200_OK)