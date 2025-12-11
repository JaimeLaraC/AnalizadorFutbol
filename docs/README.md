# 📚 Documentación - AnalizadorFutbol

## Índice

### Guías
- [🚀 Guía de Desarrollo](development_guide.md) - Setup, desarrollo diario, solución de problemas
- [🔀 Guía de Git](git_guide.md) - Git Flow, commits, PRs

### Arquitectura
- [🏗️ Arquitectura del Sistema](architecture.md) - Diagramas y componentes
- [🗄️ Esquema de Base de Datos](database_schema.md) - Diagrama ER y tablas

### Planificación
- [🎯 Plan de Implementación](implementation_plan.md) - Fases y configuración
- [📊 Catálogo de Features](features_catalog.md) - 69 features para el modelo

### Decisiones de Arquitectura (ADRs)
- [ADR-001: Modelo Binario](adr/ADR-001-modelo-binario.md) - Sin empates
- [ADR-002: Caché en Archivos](adr/ADR-002-cache-archivos.md) - Sistema de caché
- [ADR-003: PostgreSQL](adr/ADR-003-postgresql.md) - Base de datos

---

## Estado del Proyecto

| Fase | Estado | Descripción |
|------|--------|-------------|
| 1. Setup | ✅ | Estructura, Git Flow, CI/CD |
| 2. API Client | ✅ | Cliente HTTP + Caché |
| 3. Database | ✅ | Modelos SQLAlchemy + Alembic |
| 4. Recopilación | ✅ | Collectors de datos |
| 5. Features | ✅ | Pipeline Feature Engineering |
| 6. Modelado | ✅ | XGBoost + LightGBM + Calibración |
| 7. Backend API | ✅ | FastAPI + APScheduler |
| 8. Frontend | ✅ | Next.js Dashboard Premium |
| 9. Testing | ⏳ | En progreso |

---

## Links Útiles

- **Repositorio**: https://github.com/JaimeLaraC/AnalizadorFutbol
- **API-Football**: https://www.api-football.com/documentation-v3
