"""
Mobile App API Views for SAFA Connect
Handles authentication and user data for the mobile application
"""

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import transaction

from .serializers import CustomUserSerializer
from .models import CustomUser
from membership.models import Member
from membership.serializers import MemberSerializer


class MobileLoginView(APIView):
    """
    Mobile app login endpoint
    Returns user data and authentication token
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'success': False,
                'message': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        user = authenticate(request, email=email, password=password)
        
        if not user:
            return Response({
                'success': False,
                'message': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'success': False,
                'message': 'User account is disabled'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        # Get member data if user is a member
        try:
            member = Member.objects.get(user=user)
            member_data = MemberSerializer(member, context={'request': request}).data
        except Member.DoesNotExist:
            member_data = None
        
        # Prepare response data
        response_data = {
            'token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': getattr(user, 'role', None),
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            },
            'member': member_data,
            'login_time': timezone.now().isoformat(),
        }
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'data': response_data
        })


class MobileLogoutView(generics.GenericAPIView):
    """
    Mobile app logout endpoint
    Deletes the authentication token
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Delete the token
            request.user.auth_token.delete()
            return Response({
                'success': True,
                'message': 'Logout successful'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Logout failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileUserProfileView(generics.RetrieveUpdateAPIView):
    """
    Mobile app user profile endpoint
    Get and update user profile information
    """
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get(self, request, *args, **kwargs):
        user = self.get_object()
        user_data = self.get_serializer(user).data
        
        # Get member data if user is a member
        try:
            member = Member.objects.get(user=user)
            member_data = MemberSerializer(member, context={'request': request}).data
        except Member.DoesNotExist:
            member_data = None
        
        return Response({
            'success': True,
            'data': {
                'user': user_data,
                'member': member_data
            }
        })


class MobileMemberProfileView(generics.RetrieveAPIView):
    """
    Mobile app member profile endpoint
    Get detailed member information
    """
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user = self.request.user
        try:
            return Member.objects.get(user=user)
        except Member.DoesNotExist:
            return None
    
    def get(self, request, *args, **kwargs):
        member = self.get_object()
        
        if not member:
            return Response({
                'success': False,
                'message': 'User is not a registered member'
            }, status=status.HTTP_404_NOT_FOUND)
        
        member_data = self.get_serializer(member, context={'request': request}).data
        
        return Response({
            'success': True,
            'data': member_data
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mobile_change_password(request):
    """
    Mobile app change password endpoint
    """
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not old_password or not new_password:
        return Response({
            'success': False,
            'message': 'Both old and new passwords are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    
    # Verify old password
    if not user.check_password(old_password):
        return Response({
            'success': False,
            'message': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate new password
    if len(new_password) < 8:
        return Response({
            'success': False,
            'message': 'New password must be at least 8 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Change password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'success': True,
        'message': 'Password changed successfully'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mobile_dashboard_data(request):
    """
    Mobile app dashboard data endpoint
    Returns summary information for the dashboard
    """
    user = request.user
    
    try:
        member = Member.objects.get(user=user)
        
        # Get member's current status and information
        dashboard_data = {
            'member_id': member.id,
            'safa_id': member.safa_id,
            'full_name': member.get_full_name(),
            'status': member.status,
            'role': member.role,
            'current_club': member.current_club.name if member.current_club else None,
            'current_season': member.current_season.season_year if member.current_season else None,
            'registration_complete': member.registration_complete,
            'has_outstanding_invoices': member.invoices.filter(
                status__in=['PENDING', 'OVERDUE', 'PARTIALLY_PAID']
            ).exists(),
            'last_activity': member.modified.isoformat() if member.modified else None,
        }
        
        return Response({
            'success': True,
            'data': dashboard_data
        })
        
    except Member.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User is not a registered member'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def mobile_health_check(request):
    """
    Mobile app health check endpoint
    Returns basic system status
    """
    return Response({
        'success': True,
        'data': {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'service': 'SAFA Connect Mobile API'
        }
    })
