#!/bin/bash

echo "=========================================="
echo "PLATAFORMA CÓDIGO DE RED - Inicio"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que existe .env
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado${NC}"
    echo "Copiando .env.example a .env..."
    cp .env.example .env
    echo -e "${GREEN}✓ Archivo .env creado${NC}"
    echo ""
fi

echo "Paso 1: Levantando servicios con Docker Compose..."
docker-compose up -d

echo ""
echo "Esperando 15 segundos para que los servicios inicien..."
sleep 15

echo ""
echo "Paso 2: Verificando estado de los servicios..."
docker-compose ps

echo ""
echo "Paso 3: Ejecutando migraciones de base de datos..."
docker-compose exec -T api alembic upgrade head

echo ""
echo "Paso 4: Ejecutando seed de datos iniciales..."
docker-compose exec -T api python scripts/seed.py

echo ""
echo "=========================================="
echo -e "${GREEN}✓ ¡Plataforma iniciada correctamente!${NC}"
echo "=========================================="
echo ""
echo "Accesos:"
echo "  • Frontend:    http://localhost:5173"
echo "  • API Docs:    http://localhost:8000/docs"
echo "  • MinIO:       http://localhost:9001"
echo ""
echo "Usuarios de prueba:"
echo "  • Superadmin:    superadmin@codebridge.com / SuperAdmin123!"
echo "  • Tenant Admin:  admin@tenant-demo.com / Admin123!"
echo ""
echo "Ver logs:"
echo "  docker-compose logs -f api"
echo ""
echo "Detener servicios:"
echo "  docker-compose down"
echo "=========================================="
