# AnalizadorFutbol - Documentación Completa del Proyecto

> **Última actualización**: 15 de Diciembre de 2025  
> **Estado**: Modelo validado con 94.4% de precisión en TOP 8 diarios

---

## 📋 Resumen Ejecutivo

Sistema de **predicción de partidos de fútbol** con Machine Learning. El modelo predice victorias locales/visitantes (excluye empates) con alta precisión en predicciones de alta confianza.

### Resultados Validados (Últimos 3 meses)
| Estrategia | Período | Aciertos | Fallos | Precisión |
|------------|---------|----------|--------|-----------|
| TOP 8 diario | 15 días (Dic) | 68 | 4 | **94.4%** |
| TOP 2 diario | 15 días (Dic) | 20 | 1 | **95.2%** |
| TOP 2 finde | Oct-Nov | 17 | 0 | **100%** |
| TOP 1 Lun-Jue | 3 meses | 24 | 5 | **82.8%** |

---

## 🤖 Modelo Actual

### Archivo del Modelo
```
backend/models/trained/main_model.pkl
```

### Especificaciones
| Parámetro | Valor |
|-----------|-------|
| **Algoritmo** | Random Forest Classifier |
| **Tipo** | Clasificación binaria (1=Local, 0=Visitante) |
| **Features** | 156 |
| **Entrenado con** | Temporadas 2023 y 2024 |
| **Validado con** | Temporada 2025 |
| **Precisión general** | 75.2% |
| **Precisión ≥70% confianza** | ~94% |

### Ligas de Entrenamiento (29 ligas de 19 países)

| ID | Liga | País | Partidos |
|----|------|------|----------|
| 39 | Premier League | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England | 585 |
| 40 | Championship | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England | 826 |
| 61 | Ligue 1 | 🇫🇷 France | 469 |
| 62 | Ligue 2 | 🇫🇷 France | 507 |
| 71 | Serie A | 🇧🇷 Brazil | 561 |
| 78 | Bundesliga | 🇩🇪 Germany | 453 |
| 79 | 2. Bundesliga | 🇩🇪 Germany | 455 |
| 88 | Eredivisie | 🇳🇱 Netherlands | 463 |
| 94 | Primeira Liga | 🇵🇹 Portugal | 458 |
| 103 | Eliteserien | 🇳🇴 Norway | 378 |
| 106 | Ekstraklasa | 🇵🇱 Poland | 442 |
| 113 | Allsvenskan | 🇸🇪 Sweden | 381 |
| 119 | Superliga | 🇩🇰 Denmark | 283 |
| 128 | Liga Profesional | 🇦🇷 Argentina | 508 |
| 135 | Serie A | 🇮🇹 Italy | 540 |
| 136 | Serie B | 🇮🇹 Italy | 523 |
| 140 | La Liga | 🇪🇸 Spain | 556 |
| 141 | Segunda División | 🇪🇸 Spain | 662 |
| 144 | Jupiler Pro League | 🇧🇪 Belgium | 455 |
| 179 | Premiership | 🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland | 347 |
| 188 | A-League | 🇦🇺 Australia | 255 |
| 197 | Super League 1 | 🇬🇷 Greece | 362 |
| 203 | Süper Lig | 🇹🇷 Turkey | 542 |
| 207 | Super League | 🇨🇭 Switzerland | 340 |
| 210 | HNL | 🇭🇷 Croatia | 264 |
| 218 | Bundesliga | 🇦🇹 Austria | 281 |
| 235 | Premier League | 🇷🇺 Russia | 349 |
| 253 | Major League Soccer | 🇺🇸 USA | 762 |
| 292 | K League 1 | 🇰🇷 South Korea | 328 |
| | **TOTAL** | **19 países** | **13,335 partidos** |

### Datos de Entrenamiento
```
backend/data/training_data_30leagues.csv       # Datos con 29 ligas
backend/data/training_data_30leagues_clean.csv # Datos limpios (imputados)
```

---

## 🚀 Inicio Rápido

### 1. Configurar entorno
```bash
cd /path/to/AnalizadorFutbol/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar base de datos
Crear `.env` en `backend/`:
```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/analizador_futbol
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=analizador_futbol
DATABASE_USER=usuario
DATABASE_PASSWORD=tu_password

API_FOOTBALL_KEY=tu_api_key
API_FOOTBALL_HOST=v3.football.api-sports.io
```

### 3. Verificar modelo
```bash
source venv/bin/activate
python -c "
import joblib
m = joblib.load('models/trained/main_model.pkl')
print(f'Modelo: {m[\"model_type\"]}')
print(f'Features: {len(m[\"feature_columns\"])}')
print(f'Entrenado: {m[\"trained_on\"]}')
print(f'Accuracy: {m[\"accuracy\"]:.1%}')
"
```

---

## 🔮 Generar Predicciones

### Script: TOP 10 del día
```bash
cd backend
source venv/bin/activate
python -c "
import pandas as pd
import joblib
from src.db.database import get_db_session
from src.db.models import Team, Fixture, League
from src.data.features.pipeline import FeaturePipeline
from datetime import datetime

# Cargar modelo
model_data = joblib.load('models/trained/main_model.pkl')
model = model_data['model']
feature_cols = model_data['feature_columns']

# Fecha a predecir (cambiar según necesidad)
start = datetime(2025, 12, 15)  # CAMBIAR FECHA
end = datetime(2025, 12, 16)    # Día siguiente

with get_db_session() as db:
    teams = {t.id: t.name for t in db.query(Team).all()}
    leagues_db = {l.id: l.name for l in db.query(League).all()}
    
    fixtures = db.query(Fixture).filter(
        Fixture.season == 2025, Fixture.date >= start, Fixture.date < end
    ).order_by(Fixture.date).all()
    
    fixture_data = [{
        'id': f.id, 'home': teams.get(f.home_team_id, 'Unknown'),
        'away': teams.get(f.away_team_id, 'Unknown'),
        'date': f.date, 'league': leagues_db.get(f.league_id, 'Unknown'),
        'status': f.status
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
            
            predictions.append({
                'home': fix['home'], 'away': fix['away'],
                'pred': pred, 'confidence': max(proba),
                'date': fix['date'], 'league': fix['league']
            })
    except: pass

# Ordenar por confianza y mostrar TOP 10
predictions.sort(key=lambda x: x['confidence'], reverse=True)

print('TOP 10 PREDICCIONES')
print('='*80)
for i, p in enumerate(predictions[:10], 1):
    winner = p['home'] if p['pred'] == 1 else p['away']
    tipo = 'LOCAL' if p['pred'] == 1 else 'VISITANTE'
    hora = p['date'].strftime('%H:%M')
    print(f'{i}. [{p[\"league\"][:15]}] {hora} | {p[\"home\"]} vs {p[\"away\"]}')
    print(f'   → {tipo}: {winner} | Confianza: {p[\"confidence\"]:.1%}')
"
```

---

## 🔄 Sincronización de Datos

### Sincronizar partidos (fixtures)
```bash
source venv/bin/activate
python -c "
from src.data.fixture_collector import FixtureCollector
collector = FixtureCollector()

# Las 29 ligas del modelo
ligas = [39, 40, 61, 62, 71, 78, 79, 88, 94, 103, 106, 113, 119, 128, 135, 136, 140, 141, 144, 179, 188, 197, 203, 207, 210, 218, 235, 253, 292]

for liga_id in ligas:
    print(f'Sincronizando liga {liga_id}...')
    collector.sync_league_fixtures(liga_id, 2025)
print('✅ Completado')
"
```

### Sincronizar clasificaciones
```bash
source venv/bin/activate
python -c "
from src.data.standings_collector import StandingsCollector
collector = StandingsCollector()

ligas = [39, 40, 61, 62, 71, 78, 79, 88, 94, 103, 106, 113, 119, 128, 135, 136, 140, 141, 144, 179, 188, 197, 203, 207, 210, 218, 235, 253, 292]
for liga_id in ligas:
    collector.sync_league_standings(liga_id, 2025)
print('✅ Standings actualizados')
"
```

---

## 📊 Features del Modelo (156 total)

### Features de Forma (form_calculator.py)
- `home_points_last_3/5/10`: Puntos en últimos N partidos
- `home_goals_for_avg_*`: Media de goles a favor
- `home_goals_against_avg_*`: Media de goles en contra
- `home_home_form_*`: Rendimiento como local
- `away_away_form_*`: Rendimiento como visitante

### Features de Clasificación (standings_calculator.py)
- `diff_position`: Diferencia de posición en liga
- `diff_points`: Diferencia de puntos
- `diff_goal_diff`: Diferencia de goles
- `diff_win_ratio`: Diferencia en ratio de victorias

### Features H2H (h2h_calculator.py)
- `h2h_total_matches`: Enfrentamientos históricos
- `h2h_home_wins/away_wins`: Victorias directas
- `h2h_dominance`: Índice de dominancia

---

## 🏗️ Arquitectura

```
AnalizadorFutbol/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI endpoints
│   │   ├── data/features/    # Calculadores de features
│   │   ├── db/               # SQLAlchemy models
│   │   └── api_client/       # Clientes externos
│   ├── models/trained/       # Modelos .pkl
│   ├── data/                 # CSVs de entrenamiento
│   └── venv/                 # Entorno virtual
├── frontend/                 # Next.js dashboard
└── PROJECT_CONTEXT.md        # Esta documentación
```

---

## ⚠️ Notas Importantes

1. **El modelo NO predice empates** - Solo victoria local (1) o visitante (0)
2. **Confianza ≥70% es el umbral recomendado** - Precisión histórica ~94%
3. **Los datos deben sincronizarse** antes de predecir para tener forma actual
4. **29 ligas de 19 países** - Cobertura global para predicciones

---

## 🔑 APIs Externas

### API-Football
- Endpoint: `v3.football.api-sports.io`
- Límite: 100 requests/día (plan gratuito)
- Usado para: fixtures, standings, equipos

---

*Última validación: 15 Diciembre 2025*
