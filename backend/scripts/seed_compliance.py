"""
Seed data for Compliance Matrix - Tabla 1.1.A
Requerimientos aplicables a los Centros de Carga
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models in correct order to ensure relationships are registered
from app.db.base import Base
from app.models.license import License
from app.models.tenant import Tenant
from app.models.role import Role
from app.models.permission import Permission
from app.models.module import Module
from app.models.security_level import SecurityLevel
from app.models.user import User
from app.models.company import Company
from app.models.audit_log import AuditLog
from app.models.obligation import Obligation
from app.models.project import Project
from app.models.evidence import Evidence
from app.models.quote import Quote
from app.models.document import Document
from app.models.compliance import (
    ComplianceRequirement,
    ComplianceRule,
    TipoCentroCarga,
    EstadoAplicabilidad,
    CompanyClassification
)
from app.db.session import AsyncSessionLocal


async def seed_requirements():
    """Seed compliance requirements from Tabla 1.1.A"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if already seeded by counting rows directly
            from sqlalchemy import text
            result = await db.execute(text("SELECT COUNT(*) FROM compliance_requirements"))
            count = result.scalar()
            if count > 0:
                print(f"Compliance requirements already seeded ({count} requirements found)")
                return
        except Exception as e:
            print(f"Note: {e}")
            # Table might not exist or first run, continue with seeding

        # Define requirements
        requirements = [
            {
                "codigo": "2.1",
                "nombre": "Tensión",
                "descripcion": "Control de tensión en el punto de interconexión",
                "orden": 1
            },
            {
                "codigo": "2.2",
                "nombre": "Frecuencia",
                "descripcion": "Control de frecuencia del sistema",
                "orden": 2
            },
            {
                "codigo": "2.3",
                "nombre": "Corto circuito",
                "descripcion": "Nivel de corto circuito simétrico y asimétrico",
                "orden": 3
            },
            {
                "codigo": "2.4",
                "nombre": "Factor de Potencia",
                "descripcion": "Mantenimiento del factor de potencia",
                "orden": 4
            },
            {
                "codigo": "2.5",
                "nombre": "Protecciones",
                "descripcion": "Sistemas de protección eléctrica",
                "orden": 5
            },
            {
                "codigo": "2.6",
                "nombre": "Control",
                "descripcion": "Sistema de control del centro de carga",
                "orden": 6
            },
            {
                "codigo": "2.7",
                "nombre": "Intercambio de información",
                "descripcion": "Intercambio de información conforme a manuales TIC",
                "orden": 7
            },
            {
                "codigo": "2.8",
                "nombre": "Calidad de la potencia",
                "descripcion": "Requisitos de calidad de la potencia eléctrica",
                "orden": 8
            },
            {
                "codigo": "2.8.1",
                "nombre": "Distorsión Armónica",
                "descripcion": "Límites de distorsión armónica total (THD)",
                "parent_codigo": "2.8",
                "orden": 9
            },
            {
                "codigo": "2.8.2",
                "nombre": "Fluctuaciones de Tensión",
                "descripcion": "Control de flicker y fluctuaciones de tensión",
                "parent_codigo": "2.8",
                "orden": 10
            },
            {
                "codigo": "2.8.3",
                "nombre": "Desbalance",
                "descripcion": "Control de desbalance de tensión y corriente",
                "parent_codigo": "2.8",
                "orden": 11
            }
        ]

        # Create requirements
        requirement_map = {}
        for req_data in requirements:
            parent_id = None
            if "parent_codigo" in req_data:
                parent_id = requirement_map.get(req_data["parent_codigo"])
            
            req = ComplianceRequirement(
                codigo=req_data["codigo"],
                nombre=req_data["nombre"],
                descripcion=req_data.get("descripcion"),
                parent_id=parent_id,
                orden=req_data["orden"],
                is_active=True
            )
            db.add(req)
            await db.flush()
            requirement_map[req.codigo] = req.id

        await db.commit()
        print(f"✅ Created {len(requirements)} compliance requirements")

        # Define applicability rules for each tipo
        rules = [
            # TIPO_A (Media Tensión < 1 MW)
            {"requirement": "2.1", "tipo": TipoCentroCarga.TIPO_A, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.2", "tipo": TipoCentroCarga.TIPO_A, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.3", "tipo": TipoCentroCarga.TIPO_A, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.4", "tipo": TipoCentroCarga.TIPO_A, "estado": EstadoAplicabilidad.NO_APLICA},
            {"requirement": "2.5", "tipo": TipoCentroCarga.TIPO_A, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.6", "tipo": TipoCentroCarga.TIPO_A, "estado": EstadoAplicabilidad.APLICA_RDC, "notas": "Aplica solo para RDC"},
            {"requirement": "2.7", "tipo": TipoCentroCarga.TIPO_A, "estado": EstadoAplicabilidad.APLICA_TIC, "notas": "Conforme a Manual TIC"},
            {"requirement": "2.8.1", "tipo": TipoCentroCarga.TIPO_A, "estado": EstadoAplicabilidad.NO_APLICA},
            {"requirement": "2.8.2", "tipo": TipoCentroCarga.TIPO_A, "estado": EstadoAplicabilidad.NO_APLICA},
            {"requirement": "2.8.3", "tipo": TipoCentroCarga.TIPO_A, "estado": EstadoAplicabilidad.APLICA},

            # TIPO_B (Media Tensión >= 1 MW)
            {"requirement": "2.1", "tipo": TipoCentroCarga.TIPO_B, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.2", "tipo": TipoCentroCarga.TIPO_B, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.3", "tipo": TipoCentroCarga.TIPO_B, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.4", "tipo": TipoCentroCarga.TIPO_B, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.5", "tipo": TipoCentroCarga.TIPO_B, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.6", "tipo": TipoCentroCarga.TIPO_B, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.7", "tipo": TipoCentroCarga.TIPO_B, "estado": EstadoAplicabilidad.APLICA_TIC, "notas": "Conforme a Manual TIC"},
            {"requirement": "2.8.1", "tipo": TipoCentroCarga.TIPO_B, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.8.2", "tipo": TipoCentroCarga.TIPO_B, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.8.3", "tipo": TipoCentroCarga.TIPO_B, "estado": EstadoAplicabilidad.APLICA},

            # TIPO_C (Alta Tensión)
            {"requirement": "2.1", "tipo": TipoCentroCarga.TIPO_C, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.2", "tipo": TipoCentroCarga.TIPO_C, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.3", "tipo": TipoCentroCarga.TIPO_C, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.4", "tipo": TipoCentroCarga.TIPO_C, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.5", "tipo": TipoCentroCarga.TIPO_C, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.6", "tipo": TipoCentroCarga.TIPO_C, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.7", "tipo": TipoCentroCarga.TIPO_C, "estado": EstadoAplicabilidad.APLICA_TIC, "notas": "Conforme a Manual TIC"},
            {"requirement": "2.8.1", "tipo": TipoCentroCarga.TIPO_C, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.8.2", "tipo": TipoCentroCarga.TIPO_C, "estado": EstadoAplicabilidad.APLICA},
            {"requirement": "2.8.3", "tipo": TipoCentroCarga.TIPO_C, "estado": EstadoAplicabilidad.APLICA},
        ]

        # Create rules
        for rule_data in rules:
            req_id = requirement_map.get(rule_data["requirement"])
            if req_id:
                rule = ComplianceRule(
                    requirement_id=req_id,
                    tipo_centro_carga=rule_data["tipo"],
                    estado_aplicabilidad=rule_data["estado"],
                    notas=rule_data.get("notas")
                )
                db.add(rule)

        await db.commit()
        print(f"✅ Created {len(rules)} compliance rules")
        print("\n✅ Compliance seed completed successfully")


if __name__ == "__main__":
    asyncio.run(seed_requirements())
