from rest_framework import generics, permissions
from .models import CustomUser
from .serializers import MCPUserSerializer

class MCPUserListView(generics.ListAPIView):
    """
    MCP-compliant API endpoint for listing users.
    Only returns active users for public/supporter access.
    """
    queryset = CustomUser.objects.filter(is_active=True)
    serializer_class = MCPUserSerializer
    permission_classes = [permissions.AllowAny]
