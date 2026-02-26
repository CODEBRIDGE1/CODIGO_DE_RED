#!/bin/bash
# Quick validation that all migrations work
# Usage: ./scripts/validate_all.sh

set -e

echo "=================================="
echo "🔍 VALIDACIÓN RÁPIDA DE MIGRACIONES"
echo "=================================="

cd "$(dirname "$0")/.."

echo ""
echo "1️⃣ Verificando que contenedores estén corriendo..."
docker-compose ps | grep healthy || {
    echo "⚠️  Servicios no están corriendo. Levantando..."
    docker-compose up -d
    sleep 10
}

echo ""
echo "2️⃣ Verificando estado actual de migraciones..."
CURRENT=$(docker-compose exec -T api alembic current 2>&1 | grep -oP '[a-f0-9]{12}' | head -1)
HEAD=$(docker-compose exec -T api alembic heads 2>&1 | grep -oP '[a-f0-9]{12}' | head -1)

echo "   Current: $CURRENT"
echo "   Head:    $HEAD"

if [ "$CURRENT" != "$HEAD" ]; then
    echo "   ⚠️  No está en HEAD, ejecutando upgrade..."
    docker-compose exec api alembic upgrade head
else
    echo "   ✅ Ya está en HEAD"
fi

echo ""
echo "3️⃣ Ejecutando validaciones de seguridad..."
docker-compose exec api python scripts/check_migrations.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ TODAS LAS VALIDACIONES PASARON"
    echo "=================================="
    echo ""
    echo "Tu sistema está listo para:"
    echo "  ✅ Deployments de producción"
    echo "  ✅ Rollbacks seguros"
    echo "  ✅ CI/CD automático"
    echo ""
else
    echo ""
    echo "=================================="
    echo "❌ ALGUNAS VALIDACIONES FALLARON"
    echo "=================================="
    echo ""
    echo "Revisa el reporte arriba y corrige los problemas."
    echo "Consulta: backend/docs/MIGRATIONS.md"
    echo ""
    exit 1
fi
