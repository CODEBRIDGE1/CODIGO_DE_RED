#!/bin/bash
# Test script para clasificación de empresas

echo "=================================="
echo "TEST: Clasificación de Empresas"
echo "=================================="

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
API_URL="http://localhost:8001"
LOGIN_ENDPOINT="$API_URL/api/v1/auth/login"
COMPANIES_ENDPOINT="$API_URL/api/v1/companies"

# Credenciales de prueba
EMAIL="admin@tenant-demo.com"
PASSWORD="Admin123!"

echo ""
echo "1️⃣  LOGIN..."
echo "--------------------"
LOGIN_RESPONSE=$(curl -s -X POST "$LOGIN_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}✗ Error en login${NC}"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Login exitoso${NC}"
echo "Token: ${TOKEN:0:20}..."

echo ""
echo "2️⃣  OBTENIENDO EMPRESAS..."
echo "--------------------"
COMPANIES_RESPONSE=$(curl -s -X GET "$COMPANIES_ENDPOINT" \
  -H "Authorization: Bearer $TOKEN")

COMPANY_ID=$(echo $COMPANIES_RESPONSE | python3 -c "import sys, json; data = json.load(sys.stdin); print(data[0]['id'] if data else '')" 2>/dev/null)

if [ -z "$COMPANY_ID" ]; then
  echo -e "${RED}✗ No se encontraron empresas${NC}"
  echo "Response: $COMPANIES_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Empresa encontrada: ID=$COMPANY_ID${NC}"

echo ""
echo "3️⃣  CREANDO CLASIFICACIÓN..."
echo "--------------------"

# Payload para clasificación
PAYLOAD='{
  "tipo_centro_carga": "TIPO_A",
  "justificacion": "Test de clasificación automática"
}'

echo "Endpoint: $API_URL/api/v1/compliance/companies/$COMPANY_ID/classification"
echo "Payload: $PAYLOAD"

CLASSIFICATION_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "$API_URL/api/v1/compliance/companies/$COMPANY_ID/classification" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

HTTP_CODE=$(echo "$CLASSIFICATION_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$CLASSIFICATION_RESPONSE" | sed '$d')

echo ""
echo "HTTP Status: $HTTP_CODE"
echo "Response:"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
  echo ""
  echo -e "${GREEN}✓ Clasificación creada exitosamente${NC}"
elif [ "$HTTP_CODE" -eq 400 ]; then
  echo ""
  echo -e "${YELLOW}⚠ Empresa ya tiene clasificación (esperado si ya se ejecutó antes)${NC}"
  
  echo ""
  echo "4️⃣  ACTUALIZANDO CLASIFICACIÓN (PUT)..."
  echo "--------------------"
  
  UPDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT \
    "$API_URL/api/v1/compliance/companies/$COMPANY_ID/classification" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
  
  HTTP_CODE=$(echo "$UPDATE_RESPONSE" | tail -n 1)
  RESPONSE_BODY=$(echo "$UPDATE_RESPONSE" | sed '$d')
  
  echo "HTTP Status: $HTTP_CODE"
  echo "Response:"
  echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
  
  if [ "$HTTP_CODE" -eq 200 ]; then
    echo ""
    echo -e "${GREEN}✓ Clasificación actualizada exitosamente${NC}"
  else
    echo ""
    echo -e "${RED}✗ Error al actualizar clasificación${NC}"
    exit 1
  fi
else
  echo ""
  echo -e "${RED}✗ Error al crear clasificación${NC}"
  
  # Mostrar detalles del error si es un error de validación
  ERROR_DETAIL=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('detail', 'Unknown error'))" 2>/dev/null)
  echo "Error: $ERROR_DETAIL"
  
  exit 1
fi

echo ""
echo "5️⃣  OBTENIENDO CLASIFICACIÓN..."
echo "--------------------"

GET_RESPONSE=$(curl -s -X GET \
  "$API_URL/api/v1/compliance/companies/$COMPANY_ID/classification" \
  -H "Authorization: Bearer $TOKEN")

echo "$GET_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$GET_RESPONSE"

echo ""
echo "=================================="
echo -e "${GREEN}✓ TODAS LAS PRUEBAS PASARON${NC}"
echo "=================================="
