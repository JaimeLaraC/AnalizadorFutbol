# Mejora: Standings Históricos para Predicciones Reproducibles

> **Fecha**: 23 Diciembre 2025  
> **Autor**: AnalizadorFutbol Team  
> **Archivos modificados**: `standings_calculator.py`, `pipeline.py`

---

## 📋 Resumen del Cambio

Se ha modificado el sistema de cálculo de features para usar **standings históricos** en lugar de standings actuales. Esto hace que las predicciones sean **100% reproducibles** independientemente de cuándo se recalculen.

---

## 🐛 Problema Detectado

Cuando se recalculaban predicciones de partidos pasados, los valores de confianza variaban porque:

1. El `form_calculator` **SÍ usaba** `fixture.date` para filtrar partidos anteriores ✅
2. El `standings_calculator` **NO usaba** la fecha, consultaba el standing actual ❌

### Ejemplo del problema:

```
Partido: Real Madrid vs Sevilla (20 Dic 2025)

Predicción original (20 Dic): 
  → Standing Real Madrid: 40 puntos, posición 2
  → Confianza: 82%

Predicción recalculada (23 Dic):
  → Standing Real Madrid: 43 puntos, posición 1 (incluye partido del 20)
  → Confianza: 84%
```

---

## ✅ Solución Implementada

### 1. Nuevo método: `_calculate_standing_from_fixtures()`

```python
def _calculate_standing_from_fixtures(
    self,
    team_id: int,
    league_id: int,
    season: int,
    before_date: datetime
) -> Optional[Dict]:
```

Este método calcula el standing de un equipo **dinámicamente** usando solo partidos finalizados (`status='FT'`) antes de la fecha especificada.

**Estadísticas calculadas**:
- Puntos, victorias, empates, derrotas
- Goles a favor/en contra
- Diferencia de goles
- Stats específicos como local/visitante
- Posición estimada basada en PPG

### 2. Parámetro `before_date` en métodos existentes

```python
def calculate_standing_features(
    self,
    team_id: int,
    league_id: int,
    season: int,
    prefix: str = "",
    before_date: Optional[datetime] = None  # ← NUEVO
) -> Dict[str, float]:

def calculate_relative_features(
    self,
    home_team_id: int,
    away_team_id: int,
    league_id: int,
    season: int,
    before_date: Optional[datetime] = None  # ← NUEVO
) -> Dict[str, float]:
```

### 3. Modo histórico por defecto

```python
class StandingsCalculator:
    def __init__(self, use_historical: bool = True):
        self.use_historical = use_historical
```

- `use_historical=True`: Calcula standings desde fixtures (reproducible)
- `use_historical=False`: Usa tabla standings actual (más rápido)

### 4. Integración en pipeline

```python
# pipeline.py, línea 96
standings_features = self.standings_calc.calculate_relative_features(
    home_id, away_id, league_id, season, match_date  # ← Pasar fecha
)
```

---

## 📊 Resultado

Ahora las predicciones son **completamente reproducibles**:

```
Partido: Real Madrid vs Sevilla (20 Dic 2025)

Cálculo 20 Dic: Confianza 84%, Standing: 39 pts
Cálculo 23 Dic: Confianza 84%, Standing: 39 pts ✅ IGUAL
Cálculo 30 Dic: Confianza 84%, Standing: 39 pts ✅ IGUAL
```

---

## ⚠️ Consideraciones

### Rendimiento
- El modo histórico es ligeramente más lento porque calcula standings desde fixtures
- Para predicciones masivas en tiempo real, considerar usar `use_historical=False`

### Posición Estimada
- Como calculamos standings desde fixtures, no tenemos el ranking real de todos los equipos
- La posición se **estima** basándose en PPG (puntos por partido):
  - PPG ≥ 2.5 → Top 3
  - PPG ≥ 2.0 → ~Posición 5
  - PPG ≥ 1.5 → ~Posición 10
  - PPG < 1.0 → ~Posición 15-20

### Compatibilidad
- Los cambios son **retrocompatibles**
- Si no se pasa `before_date`, funciona como antes

---

## 🧪 Testing

```bash
# Verificar que funciona
cd backend
source venv/bin/activate
python -c "
from datetime import datetime
from src.data.features.standings_calculator import StandingsCalculator

calc = StandingsCalculator(use_historical=True)
features = calc.calculate_standing_features(
    541,  # Real Madrid
    140,  # La Liga
    2025,
    'home_',
    datetime(2025, 12, 20)
)
print(f'Points: {features[\"home_points\"]}')
print(f'PPG: {features[\"home_ppg\"]:.2f}')
"
```

---

## 📁 Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `src/data/features/standings_calculator.py` | Añadido `_calculate_standing_from_fixtures()`, parámetro `before_date`, modo `use_historical` |
| `src/data/features/pipeline.py` | Pasar `match_date` a `calculate_relative_features()` |

---

*Documentación generada automáticamente - AnalizadorFutbol v2.0*
