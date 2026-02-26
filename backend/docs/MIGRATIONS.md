# 🛡️ Migration Safety Guidelines

## Overview

This project uses **Alembic** for database migrations with **PostgreSQL 15**. All migrations MUST follow these safety rules to ensure:
- ✅ Zero-downtime deployments
- ✅ Rollback capability
- ✅ Container compatibility (asyncpg)
- ✅ Idempotent operations

---

## 🚨 Critical Rules

### 1. ENUM Types

**Problem**: PostgreSQL ENUMs fail without explicit casting.

**Solution**: Always use `postgresql_using` clause:

```python
# ❌ WRONG - Will fail
op.alter_column('table', 'column',
    type_=sa.Enum('A', 'B', name='myenum'))

# ✅ CORRECT
myenum = sa.Enum('A', 'B', name='myenum')
myenum.create(op.get_bind(), checkfirst=True)  # Create ENUM first

op.alter_column('table', 'column',
    type_=myenum,
    postgresql_using='column::myenum')  # Explicit cast
```

### 2. NOT NULL Columns

**Problem**: Adding `NOT NULL` to existing tables fails if rows exist.

**Solution**: Use 3-step pattern:

```python
# Step 1: Add as nullable
op.add_column('table', sa.Column('new_col', sa.String(), nullable=True))

# Step 2: Populate existing rows
op.execute("UPDATE table SET new_col = 'default' WHERE new_col IS NULL")

# Step 3: Make NOT NULL
op.alter_column('table', 'new_col', nullable=False)
```

### 3. Server Defaults

**Always** use `server_default` for timestamp columns:

```python
# ✅ CORRECT
sa.Column('created_at', sa.DateTime(), nullable=False, 
          server_default=sa.text('now()'))
```

### 4. Foreign Key Cascades

**Always** specify `ondelete` behavior:

```python
# ✅ CORRECT
sa.ForeignKeyConstraint(['company_id'], ['companies.id'], 
                       ondelete='CASCADE')
```

### 5. ENUM Creation Safety

**Always** use `checkfirst=True` for idempotency:

```python
# ✅ CORRECT - Won't fail on re-run
myenum = sa.Enum('A', 'B', name='myenum')
myenum.create(op.get_bind(), checkfirst=True)
```

---

## 🔧 Workflow

### Creating a New Migration

```bash
# Auto-generate from model changes
docker-compose exec api alembic revision --autogenerate -m "description"

# Review and edit the generated file in alembic/versions/
# Apply rules above if needed

# Test the migration
docker-compose exec api alembic upgrade head

# Test rollback
docker-compose exec api alembic downgrade -1
docker-compose exec api alembic upgrade head
```

### Testing from Scratch

```bash
# Run full test (drops database!)
./backend/scripts/test_migrations.sh
```

### Validation

```bash
# Check migration safety
docker-compose exec api python scripts/check_migrations.py
```

---

## 📋 Pre-Commit Checklist

Before merging a migration:

- [ ] ENUM types use `checkfirst=True`
- [ ] ENUM conversions use `postgresql_using`
- [ ] NOT NULL columns follow 3-step pattern
- [ ] Timestamps have `server_default=sa.text('now()')`
- [ ] Foreign keys have `ondelete` specified
- [ ] `downgrade()` function is implemented
- [ ] Tested with `alembic upgrade head` in fresh DB
- [ ] Tested with `alembic downgrade -1`
- [ ] `check_migrations.py` passes

---

## 🐛 Common Errors

### Error: "column cannot be cast automatically to type enum"

**Fix**: Add `postgresql_using` clause:

```python
op.alter_column('table', 'column',
    type_=myenum,
    postgresql_using='column::myenum')
```

### Error: "column contains null values"

**Fix**: Use 3-step NOT NULL pattern (see above).

### Error: "type 'myenum' already exists"

**Fix**: Add `checkfirst=True`:

```python
myenum.create(op.get_bind(), checkfirst=True)
```

---

## 📚 References

- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [PostgreSQL ENUM Types](https://www.postgresql.org/docs/15/datatype-enum.html)
- [SQLAlchemy Asyncpg Notes](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.asyncpg)
