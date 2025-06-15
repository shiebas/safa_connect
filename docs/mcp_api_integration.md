# MCP API Endpoint Integration

## Overview
This document describes the process of adding a non-disruptive, MCP-compliant API endpoint to the project.

### 1. Serializer
- Created `accounts/serializers.py` with `MCPUserSerializer` for the `CustomUser` model.

### 2. View
- Created `accounts/views_mcp.py` with `MCPUserListView` (Django REST Framework ListAPIView).
- Only returns active users for public/supporter access.

### 3. URL Routing
- Updated `accounts/urls.py` to add:
  - `path('api/mcp/users/', MCPUserListView.as_view(), name='mcp_user_list')`

### 4. Testing
- No existing endpoints or code were changed.
- You can test the new endpoint at `/accounts/api/mcp/users/`.

### 5. Next Steps
- Gradually add more MCP-compliant endpoints as needed.
- Update documentation as you expand MCP support.

---

_Last updated: 15 June 2025_
