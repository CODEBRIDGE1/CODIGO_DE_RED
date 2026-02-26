#!/bin/bash
# Test CORS configuration
# Usage: ./scripts/test_cors.sh [server_ip]

SERVER_IP="${1:-31.97.210.250}"
API_PORT="${2:-8001}"

echo "=================================="
echo "🌐 TESTING CORS CONFIGURATION"
echo "=================================="
echo ""

echo "📍 Testing server: $SERVER_IP:$API_PORT"
echo ""

# Test 1: Check if API is accessible
echo "1️⃣ Testing API accessibility..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP:$API_PORT/docs 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ API is accessible (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "000" ]; then
    echo "   ❌ Cannot connect to API (connection refused or timeout)"
    echo "   💡 Check if:"
    echo "      - Docker containers are running: docker-compose ps"
    echo "      - Port $API_PORT is open in firewall"
    echo "      - API is listening on 0.0.0.0: docker-compose logs api | grep listening"
    exit 1
else
    echo "   ⚠️  API returned HTTP $HTTP_CODE"
fi

echo ""

# Test 2: Check CORS headers from localhost
echo "2️⃣ Testing CORS from localhost origin..."
CORS_RESPONSE=$(curl -s -I \
    -H "Origin: http://localhost:5173" \
    -H "Access-Control-Request-Method: GET" \
    http://$SERVER_IP:$API_PORT/api/v1/auth/me 2>/dev/null)

if echo "$CORS_RESPONSE" | grep -qi "Access-Control-Allow-Origin"; then
    ALLOWED_ORIGIN=$(echo "$CORS_RESPONSE" | grep -i "Access-Control-Allow-Origin" | cut -d' ' -f2- | tr -d '\r')
    echo "   ✅ CORS header present: $ALLOWED_ORIGIN"
else
    echo "   ❌ No CORS header found"
    echo "   💡 API might not have CORS configured"
fi

echo ""

# Test 3: Check CORS headers from server IP origin
echo "3️⃣ Testing CORS from server IP origin..."
CORS_RESPONSE=$(curl -s -I \
    -H "Origin: http://$SERVER_IP:5173" \
    -H "Access-Control-Request-Method: GET" \
    http://$SERVER_IP:$API_PORT/api/v1/auth/me 2>/dev/null)

if echo "$CORS_RESPONSE" | grep -qi "Access-Control-Allow-Origin"; then
    ALLOWED_ORIGIN=$(echo "$CORS_RESPONSE" | grep -i "Access-Control-Allow-Origin" | cut -d' ' -f2- | tr -d '\r')
    echo "   ✅ CORS header present: $ALLOWED_ORIGIN"
    
    if [ "$ALLOWED_ORIGIN" = "*" ]; then
        echo "   ⚠️  WARNING: CORS is allowing ALL origins (*)"
        echo "   💡 This is OK for development, but should be restricted in production"
    fi
else
    echo "   ❌ No CORS header found for server IP origin"
    echo "   💡 Add http://$SERVER_IP:5173 to CORS_ORIGINS in .env"
fi

echo ""

# Test 4: Check environment configuration
echo "4️⃣ Checking container environment..."
CORS_ENV=$(docker-compose exec -T api printenv CORS_ORIGINS 2>/dev/null || echo "NOT_SET")
ENV=$(docker-compose exec -T api printenv ENVIRONMENT 2>/dev/null || echo "NOT_SET")

echo "   ENVIRONMENT: $ENV"
echo "   CORS_ORIGINS: $CORS_ENV"

if [ "$CORS_ENV" = "NOT_SET" ]; then
    echo "   ⚠️  CORS_ORIGINS not set in container"
    echo "   💡 Update .env file and restart: docker-compose restart api"
fi

echo ""

# Test 5: Show current configuration
echo "5️⃣ Current .env configuration:"
if [ -f .env ]; then
    echo "   CORS_ORIGINS=$(grep CORS_ORIGINS .env | cut -d'=' -f2-)"
    echo "   ENVIRONMENT=$(grep -E '^ENVIRONMENT=' .env | cut -d'=' -f2-)"
else
    echo "   ❌ .env file not found"
    echo "   💡 Copy from: cp .env.example .env"
fi

echo ""
echo "=================================="
echo "📝 RECOMMENDATIONS"
echo "=================================="
echo ""

if [ "$ENV" = "development" ]; then
    echo "✅ Development mode detected - CORS should allow all origins"
    echo ""
    echo "To enable production mode:"
    echo "1. Edit .env:"
    echo "   ENVIRONMENT=production"
    echo "   CORS_ORIGINS=http://localhost:5173,http://$SERVER_IP:5173"
    echo ""
    echo "2. Restart API:"
    echo "   docker-compose restart api"
else
    echo "🔒 Production mode detected"
    echo ""
    echo "Make sure CORS_ORIGINS includes all required origins:"
    echo "   CORS_ORIGINS=http://localhost:5173,http://$SERVER_IP:5173,https://yourdomain.com"
    echo ""
    echo "After updating .env, restart:"
    echo "   docker-compose restart api"
fi

echo ""
echo "=================================="
