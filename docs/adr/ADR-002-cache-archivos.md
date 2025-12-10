# ADR-002: Sistema de Caché Basado en Archivos

## Estado
**Aceptado** - 2024-12-11

## Contexto
API-Football tiene límites de requests diarios (7500 en plan Pro). Necesitamos un sistema de caché para:
- Reducir requests innecesarios
- Acelerar operaciones repetidas
- Mantener datos disponibles offline

## Opciones Consideradas

### 1. Redis
- **Pros**: Rápido, TTL nativo, compartible entre procesos
- **Contras**: Requiere servicio adicional, más complejidad de deploy

### 2. diskcache (Python)
- **Pros**: Fácil de usar, persistente
- **Contras**: Dependencia adicional, menos control

### 3. Archivos JSON (elegido)
- **Pros**: Simple, sin dependencias, inspectable manualmente
- **Contras**: Más lento para grandes volúmenes

## Decisión
**Usar caché basado en archivos JSON** para la fase inicial.

Cada entrada se guarda como:
```json
{
  "data": {...},
  "timestamp": 1702300000,
  "ttl": 3600,
  "endpoint": "/fixtures",
  "params": {"date": "2024-12-11"}
}
```

### TTL por Tipo de Datos

| Tipo | TTL | Razón |
|------|-----|-------|
| Ligas | 7 días | Raramente cambian |
| Equipos | 7 días | Raramente cambian |
| Standings | 6 horas | Cambian tras partidos |
| Fixtures | 1 hora | Pueden reprogramarse |
| Odds | 30 min | Muy dinámicas |

## Consecuencias

### Positivas
- Cero dependencias externas
- Fácil inspección y debug
- Portabilidad total

### Negativas
- No compartible entre procesos
- Limpieza manual necesaria

### Mitigaciones
- Job de limpieza de caché expirado
- Migrar a Redis si escala es insuficiente

## Referencias
- Requisito: Desarrollo local sin Docker
- Plan API: Pro (7500 req/día)
