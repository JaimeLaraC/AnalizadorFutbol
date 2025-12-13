#!/usr/bin/env python3
"""
CLI para AnalizadorFutbol - Visualización de datos de la base de datos.

Uso:
    python -m src.cli --help
    python -m src.cli tables
    python -m src.cli show predictions
    python -m src.cli show fixtures --limit 20
    python -m src.cli stats
"""

import sys
from datetime import datetime, date
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

from .utils.config import settings

app = typer.Typer(
    name="futbol-cli",
    help="🎯 CLI para visualizar datos de AnalizadorFutbol",
    add_completion=False,
)

console = Console()

# Conexión a la base de datos
engine = create_engine(settings.database_url, echo=False)
Session = sessionmaker(bind=engine)


def get_db():
    """Obtiene una sesión de base de datos."""
    return Session()


@app.command("tables")
def list_tables():
    """📋 Lista todas las tablas de la base de datos."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    table = Table(
        title="📊 Tablas en la Base de Datos",
        box=box.ROUNDED,
        header_style="bold cyan",
        show_lines=True
    )
    table.add_column("Tabla", style="green")
    table.add_column("Columnas", style="yellow")
    table.add_column("Filas", justify="right", style="magenta")
    
    db = get_db()
    for t in tables:
        if t == "alembic_version":
            continue
        columns = [col["name"] for col in inspector.get_columns(t)]
        count = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        table.add_row(t, ", ".join(columns[:5]) + ("..." if len(columns) > 5 else ""), str(count))
    db.close()
    
    console.print(table)


@app.command("show")
def show_table(
    table_name: str = typer.Argument(..., help="Nombre de la tabla a mostrar"),
    limit: int = typer.Option(10, "--limit", "-l", help="Número máximo de filas"),
    offset: int = typer.Option(0, "--offset", "-o", help="Filas a saltar"),
):
    """👁️ Muestra los datos de una tabla específica."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if table_name not in tables:
        console.print(f"[red]❌ Tabla '{table_name}' no encontrada.[/red]")
        console.print(f"[yellow]Tablas disponibles: {', '.join(tables)}[/yellow]")
        raise typer.Exit(1)
    
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    
    db = get_db()
    result = db.execute(text(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"))
    rows = result.fetchall()
    total = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
    db.close()
    
    table = Table(
        title=f"📋 {table_name.upper()} ({len(rows)} de {total} filas)",
        box=box.ROUNDED,
        header_style="bold cyan",
        show_lines=True,
        expand=True
    )
    
    # Limitar columnas visibles para que quepan
    visible_cols = columns[:8]
    for col in visible_cols:
        table.add_column(col, overflow="ellipsis", max_width=25)
    
    if len(columns) > 8:
        table.add_column("...", style="dim")
    
    for row in rows:
        row_data = [str(v)[:25] if v is not None else "-" for v in row[:8]]
        if len(columns) > 8:
            row_data.append("...")
        table.add_row(*row_data)
    
    if not rows:
        console.print(Panel("[yellow]⚠️ La tabla está vacía[/yellow]", title=table_name))
    else:
        console.print(table)


@app.command("predictions")
def show_predictions(
    date_filter: Optional[str] = typer.Option(None, "--date", "-d", help="Filtrar por fecha (YYYY-MM-DD)"),
    top5: bool = typer.Option(False, "--top5", "-t", help="Solo mostrar Top 5"),
    limit: int = typer.Option(20, "--limit", "-l", help="Número máximo de resultados"),
):
    """🎯 Muestra las predicciones de forma detallada."""
    db = get_db()
    
    query = """
        SELECT 
            p.id,
            p.fixture_id,
            p.predicted_winner,
            p.confidence,
            p.is_correct,
            p.is_top_5,
            f.date as match_date,
            th.name as home_team,
            ta.name as away_team,
            l.name as league
        FROM predictions p
        LEFT JOIN fixtures f ON p.fixture_id = f.id
        LEFT JOIN teams th ON f.home_team_id = th.id
        LEFT JOIN teams ta ON f.away_team_id = ta.id
        LEFT JOIN leagues l ON f.league_id = l.id
        WHERE 1=1
    """
    
    if date_filter:
        query += f" AND DATE(f.date) = '{date_filter}'"
    if top5:
        query += " AND p.is_top_5 = true"
    
    query += f" ORDER BY p.confidence DESC LIMIT {limit}"
    
    result = db.execute(text(query))
    rows = result.fetchall()
    db.close()
    
    table = Table(
        title="🎯 Predicciones",
        box=box.ROUNDED,
        header_style="bold cyan"
    )
    table.add_column("ID", style="dim")
    table.add_column("Partido", style="green")
    table.add_column("Liga", style="blue")
    table.add_column("Predicción", justify="center")
    table.add_column("Confianza", justify="right", style="yellow")
    table.add_column("Resultado", justify="center")
    table.add_column("Top5", justify="center")
    
    for row in rows:
        pred_winner = "🏠 Local" if row[2] == 1 else "✈️ Visit"
        confidence = f"{row[3]*100:.1f}%" if row[3] else "-"
        is_correct = "✅" if row[4] else ("❌" if row[4] is False else "⏳")
        is_top5 = "⭐" if row[5] else ""
        home_team = row[7] or "?"
        away_team = row[8] or "?"
        league = row[9] or "-"
        
        table.add_row(
            str(row[0]),
            f"{home_team} vs {away_team}",
            league[:20],
            pred_winner,
            confidence,
            is_correct,
            is_top5
        )
    
    if not rows:
        console.print(Panel("[yellow]⚠️ No hay predicciones[/yellow]"))
    else:
        console.print(table)


@app.command("fixtures")
def show_fixtures(
    date_filter: Optional[str] = typer.Option(None, "--date", "-d", help="Filtrar por fecha"),
    limit: int = typer.Option(20, "--limit", "-l", help="Número máximo"),
):
    """⚽ Muestra los partidos programados."""
    db = get_db()
    
    query = """
        SELECT 
            f.id,
            f.date,
            th.name as home_team,
            ta.name as away_team,
            l.name as league,
            f.status,
            f.home_goals,
            f.away_goals
        FROM fixtures f
        LEFT JOIN teams th ON f.home_team_id = th.id  
        LEFT JOIN teams ta ON f.away_team_id = ta.id
        LEFT JOIN leagues l ON f.league_id = l.id
        WHERE 1=1
    """
    
    if date_filter:
        query += f" AND DATE(f.date) = '{date_filter}'"
    
    query += f" ORDER BY f.date DESC LIMIT {limit}"
    
    result = db.execute(text(query))
    rows = result.fetchall()
    db.close()
    
    table = Table(
        title="⚽ Partidos",
        box=box.ROUNDED,
        header_style="bold cyan"
    )
    table.add_column("ID", style="dim")
    table.add_column("Fecha", style="magenta")
    table.add_column("Local", style="green")
    table.add_column("", justify="center")
    table.add_column("Visitante", style="green")
    table.add_column("Liga", style="blue")
    table.add_column("Estado", justify="center")
    
    for row in rows:
        fecha = row[1].strftime("%d/%m %H:%M") if row[1] else "-"
        home = row[2] or "?"
        away = row[3] or "?"
        league = (row[4] or "-")[:15]
        status = row[5] or "-"
        
        if row[6] is not None and row[7] is not None:
            score = f"{row[6]}-{row[7]}"
        else:
            score = "vs"
        
        table.add_row(str(row[0]), fecha, home, score, away, league, status)
    
    if not rows:
        console.print(Panel("[yellow]⚠️ No hay partidos[/yellow]"))
    else:
        console.print(table)


@app.command("stats")
def show_stats():
    """📈 Muestra estadísticas generales del sistema."""
    db = get_db()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # Obtener conteos
    counts = {}
    for t in tables:
        if t != "alembic_version":
            counts[t] = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
    
    # Estadísticas de predicciones
    pred_stats = db.execute(text("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_correct = true THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN is_correct = false THEN 1 ELSE 0 END) as incorrect,
            SUM(CASE WHEN is_correct IS NULL THEN 1 ELSE 0 END) as pending,
            AVG(confidence) as avg_confidence
        FROM predictions
    """)).fetchone()
    
    db.close()
    
    # Panel principal
    stats_text = Text()
    stats_text.append("📊 Datos en Base de Datos\n\n", style="bold cyan")
    
    for t, c in counts.items():
        emoji = {"predictions": "🎯", "fixtures": "⚽", "teams": "👥", 
                 "leagues": "🏆", "standings": "📋"}.get(t, "📁")
        stats_text.append(f"  {emoji} {t}: ", style="green")
        stats_text.append(f"{c:,}\n", style="yellow bold")
    
    console.print(Panel(stats_text, title="AnalizadorFutbol CLI", border_style="cyan"))
    
    # Estadísticas de predicciones si hay datos
    if pred_stats[0] > 0:
        total, correct, incorrect, pending, avg_conf = pred_stats
        accuracy = (correct / (correct + incorrect) * 100) if (correct + incorrect) > 0 else 0
        
        pred_table = Table(box=box.SIMPLE, show_header=False)
        pred_table.add_column("Métrica", style="cyan")
        pred_table.add_column("Valor", style="yellow")
        
        pred_table.add_row("Total predicciones", str(total))
        pred_table.add_row("✅ Correctas", str(correct or 0))
        pred_table.add_row("❌ Incorrectas", str(incorrect or 0))
        pred_table.add_row("⏳ Pendientes", str(pending or 0))
        pred_table.add_row("📊 Precisión", f"{accuracy:.1f}%")
        pred_table.add_row("🎯 Confianza promedio", f"{(avg_conf or 0)*100:.1f}%")
        
        console.print(Panel(pred_table, title="🎯 Estadísticas de Predicciones", border_style="green"))


@app.command("sql")
def run_sql(
    query: str = typer.Argument(..., help="Consulta SQL a ejecutar"),
):
    """🔧 Ejecuta una consulta SQL personalizada (solo SELECT)."""
    if not query.strip().lower().startswith("select"):
        console.print("[red]❌ Solo se permiten consultas SELECT[/red]")
        raise typer.Exit(1)
    
    db = get_db()
    try:
        result = db.execute(text(query))
        rows = result.fetchall()
        columns = result.keys()
        
        table = Table(box=box.ROUNDED, header_style="bold cyan")
        for col in columns:
            table.add_column(str(col))
        
        for row in rows[:50]:
            table.add_row(*[str(v)[:30] if v is not None else "-" for v in row])
        
        console.print(table)
        console.print(f"[dim]{len(rows)} filas[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
    finally:
        db.close()


@app.callback()
def main():
    """🎯⚽ AnalizadorFutbol CLI - Visualizador de Base de Datos"""
    pass


if __name__ == "__main__":
    app()
