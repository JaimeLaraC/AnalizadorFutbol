"""
Router para explorar datos de la base de datos.

Endpoints para obtener información de tablas.
"""

from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from pydantic import BaseModel

from ...db import get_db
from ...db.database import engine


router = APIRouter()


class TableInfo(BaseModel):
    """Información de una tabla."""
    name: str
    columns: List[str]
    row_count: int


class TableData(BaseModel):
    """Datos de una tabla."""
    table_name: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class DatabaseStats(BaseModel):
    """Estadísticas de la base de datos."""
    tables: List[TableInfo]
    total_predictions: int
    total_fixtures: int
    total_teams: int
    total_leagues: int


@router.get("/tables", response_model=List[TableInfo])
async def list_tables(db: Session = Depends(get_db)):
    """Lista todas las tablas con su información."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    result = []
    for t in tables:
        if t == "alembic_version":
            continue
        columns = [col["name"] for col in inspector.get_columns(t)]
        count = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        result.append(TableInfo(name=t, columns=columns, row_count=count))
    
    return result


@router.get("/tables/{table_name}", response_model=TableData)
async def get_table_data(
    table_name: str,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Obtiene los datos de una tabla específica."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if table_name not in tables:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Tabla '{table_name}' no encontrada")
    
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    total = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
    
    result = db.execute(text(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"))
    rows = []
    for row in result.fetchall():
        row_dict = {}
        for i, col in enumerate(columns):
            val = row[i]
            # Convertir tipos no serializables a string
            if val is not None and not isinstance(val, (str, int, float, bool)):
                val = str(val)
            row_dict[col] = val
        rows.append(row_dict)
    
    return TableData(
        table_name=table_name,
        columns=columns,
        rows=rows,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/stats", response_model=DatabaseStats)
async def get_database_stats(db: Session = Depends(get_db)):
    """Obtiene estadísticas generales de la base de datos."""
    inspector = inspect(engine)
    tables_info = []
    
    for t in inspector.get_table_names():
        if t == "alembic_version":
            continue
        columns = [col["name"] for col in inspector.get_columns(t)]
        count = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        tables_info.append(TableInfo(name=t, columns=columns, row_count=count))
    
    # Conteos específicos
    predictions = db.execute(text("SELECT COUNT(*) FROM predictions")).scalar()
    fixtures = db.execute(text("SELECT COUNT(*) FROM fixtures")).scalar()
    teams = db.execute(text("SELECT COUNT(*) FROM teams")).scalar()
    leagues = db.execute(text("SELECT COUNT(*) FROM leagues")).scalar()
    
    return DatabaseStats(
        tables=tables_info,
        total_predictions=predictions,
        total_fixtures=fixtures,
        total_teams=teams,
        total_leagues=leagues
    )


# =====================================
# Endpoints CRUD
# =====================================

class ColumnInfo(BaseModel):
    """Información detallada de una columna."""
    name: str
    type: str
    nullable: bool
    primary_key: bool
    default: Optional[str] = None


class TableSchema(BaseModel):
    """Schema completo de una tabla."""
    name: str
    columns: List[ColumnInfo]
    row_count: int
    primary_keys: List[str]


class DeleteResponse(BaseModel):
    """Respuesta de eliminación."""
    success: bool
    message: str
    deleted_count: int = 0


class RowData(BaseModel):
    """Datos de una fila individual."""
    data: Dict[str, Any]


@router.get("/schema/{table_name}", response_model=TableSchema)
async def get_table_schema(table_name: str, db: Session = Depends(get_db)):
    """Obtiene el schema detallado de una tabla."""
    from fastapi import HTTPException
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Tabla '{table_name}' no encontrada")
    
    columns_info = []
    pk_constraint = inspector.get_pk_constraint(table_name)
    pk_columns = pk_constraint.get("constrained_columns", []) if pk_constraint else []
    
    for col in inspector.get_columns(table_name):
        columns_info.append(ColumnInfo(
            name=col["name"],
            type=str(col["type"]),
            nullable=col.get("nullable", True),
            primary_key=col["name"] in pk_columns,
            default=str(col.get("default")) if col.get("default") else None
        ))
    
    count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
    
    return TableSchema(
        name=table_name,
        columns=columns_info,
        row_count=count,
        primary_keys=pk_columns
    )


@router.get("/tables/{table_name}/row/{row_id}", response_model=RowData)
async def get_row(table_name: str, row_id: int, db: Session = Depends(get_db)):
    """Obtiene una fila específica por ID."""
    from fastapi import HTTPException
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Tabla '{table_name}' no encontrada")
    
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    result = db.execute(text(f"SELECT * FROM {table_name} WHERE id = :id"), {"id": row_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Registro con ID {row_id} no encontrado")
    
    row_dict = {}
    for i, col in enumerate(columns):
        val = row[i]
        if val is not None and not isinstance(val, (str, int, float, bool)):
            val = str(val)
        row_dict[col] = val
    
    return RowData(data=row_dict)


@router.delete("/tables/{table_name}/row/{row_id}", response_model=DeleteResponse)
async def delete_row(table_name: str, row_id: int, db: Session = Depends(get_db)):
    """Elimina una fila específica por ID."""
    from fastapi import HTTPException
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Tabla '{table_name}' no encontrada")
    
    # Verificar que existe
    exists = db.execute(text(f"SELECT 1 FROM {table_name} WHERE id = :id"), {"id": row_id}).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail=f"Registro con ID {row_id} no encontrado")
    
    db.execute(text(f"DELETE FROM {table_name} WHERE id = :id"), {"id": row_id})
    db.commit()
    
    return DeleteResponse(success=True, message=f"Registro {row_id} eliminado de {table_name}", deleted_count=1)


@router.delete("/tables/{table_name}/clear", response_model=DeleteResponse)
async def clear_table(table_name: str, confirm: bool = Query(default=False), db: Session = Depends(get_db)):
    """Elimina todos los registros de una tabla."""
    from fastapi import HTTPException
    
    if not confirm:
        raise HTTPException(status_code=400, detail="Debes confirmar la operación con confirm=true")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Tabla '{table_name}' no encontrada")
    
    if table_name == "alembic_version":
        raise HTTPException(status_code=403, detail="No se puede eliminar la tabla de versiones de Alembic")
    
    count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
    db.execute(text(f"DELETE FROM {table_name}"))
    db.commit()
    
    return DeleteResponse(success=True, message=f"Tabla {table_name} vaciada", deleted_count=count)


@router.delete("/clear-all", response_model=DeleteResponse)
async def clear_all_tables(confirm: bool = Query(default=False), db: Session = Depends(get_db)):
    """⚠️ PELIGROSO: Elimina TODOS los datos de TODAS las tablas."""
    from fastapi import HTTPException
    
    if not confirm:
        raise HTTPException(status_code=400, detail="Debes confirmar la operación con confirm=true. ¡Esta acción es irreversible!")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # Orden de eliminación para respetar foreign keys
    delete_order = [
        "predictions",
        "fixture_statistics", 
        "head_to_head",
        "standings",
        "team_statistics",
        "fixtures",
        "teams",
        "leagues"
    ]
    
    total_deleted = 0
    for table_name in delete_order:
        if table_name in tables:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            if count > 0:
                db.execute(text(f"DELETE FROM {table_name}"))
                total_deleted += count
    
    db.commit()
    
    return DeleteResponse(
        success=True, 
        message=f"Base de datos limpiada. {total_deleted} registros eliminados.",
        deleted_count=total_deleted
    )


@router.put("/tables/{table_name}/row/{row_id}")
async def update_row(
    table_name: str, 
    row_id: int, 
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Actualiza una fila específica."""
    from fastapi import HTTPException
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Tabla '{table_name}' no encontrada")
    
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    
    # Filtrar solo columnas válidas
    valid_data = {k: v for k, v in data.items() if k in columns and k != "id"}
    
    if not valid_data:
        raise HTTPException(status_code=400, detail="No hay datos válidos para actualizar")
    
    # Construir SET clause
    set_clause = ", ".join([f"{k} = :{k}" for k in valid_data.keys()])
    valid_data["id"] = row_id
    
    result = db.execute(
        text(f"UPDATE {table_name} SET {set_clause} WHERE id = :id"),
        valid_data
    )
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Registro con ID {row_id} no encontrado")
    
    return {"success": True, "message": f"Registro {row_id} actualizado en {table_name}"}

