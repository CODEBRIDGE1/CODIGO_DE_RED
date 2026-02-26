#!/usr/bin/env python3
"""
Migration Safety Checker
Validates that Alembic migrations are consistent with SQLAlchemy models

Run: python scripts/check_migrations.py
Exit codes:
  0 = All good
  1 = Pending migrations detected
  2 = Schema drift detected
  3 = Migration history issues
"""
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect, text
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from app.core.config import settings
from app.db.base import import_models

# Import models to register them
import_models()

def check_migration_history():
    """Check for branches in migration history"""
    print("🔍 Checking migration history for branches...")
    
    result = subprocess.run(
        ["alembic", "branches"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    if result.stdout.strip():
        print("❌ BRANCHES DETECTED in migration history:")
        print(result.stdout)
        print("\n💡 FIX: Run 'alembic merge heads' to create a merge migration")
        return False
    
    print("✅ No branches detected")
    return True


def check_current_head():
    """Check if database is at latest migration"""
    print("\n🔍 Checking database migration state...")
    
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current = context.get_current_revision()
        
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    head = script.get_current_head()
    
    if current != head:
        print(f"❌ Database is NOT at HEAD")
        print(f"   Current: {current}")
        print(f"   Head:    {head}")
        print("\n💡 FIX: Run 'alembic upgrade head'")
        return False
    
    print(f"✅ Database at HEAD: {head}")
    return True


def check_pending_migrations():
    """Check for pending model changes"""
    print("\n🔍 Checking for pending model changes...")
    
    result = subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", "check_drift", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    # Check if autogenerate would create changes
    if "detected" in result.stdout.lower() or "Generating" in result.stdout:
        print("❌ SCHEMA DRIFT DETECTED - Models don't match database:")
        print(result.stdout)
        print("\n💡 FIX: Run 'alembic revision --autogenerate -m \"fix drift\"'")
        return False
    
    print("✅ No pending migrations detected")
    return True


def check_enum_safety():
    """Check that ENUMs are created safely with checkfirst=True"""
    print("\n🔍 Checking ENUM safety in migrations...")
    
    migrations_path = Path(__file__).parent.parent / "alembic" / "versions"
    issues = []
    
    for migration_file in migrations_path.glob("*.py"):
        content = migration_file.read_text()
        
        # Check for ENUM creation without checkfirst
        if "sa.Enum(" in content:
            if ".create(" in content and "checkfirst=True" not in content:
                issues.append(f"{migration_file.name}: ENUM.create() without checkfirst=True")
        
        # Check for alter_column with ENUM without postgresql_using
        if "alter_column" in content and "Enum(" in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "alter_column" in line and "Enum(" in lines[i:i+5]:
                    # Check next 5 lines for postgresql_using
                    block = "\n".join(lines[i:i+6])
                    if "postgresql_using" not in block and "type_=" in block:
                        issues.append(f"{migration_file.name}: alter_column with ENUM missing postgresql_using")
                        break
    
    if issues:
        print("⚠️  ENUM safety issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n💡 FIX: Add checkfirst=True and postgresql_using to ENUM operations")
        return False
    
    print("✅ ENUM safety checks passed")
    return True


def check_not_null_safety():
    """Check for unsafe NOT NULL column additions"""
    print("\n🔍 Checking NOT NULL safety...")
    
    migrations_path = Path(__file__).parent.parent / "alembic" / "versions"
    issues = []
    
    for migration_file in migrations_path.glob("*.py"):
        content = migration_file.read_text()
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            # Check for add_column with nullable=False
            if "op.add_column" in line and "nullable=False" in line:
                # Check if there's a server_default
                if "server_default" not in line:
                    # Check next few lines for UPDATE or alter_column
                    next_lines = "\n".join(lines[i:i+10])
                    if "op.execute" not in next_lines and "UPDATE" not in next_lines:
                        issues.append(f"{migration_file.name} line {i+1}: add_column with nullable=False without default or data update")
    
    if issues:
        print("⚠️  NOT NULL safety issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n💡 FIX: Use 3-step pattern: nullable=True → UPDATE → alter_column nullable=False")
        return False
    
    print("✅ NOT NULL safety checks passed")
    return True


def check_downgrade_functions():
    """Check that all migrations have proper downgrade functions"""
    print("\n🔍 Checking downgrade functions...")
    
    migrations_path = Path(__file__).parent.parent / "alembic" / "versions"
    issues = []
    
    for migration_file in migrations_path.glob("*.py"):
        content = migration_file.read_text()
        
        # Check if downgrade is just 'pass'
        if "def downgrade()" in content:
            downgrade_section = content.split("def downgrade()")[1].split("\n\n")[0]
            non_comment_lines = [l for l in downgrade_section.split("\n") 
                               if l.strip() and not l.strip().startswith("#")]
            
            if len(non_comment_lines) <= 2 and "pass" in downgrade_section:
                # Only flag if upgrade has actual operations
                upgrade_section = content.split("def upgrade()")[1].split("def downgrade()")[0]
                if "op." in upgrade_section and "pass" not in upgrade_section:
                    issues.append(f"{migration_file.name}: has operations but downgrade is empty")
    
    if issues:
        print("⚠️  Downgrade issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n💡 FIX: Implement proper downgrade operations")
        return False
    
    print("✅ Downgrade functions look good")
    return True


def main():
    print("=" * 70)
    print("🛡️  ALEMBIC MIGRATION SAFETY CHECKER")
    print("=" * 70)
    
    all_checks = [
        check_migration_history(),
        check_current_head(),
        check_pending_migrations(),
        check_enum_safety(),
        check_not_null_safety(),
        check_downgrade_functions()
    ]
    
    print("\n" + "=" * 70)
    if all(all_checks):
        print("✅ ALL CHECKS PASSED - Migrations are safe!")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review issues above")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
