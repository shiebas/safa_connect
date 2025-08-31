from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ParkingZone, ParkingSpace, ParkingAllocation
from .serializers import ParkingZoneSerializer, ParkingSpaceSerializer
from events.models import InternationalMatch
import qrcode
import base64
from io import BytesIO

@api_view(['GET'])
def parking_data_api(request):
    """API endpoint to return parking zone and space data."""
    zones = ParkingZone.objects.all()
    spaces = ParkingSpace.objects.all()

    zone_serializer = ParkingZoneSerializer(zones, many=True)
    space_serializer = ParkingSpaceSerializer(spaces, many=True)

    return Response({
        'zones': zone_serializer.data,
        'spaces': space_serializer.data
    })

@login_required
def parking_allocation_detail(request, allocation_id):
    """Display the details of a parking allocation, including a map and QR code."""
    allocation = get_object_or_404(ParkingAllocation, id=allocation_id, user=request.user)
    context = {
        'allocation': allocation,
    }
    return render(request, 'parking/parking_allocation_detail.html', context)

@login_required
def allocate_parking(request, match_id):
    """Allocate a parking space for a user for a specific match."""
    if request.method == 'POST':
        match = get_object_or_404(InternationalMatch, id=match_id)
        user = request.user

        # Check if the user already has a parking allocation for this match
        if ParkingAllocation.objects.filter(user=user, event=match).exists():
            return JsonResponse({'status': 'error', 'message': 'You already have a parking space allocated for this event.'}, status=400)

        # Find an available parking space
        parking_space = ParkingSpace.objects.filter(is_available=True).first()

        if parking_space:
            # Allocate the parking space
            parking_allocation = ParkingAllocation.objects.create(
                user=user,
                space=parking_space,
                event=match,
            )

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f"SAFA Parking: {parking_allocation.id}")
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            parking_allocation.qr_code = qr_code_base64
            parking_allocation.save()

            # Mark the parking space as unavailable
            parking_space.is_available = False
            parking_space.save()

            return JsonResponse({'status': 'success', 'parking_allocation_id': parking_allocation.id})
        else:
            return JsonResponse({'status': 'error', 'message': 'No available parking spaces.'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)