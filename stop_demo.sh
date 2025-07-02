#!/bin/bash

# ================================================================
# SAFA Global Demo Stop Script
# Safely stop the demo environment
# ================================================================

echo "🛑 Stopping SAFA Global Demo..."

# Kill Django development server
pkill -f "python.*manage.py.*runserver" && echo "✅ Django server stopped" || echo "⚠️  No Django server running"

# Remove PID file if it exists
if [ -f ".demo_server.pid" ]; then
    rm .demo_server.pid
    echo "✅ Cleaned up PID file"
fi

echo "🎯 Demo stopped successfully!"
echo ""
echo "To restart the demo, run: bash demo_setup.sh"
