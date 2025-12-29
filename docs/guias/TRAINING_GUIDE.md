# Guía de Entrenamiento del Modelo - AnalizadorFutbol

> Esta guía describe paso a paso cómo recrear el modelo de predicción de fútbol desde cero.

---

## 📋 Resumen del Modelo

| Característica | Valor |
|---------------|-------|
| **Algoritmo** | Random Forest Classifier |
| **Target** | Binario: 1 (Local gana), 0 (Visitante gana) |
| **Features** | 156 |
| **Ligas** | 29 (19 países) |
| **Partidos entrenamiento** | 13,335 |
| **Temporadas** | 2023-2024 |
| **Precisión validación** | 75.2% general, 94%+ alta confianza |

---

## 🔧 Requisitos Previos

### 1. Entorno Python
```bash
cd AnalizadorFutbol/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Base de Datos PostgreSQL
```bash
# Crear base de datos
createdb analizador_futbol

# Configurar .env
cat > .env << EOF
DATABASE_URL=postgresql://usuario:password@localhost:5432/analizador_futbol
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=analizador_futbol
DATABASE_USER=usuario
DATABASE_PASSWORD=tu_password
API_FOOTBALL_KEY=tu_api_key
API_FOOTBALL_HOST=v3.football.api-sports.io
EOF
```

### 3. API-Football
- Registrarse en [API-Football](https://www.api-football.com/)
- Obtener API key (plan gratuito: 100 requests/día)

---

## 📥 Paso 1: Descargar Datos

### 1.1 Ligas a descargar
```python
# IDs de las 29 ligas del modelo
LIGAS = [
    39,   # Premier League (England)
    40,   # Championship (England)
    61,   # Ligue 1 (France)
    62,   # Ligue 2 (France)
    71,   # Serie A (Brazil)
    78,   # Bundesliga (Germany)
    79,   # 2. Bundesliga (Germany)
    88,   # Eredivisie (Netherlands)
    94,   # Primeira Liga (Portugal)
    103,  # Eliteserien (Norway)
    106,  # Ekstraklasa (Poland)
    113,  # Allsvenskan (Sweden)
    119,  # Superliga (Denmark)
    128,  # Liga Profesional (Argentina)
    135,  # Serie A (Italy)
    136,  # Serie B (Italy)
    140,  # La Liga (Spain)
    141,  # Segunda División (Spain)
    144,  # Jupiler Pro League (Belgium)
    179,  # Premiership (Scotland)
    188,  # A-League (Australia)
    197,  # Super League 1 (Greece)
    203,  # Süper Lig (Turkey)
    207,  # Super League (Switzerland)
    210,  # HNL (Croatia)
    218,  # Bundesliga (Austria)
    235,  # Premier League (Russia)
    253,  # MLS (USA)
    292,  # K League 1 (South Korea)
]
```

### 1.2 Descargar fixtures
```bash
source venv/bin/activate
python -c "
from src.data.fixture_collector import FixtureCollector

LIGAS = [39, 40, 61, 62, 71, 78, 79, 88, 94, 103, 106, 113, 119, 128, 135, 136, 140, 141, 144, 179, 188, 197, 203, 207, 210, 218, 235, 253, 292]
TEMPORADAS = [2023, 2024, 2025]

collector = FixtureCollector()

for temporada in TEMPORADAS:
    for liga_id in LIGAS:
        print(f'Descargando liga {liga_id}, temporada {temporada}...')
        try:
            collector.sync_league_fixtures(liga_id, temporada)
        except Exception as e:
            print(f'  Error: {e}')

print('✅ Fixtures descargados')
"
```

### 1.3 Descargar equipos
```bash
python -c "
from src.data.team_collector import TeamCollector

LIGAS = [39, 40, 61, 62, 71, 78, 79, 88, 94, 103, 106, 113, 119, 128, 135, 136, 140, 141, 144, 179, 188, 197, 203, 207, 210, 218, 235, 253, 292]

collector = TeamCollector()

for liga_id in LIGAS:
    print(f'Descargando equipos liga {liga_id}...')
    collector.sync_league_teams(liga_id, 2024)

print('✅ Equipos descargados')
"
```

### 1.4 Descargar standings
```bash
python -c "
from src.data.standings_collector import StandingsCollector

LIGAS = [39, 40, 61, 62, 71, 78, 79, 88, 94, 103, 106, 113, 119, 128, 135, 136, 140, 141, 144, 179, 188, 197, 203, 207, 210, 218, 235, 253, 292]
TEMPORADAS = [2023, 2024, 2025]

collector = StandingsCollector()

for temporada in TEMPORADAS:
    for liga_id in LIGAS:
        print(f'Standings liga {liga_id}, temporada {temporada}...')
        try:
            collector.sync_league_standings(liga_id, temporada)
        except: pass

print('✅ Standings descargados')
"
```

---

## 🔢 Paso 2: Generar Features

### 2.1 Ejecutar pipeline de features
```bash
python -c "
from src.data.features.pipeline import FeaturePipeline

LIGAS = [39, 40, 61, 62, 71, 78, 79, 88, 94, 103, 106, 113, 119, 128, 135, 136, 140, 141, 144, 179, 188, 197, 203, 207, 210, 218, 235, 253, 292]

pipeline = FeaturePipeline()

# Generar features para temporadas de entrenamiento
df = pipeline.generate_training_data(
    seasons=[2023, 2024],
    league_ids=LIGAS,
    output_path='data/training_data_30leagues.csv'
)

print(f'✅ Generadas {len(df)} filas con {len(df.columns)} columnas')
"
```

### 2.2 Limpiar datos (imputar NaN)
```bash
python -c "
import pandas as pd
import numpy as np

df = pd.read_csv('data/training_data_30leagues.csv')
print(f'Filas originales: {len(df)}')

# Eliminar filas sin target (empates)
df = df.dropna(subset=['target'])

# Imputar NaN con 0 en features numéricas
feature_cols = [c for c in df.columns if c not in ['fixture_id', 'league_id', 'season', 'target', 'date']]
df[feature_cols] = df[feature_cols].fillna(0)

# Guardar
df.to_csv('data/training_data_30leagues_clean.csv', index=False)
print(f'✅ Guardadas {len(df)} filas limpias')
"
```

---

## 🤖 Paso 3: Entrenar Modelo

### 3.1 Script de entrenamiento
```python
# Guardar como: backend/train_model.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# 1. Cargar datos
print("Cargando datos...")
df = pd.read_csv('data/training_data_30leagues_clean.csv')

# 2. Separar features y target
feature_cols = [c for c in df.columns if c not in [
    'fixture_id', 'league_id', 'season', 'target', 'date', 
    'home_team_id', 'away_team_id'
]]

X = df[feature_cols].fillna(0)
y = df['target'].astype(int)

print(f"Features: {len(feature_cols)}")
print(f"Samples: {len(X)}")

# 3. Split train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Train: {len(X_train)}, Test: {len(X_test)}")

# 4. Entrenar modelo
print("Entrenando Random Forest...")
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# 5. Evaluar
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n✅ Accuracy: {accuracy:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Away Win', 'Home Win']))

# 6. Guardar modelo
model_data = {
    'model': model,
    'feature_columns': feature_cols,
    'model_type': 'RandomForest',
    'trained_on': ['2023', '2024'],
    'validated_on': 2025,
    'accuracy': accuracy
}

joblib.dump(model_data, 'models/trained/main_model.pkl')
print("\n✅ Modelo guardado en models/trained/main_model.pkl")
```

### 3.2 Ejecutar entrenamiento
```bash
python train_model.py
```

---

## ✅ Paso 4: Verificar Modelo

### 4.1 Cargar y verificar
```bash
python -c "
import joblib

m = joblib.load('models/trained/main_model.pkl')

print('Modelo cargado:')
print(f'  Tipo: {m[\"model_type\"]}')
print(f'  Features: {len(m[\"feature_columns\"])}')
print(f'  Entrenado: {m[\"trained_on\"]}')
print(f'  Accuracy: {m[\"accuracy\"]:.1%}')
"
```

### 4.2 Probar predicción
```bash
python -c "
import pandas as pd
import joblib
from datetime import datetime
from src.db.database import get_db_session
from src.db.models import Fixture, Team
from src.data.features.pipeline import FeaturePipeline

model_data = joblib.load('models/trained/main_model.pkl')
model = model_data['model']
feature_cols = model_data['feature_columns']

# Obtener un fixture de ejemplo
with get_db_session() as db:
    fixture = db.query(Fixture).filter(Fixture.status == 'NS').first()
    if fixture:
        home = db.query(Team).filter(Team.id == fixture.home_team_id).first()
        away = db.query(Team).filter(Team.id == fixture.away_team_id).first()
        
        pipeline = FeaturePipeline()
        features = pipeline.calculate_fixture_features(fixture)
        
        if features and features.features:
            X = pd.DataFrame([features.features])
            for col in feature_cols:
                if col not in X.columns:
                    X[col] = 0
            X = X[feature_cols].fillna(0)
            
            pred = model.predict(X)[0]
            proba = model.predict_proba(X)[0]
            
            winner = home.name if pred == 1 else away.name
            print(f'Partido: {home.name} vs {away.name}')
            print(f'Predicción: {winner}')
            print(f'Confianza: {max(proba):.1%}')
"
```

---

## 📊 Features del Modelo (156)

### Categorías de Features

| Categoría | Cantidad | Descripción |
|-----------|----------|-------------|
| Forma general | 36 | Puntos y goles últimos 3/5/10 partidos |
| Forma local/visitante | 36 | Rendimiento específico como local/visitante |
| Standings | 20 | Posición, puntos, diferencia goles |
| Head-to-head | 15 | Historial enfrentamientos directos |
| Rachas | 20 | Victorias/derrotas consecutivas |
| Promedios | 29 | Xg esperado, corners, tarjetas |

### Features principales
```
home_points_last_3, home_points_last_5, home_points_last_10
home_goals_for_avg_3, home_goals_for_avg_5, home_goals_for_avg_10
home_goals_against_avg_3, home_goals_against_avg_5
away_points_last_3, away_points_last_5, away_points_last_10
diff_position, diff_points, diff_goal_diff
h2h_total_matches, h2h_home_wins, h2h_away_wins
home_win_streak, away_loss_streak
...
```

---

## 🔄 Actualización del Modelo

### Re-entrenar con nuevos datos
```bash
# 1. Sincronizar datos recientes
python -c "
from src.data.fixture_collector import FixtureCollector
from src.data.standings_collector import StandingsCollector

LIGAS = [39, 40, 61, 62, 71, 78, 79, 88, 94, 103, 106, 113, 119, 128, 135, 136, 140, 141, 144, 179, 188, 197, 203, 207, 210, 218, 235, 253, 292]

fc = FixtureCollector()
sc = StandingsCollector()

for liga in LIGAS:
    fc.sync_league_fixtures(liga, 2025)
    sc.sync_league_standings(liga, 2025)
"

# 2. Regenerar features incluyendo 2025
# 3. Re-entrenar modelo
```

---

## ⚠️ Notas Importantes

1. **API Limits**: Plan gratuito = 100 requests/día. Descargar todas las ligas puede tomar varios días.

2. **Empates excluidos**: El modelo es binario (local/visitante). Los empates se eliminan del entrenamiento.

3. **Features historicas**: Necesitas partidos previos para calcular features. Los primeros ~5 partidos de cada equipo tendrán features incompletas.

4. **Validación temporal**: Siempre valida con datos de temporadas futuras (no vistas en entrenamiento).

---

*Última actualización: 15 Diciembre 2025*
