# AnalizadorFutbol 🎯⚽

Sistema de predicción de partidos de fútbol con Machine Learning.

## 📊 Resultados del Modelo

| Estrategia | Precisión | Período |
|------------|-----------|---------|
| TOP 8 diario | **94.4%** | Diciembre 2025 |
| TOP 2 diario | **95.2%** | Diciembre 2025 |
| TOP 2 finde | **100%** | Oct-Nov 2025 |

## 🚀 Inicio Rápido

```bash
# 1. Clonar y configurar
git clone https://github.com/JaimeLaraC/AnalizadorFutbol.git
cd AnalizadorFutbol/backend

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configurar .env (copiar de .env.example)
cp .env.example .env
# Editar con tus credenciales de PostgreSQL y API-Football

# 4. Verificar modelo
python -c "
import joblib
m = joblib.load('models/trained/main_model.pkl')
print(f'✅ Modelo cargado: {m[\"model_type\"]} con {len(m[\"feature_columns\"])} features')
"
```

## 🔮 Generar Predicciones

```bash
cd backend && source venv/bin/activate

# TOP 10 de hoy
python -c "
from datetime import datetime
import pandas as pd, joblib
from src.db.database import get_db_session
from src.db.models import Team, Fixture, League
from src.data.features.pipeline import FeaturePipeline

model_data = joblib.load('models/trained/main_model.pkl')
model, feature_cols = model_data['model'], model_data['feature_columns']

today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
tomorrow = today.replace(day=today.day + 1)

with get_db_session() as db:
    teams = {t.id: t.name for t in db.query(Team).all()}
    fixtures = db.query(Fixture).filter(Fixture.date >= today, Fixture.date < tomorrow).all()

pipeline = FeaturePipeline()
preds = []
for f in fixtures:
    try:
        with get_db_session() as db:
            fix = db.query(Fixture).filter(Fixture.id == f.id).first()
            feat = pipeline.calculate_fixture_features(fix)
            if feat and feat.features:
                X = pd.DataFrame([feat.features]).reindex(columns=feature_cols, fill_value=0)
                preds.append({'home': teams[f.home_team_id], 'away': teams[f.away_team_id],
                    'pred': model.predict(X)[0], 'conf': max(model.predict_proba(X)[0])})
    except: pass

for i, p in enumerate(sorted(preds, key=lambda x: -x['conf'])[:10], 1):
    winner = p['home'] if p['pred'] == 1 else p['away']
    print(f'{i}. {p[\"home\"]} vs {p[\"away\"]} → {winner} ({p[\"conf\"]:.0%})')
"
```

## 🤖 Modelo

- **Algoritmo**: Random Forest
- **Features**: 156 (forma, clasificación, H2H)
- **Entrenado con**: 5 grandes ligas (7,234 partidos de 2023-2024)
- **Target**: 1 = Local gana, 0 = Visitante gana
- **Empates**: Excluidos

## 📁 Estructura

```
AnalizadorFutbol/
├── backend/
│   ├── models/trained/main_model.pkl  # Modelo entrenado
│   ├── data/training_data.csv         # Datos de entrenamiento
│   ├── src/
│   │   ├── api/                       # FastAPI
│   │   ├── data/features/             # Feature engineering
│   │   └── db/                        # PostgreSQL models
│   └── requirements.txt
├── frontend/                          # Next.js dashboard
└── PROJECT_CONTEXT.md                 # Documentación completa
```

## 📖 Documentación

Ver **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** para documentación completa con:
- Scripts de predicción detallados
- Sincronización de datos
- Lista completa de features
- Notas de validación

---

*Desarrollado con 🤖 ML + ⚽ Fútbol*