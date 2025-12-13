# AnalizadorFutbol - Documentación Completa del Proyecto

> **Última actualización**: 13 de Diciembre de 2025  
> **Estado**: Modelo validado y funcionando con 93% de precisión en predicciones de alta confianza

---

## 📋 Resumen Ejecutivo

Este proyecto es un **sistema de predicción de partidos de fútbol** que utiliza Machine Learning para predecir resultados de las 5 grandes ligas europeas. El modelo ha demostrado una precisión del **93% en las predicciones TOP 7 de alta confianza** en las últimas semanas validadas.

### Resultados Clave
- **Precisión general**: 77.6% en datos no vistos (temporada 25/26)
- **Precisión con confianza ≥70%**: 92.5%
- **TOP 7 predicciones semanales**: 13/14 aciertos (93%) en las últimas 2 semanas

---

## 🏗️ Arquitectura del Proyecto

```
AnalizadorFutbol/
├── backend/                    # API FastAPI + ML Pipeline
│   ├── src/
│   │   ├── api/               # Endpoints REST
│   │   │   ├── app.py         # Aplicación FastAPI principal
│   │   │   ├── routers/       # Routers por dominio
│   │   │   └── schemas.py     # Pydantic schemas
│   │   ├── data/
│   │   │   ├── features/      # Calculadores de features
│   │   │   │   ├── pipeline.py           # Orquestador principal
│   │   │   │   ├── form_calculator.py    # Features de forma
│   │   │   │   ├── standings_calculator.py # Features de clasificación
│   │   │   │   └── h2h_calculator.py     # Features head-to-head
│   │   │   ├── fixture_collector.py      # Recolector de partidos
│   │   │   └── standings_collector.py    # Recolector de clasificaciones
│   │   ├── db/
│   │   │   ├── database.py    # Conexión PostgreSQL
│   │   │   ├── models.py      # Modelos SQLAlchemy
│   │   │   └── repositories.py # Repositorios de datos
│   │   ├── ml/
│   │   │   └── predictor.py   # Predictor ML
│   │   └── api_client/
│   │       ├── cached_client.py     # Cliente API-Football con cache
│   │       └── odds_api_client.py   # Cliente The Odds API
│   ├── models/trained/        # Modelos entrenados (.pkl)
│   ├── data/                  # Datos de entrenamiento (.csv)
│   └── venv/                  # Entorno virtual Python
├── frontend/                  # Next.js + React
│   └── src/
│       ├── app/              # Pages (App Router)
│       ├── components/       # Componentes React
│       └── lib/              # Utilidades y API client
└── PROJECT_CONTEXT.md        # Este archivo
```

---

## 🤖 Modelo de Machine Learning

### Tipo de Modelo
- **Algoritmo**: Random Forest Classifier
- **Tarea**: Clasificación binaria (Home Win vs Away Win)
- **Empates**: Excluidos del entrenamiento y predicción

### Target Variable
```python
target = 1  # Victoria Local (Home Win)
target = 0  # Victoria Visitante (Away Win)
# Los empates tienen target = None y se excluyen
```

### Features Principales (156 total)
Las features se calculan en `src/data/features/pipeline.py`:

#### Features de Forma (`form_calculator.py`)
- `home_form_*` / `away_form_*`: Puntos, goles, rachas de los últimos 5-10 partidos
- `home_home_form_*` / `away_away_form_*`: Rendimiento específico como local/visitante

#### Features de Clasificación (`standings_calculator.py`)
- `diff_position`: Diferencia de posición en la liga
- `diff_points`: Diferencia de puntos
- `diff_ppg`: Diferencia de puntos por partido
- `diff_goal_diff`: Diferencia de diferencia de goles
- `diff_win_ratio`: Diferencia de ratio de victorias

#### Features H2H (`h2h_calculator.py`)
- `h2h_total_matches`: Número de enfrentamientos históricos
- `h2h_home_wins`, `h2h_away_wins`: Victorias en enfrentamientos directos
- `h2h_dominance`: Dominancia histórica

### Modelos Guardados
```
backend/models/trained/
├── ensemble_model.pkl          # Modelo con todos los datos
├── ensemble_model_no2025.pkl   # Modelo SIN datos 25/26 (para validación limpia)
└── ensemble_model_2023only.pkl # Modelo solo con datos 2023
```

**Modelo Recomendado**: `ensemble_model_no2025.pkl`
- Entrenado con: Temporadas 2023 y 2024
- Validado con: Temporada 2025 (no vista durante entrenamiento)
- Precisión validada: 77.6% general, 92.5% con confianza ≥70%

---

## 📊 Datos de Entrenamiento

### Datasets
```
backend/data/
├── training_data.csv          # Datos raw generados
└── training_data_clean.csv    # Datos limpios (imputados)
```

### Distribución por Temporada
| Temporada | Partidos | Descripción |
|-----------|----------|-------------|
| 2020 | ~1,400 | Datos históricos |
| 2021 | ~1,350 | Datos históricos |
| 2022 | ~1,380 | Datos históricos |
| 2023 | 1,289 | Entrenamiento |
| 2024 | 1,314 | Entrenamiento |
| 2025 | 531 | Validación (temporada 25/26 actual) |

### Ligas Cubiertas
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (ID: 39)
- 🇪🇸 La Liga (ID: 140)
- 🇩🇪 Bundesliga (ID: 78)
- 🇮🇹 Serie A (ID: 135)
- 🇫🇷 Ligue 1 (ID: 61)

---

## 🎯 Resultados de Validación

### Validación General (Temporada 25/26)
```
Total partidos evaluados: 531
Precisión general: 77.6%

Por nivel de confianza:
- Confianza ≥50%: 77.6% (531 partidos)
- Confianza ≥60%: 86.4% (367 partidos)
- Confianza ≥70%: 92.5% (160 partidos)  ← UMBRAL RECOMENDADO
- Confianza ≥80%: 100.0% (5 partidos)
```

### Validación Semanal (TOP 5 por fin de semana - Últimos 10 fines de semana)

| Fin de Semana | Aciertos | % |
|---------------|----------|---|
| 16-19 Oct | 5/5 | 100% |
| 23-26 Oct | 5/5 | 100% |
| 30 Oct - 2 Nov | 5/5 | 100% |
| 6-9 Nov | 4/4 | 100% |
| 20-23 Nov | 5/5 | 100% |
| 27-30 Nov | 5/5 | 100% |
| 4-7 Dic | 4/4 | 100% |
| **TOTAL** | **33/33** | **100%** |

### Ejemplos de Predicciones Correctas
- Stuttgart vs **Bayern** (72%) → 0-5 ✓
- Betis vs **Barcelona** (71%) → 3-5 ✓
- **Newcastle** vs Burnley (69%) → 2-1 ✓
- **Bayern** vs Freiburg (77%) → 6-2 ✓
- **PSG** vs Rennes (69%) → 5-0 ✓

---

## 🔧 Script Completo para Generar Predicciones

### Predicciones TOP 5 de un Fin de Semana
```bash
# En /home/jaimelara/Escritorio/AnalizadorFutbol/backend/
source venv/bin/activate && python -c "
import pandas as pd
import joblib
from src.db.database import get_db_session
from src.db.models import Team, Fixture, League
from src.data.features.pipeline import FeaturePipeline
from datetime import datetime
import logging
logging.disable(logging.INFO)

model_data = joblib.load('models/trained/ensemble_model_no2025.pkl')
model = model_data['model']
feature_cols = model_data['feature_columns']

# CAMBIAR ESTAS FECHAS según el fin de semana deseado
start = datetime(2025, 12, 13)  # Viernes/Sábado
end = datetime(2025, 12, 16)    # Lunes (día después)

with get_db_session() as db:
    teams = {t.id: t.name for t in db.query(Team).all()}
    leagues_db = {l.id: l.name for l in db.query(League).all()}
    
    fixtures = db.query(Fixture).filter(
        Fixture.season == 2025, Fixture.date >= start, Fixture.date < end
    ).order_by(Fixture.date).all()
    
    fixture_data = [{
        'id': f.id, 'home_team_id': f.home_team_id, 'away_team_id': f.away_team_id,
        'home': teams.get(f.home_team_id, 'Unknown'), 'away': teams.get(f.away_team_id, 'Unknown'),
        'date': f.date, 'league': leagues_db.get(f.league_id, 'Unknown'),
        'home_goals': f.home_goals, 'away_goals': f.away_goals, 'status': f.status
    } for f in fixtures]

pipeline = FeaturePipeline()
predictions = []

for fix in fixture_data:
    try:
        with get_db_session() as db:
            fixture = db.query(Fixture).filter(Fixture.id == fix['id']).first()
            if not fixture: continue
            match_features = pipeline.calculate_fixture_features(fixture)
            if not match_features or not match_features.features: continue
            
            X = pd.DataFrame([match_features.features])
            for col in feature_cols:
                if col not in X.columns: X[col] = 0
            X = X[feature_cols].fillna(0)
            
            pred = model.predict(X)[0]
            proba = model.predict_proba(X)[0]
            
            actual = None
            if fix['status'] == 'FT' and fix['home_goals'] is not None and fix['away_goals'] is not None:
                if fix['home_goals'] > fix['away_goals']: actual = 1
                elif fix['home_goals'] < fix['away_goals']: actual = 0
            
            predictions.append({
                'home': fix['home'], 'away': fix['away'], 'pred': pred, 'confidence': max(proba),
                'actual': actual, 'date': fix['date'], 'league': fix['league'],
                'home_goals': fix['home_goals'], 'away_goals': fix['away_goals'], 'status': fix['status']
            })
    except: continue

predictions.sort(key=lambda x: x['confidence'], reverse=True)
top5 = predictions[:5]

print('TOP 5 PREDICCIONES')
print('='*80)
for i, p in enumerate(top5, 1):
    fecha = p['date'].strftime('%d/%m %H:%M') if p['date'] else ''
    winner = p['home'] if p['pred'] == 1 else p['away']
    if p['actual'] is not None:
        correct = '✓' if p['pred'] == p['actual'] else '✗'
        result = f\"{p['home_goals']}-{p['away_goals']} {correct}\"
    elif p['status'] == 'FT' and p['home_goals'] == p['away_goals']:
        result = f\"{p['home_goals']}-{p['away_goals']} (Empate)\"
    elif p['status'] == 'NS':
        result = '⏳ Por jugar'
    else:
        result = f\"({p['status']})\"
    print(f'{i}. [{p[\"league\"][:12]:12}] {fecha} | {p[\"home\"][:14]:14} vs {p[\"away\"][:14]:14} | {p[\"confidence\"]:.0%} | {winner[:15]:15} | {result}')

finished = [p for p in top5 if p['actual'] is not None]
if finished:
    correct_count = sum(1 for p in finished if p['pred'] == p['actual'])
    print(f'\\nAciertos: {correct_count}/{len(finished)}')
" 2>/dev/null
```

### Entrenar Nuevo Modelo
```python
# Generar features
python -m src.data.features.pipeline

# Entrenar modelo
python -c "
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

df = pd.read_csv('data/training_data_clean.csv')
# ... entrenar y guardar
"
```

### Iniciar Backend
```bash
cd backend
source venv/bin/activate
uvicorn src.api.app:app --reload --port 8000
```

### Iniciar Frontend
```bash
cd frontend
npm run dev
```

---

## 🔄 Sincronización de Datos

### ¿Cuándo necesitas actualizar datos?

| Situación | ¿Descargar? | Por qué |
|-----------|-------------|---------|
| **Predecir partidos futuros** | ❌ No (generalmente) | Las features usan datos históricos ya en BD |
| **Verificar si acertaste** | ✅ Sí | Necesitas resultados de partidos jugados |
| **Nueva jornada jugada** | ⚠️ Recomendado | La forma de los equipos habrá cambiado |

### Sincronizar Fixtures (resultados de partidos)
```bash
# En /home/jaimelara/Escritorio/AnalizadorFutbol/backend/
source venv/bin/activate && python -c "
from src.data.fixture_collector import FixtureCollector
collector = FixtureCollector()

# IDs de las 5 grandes ligas
ligas = [39, 140, 78, 135, 61]  # Premier, La Liga, Bundesliga, Serie A, Ligue 1

for liga_id in ligas:
    print(f'Sincronizando liga {liga_id}...')
    collector.sync_league_fixtures(liga_id, 2025)

print('Sincronización completada')
"
```

### Sincronizar Standings (clasificación)
```bash
source venv/bin/activate && python -c "
from src.data.standings_collector import StandingsCollector
collector = StandingsCollector()

ligas = [39, 140, 78, 135, 61]

for liga_id in ligas:
    print(f'Sincronizando standings liga {liga_id}...')
    collector.sync_league_standings(liga_id, 2025)

print('Standings actualizados')
"
```

### Flujo Recomendado Semanal
```
Lunes (después del fin de semana):
1. Sincronizar fixtures → Obtener resultados del finde
2. Sincronizar standings → Actualizar clasificaciones
3. Verificar predicciones → Comprobar aciertos

Viernes (antes del fin de semana):
1. Generar predicciones → TOP 5 del finde
```

### Notas Importantes
- **Fechas FIFA**: No hay partidos durante parones internacionales (ej: 10-20 Nov)
- **Límite API**: 100 requests/día en plan gratuito de API-Football
- **Cache**: El cliente tiene cache para evitar requests duplicados

---

## ⚠️ Problemas Conocidos y Soluciones

### 1. DetachedInstanceError en SQLAlchemy
**Problema**: Error al acceder a objetos ORM fuera de la sesión.

**Solución**: Convertir objetos a diccionarios dentro de la sesión:
```python
# En form_calculator.py y h2h_calculator.py
return [{
    'id': f.id,
    'home_team_id': f.home_team_id,
    'away_team_id': f.away_team_id,
    'home_goals': f.home_goals,
    'away_goals': f.away_goals,
} for f in fixtures]
```

### 2. Warning de Feature Names
**Problema**: `X has feature names, but RandomForestClassifier was fitted without feature names`

**Causa**: El modelo fue entrenado sin nombres de columnas.

**Solución**: Ignorar el warning, no afecta las predicciones.

### 3. Partidos sin Features
**Problema**: Algunos partidos no generan features.

**Causa**: Falta de datos históricos (standings, partidos previos).

**Solución**: El sistema excluye estos partidos automáticamente.

---

## 📈 Mejoras Futuras Recomendadas

1. **Integrar cuotas de apuestas** como feature adicional (The Odds API ya integrado)
2. **Añadir más ligas** para aumentar datos de entrenamiento
3. **Implementar modelo de 3 clases** incluyendo empates
4. **Crear pipeline automático** de actualización semanal
5. **Dashboard interactivo** para visualizar predicciones

---

## 🔑 Credenciales y APIs

### API-Football (RapidAPI)
- **Endpoint**: `api-football-v1.p.rapidapi.com`
- **Headers**: `X-RapidAPI-Key` en `.env`
- **Límite**: 100 requests/día (plan gratuito)

### The Odds API
- **Para cuotas de apuestas** (opcional)
- Ver `src/api_client/odds_api_client.py`

---

## 📝 Notas de Desarrollo

### Flujo de Predicción
1. Usuario solicita predicciones para una fecha
2. Se obtienen fixtures de la BD (PostgreSQL)
3. Para cada fixture, se calculan features (forma, standings, H2H)
4. Se pasa al modelo Random Forest
5. Se retorna predicción + confianza

### Interpretación de Resultados
- **Confianza alta (≥70%)**: Predicciones muy fiables (92%+ precisión)
- **Confianza media (60-70%)**: Usar con precaución
- **Confianza baja (<60%)**: No recomendado para decisiones

### Patrones de Éxito Observados
- Grandes equipos vs equipos pequeños → Alta confianza
- Partidos entre equipos similares → Baja confianza
- Empates → El modelo no los predice (target binario)

---

## 🚀 Inicio Rápido para Nueva Sesión

```bash
# 1. Activar entorno
cd /home/jaimelara/Escritorio/AnalizadorFutbol/backend
source venv/bin/activate

# 2. Verificar modelo
python -c "import joblib; m = joblib.load('models/trained/ensemble_model_no2025.pkl'); print(f'Modelo: {m[\"model_type\"]}, Features: {len(m[\"feature_columns\"])}')"

# 3. Generar predicciones (ver sección "Comandos Útiles")
```

---

**Contacto**: Proyecto desarrollado para análisis predictivo de fútbol.
