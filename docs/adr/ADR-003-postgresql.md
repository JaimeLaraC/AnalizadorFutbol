# ADR-003: PostgreSQL como Base de Datos Principal

## Estado
**Aceptado** - 2024-12-11

## Contexto
Necesitamos una base de datos para almacenar:
- Datos históricos de partidos
- Estadísticas de equipos
- Predicciones y resultados
- Tracking de rendimiento del modelo

## Opciones Consideradas

### 1. SQLite
- **Pros**: Sin servidor, portable
- **Contras**: Concurrencia limitada, menos features

### 2. PostgreSQL (elegido)
- **Pros**: Robusto, JSON nativo, índices avanzados
- **Contras**: Requiere instalación

### 3. MongoDB
- **Pros**: Flexible, sin esquema
- **Contras**: Menos eficiente para queries analíticas

## Decisión
**Usar PostgreSQL** para producción y desarrollo.

### Razones
1. **Soporte JSON**: Para campos dinámicos (`extra_data`, `features_snapshot`)
2. **Índices parciales**: Para queries de predicciones top 5
3. **CTEs**: Para queries complejas de features
4. **Familiar**: Stack estándar Python

## Consecuencias

### Positivas
- Queries analíticas eficientes
- Transacciones ACID
- Escalable

### Negativas
- Requiere instalación local
- Configuración inicial

## Migraciones
Usamos **Alembic** para migraciones versionadas.

```bash
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
```
