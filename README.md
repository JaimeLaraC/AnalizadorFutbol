# AnalizadorFutbol 🎯⚽

Sistema de Inteligencia Artificial para predicción de partidos de fútbol.

## 📋 Descripción

Modelo de Machine Learning que predice resultados de partidos de fútbol (victoria local o visitante) con el objetivo de maximizar la fiabilidad de las predicciones. El sistema analiza datos históricos y genera diariamente las **Top 5 predicciones** con mayor confianza.

## 🎯 Características

- **Predicción binaria**: Solo 1 (local gana) o 2 (visitante gana) - empates excluidos
- **Umbral de confianza**: 75% mínimo para recomendar
- **Top 5 diario**: Las 5 predicciones con mayor probabilidad
- **Cobertura global**: Todas las ligas del mundo
- **Dashboard web**: Interfaz moderna para visualizar predicciones

## 🏗️ Arquitectura

```
AnalizadorFutbol/
├── backend/          # Python API + ML
├── frontend/         # Next.js Dashboard
├── notebooks/        # Exploración y training
├── docs/             # Documentación
└── .github/          # CI/CD
```

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.11, FastAPI |
| ML | scikit-learn, XGBoost, LightGBM |
| Base de datos | PostgreSQL |
| Frontend | Next.js 14, React, Tailwind |
| API Datos | API-Football (Pro) |

## 📊 Features del Modelo

El modelo utiliza ~69 features pre-partido:
- Forma histórica del equipo
- Estadísticas agregadas de temporada
- Contexto de liga (posición, puntos)
- Head-to-head histórico
- Cuotas del mercado de apuestas
- Predicciones de API-Football

## 🚀 Instalación

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/AnalizadorFutbol.git
cd AnalizadorFutbol

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

## ⚙️ Configuración

Crear archivo `.env` en `backend/`:
```
API_FOOTBALL_KEY=tu_api_key
DATABASE_URL=postgresql://user:pass@localhost:5432/futbol_db
```

## 📖 Documentación

- [Plan de Implementación](docs/implementation_plan.md)
- [Catálogo de Features](docs/features_catalog.md)
- [Guía de Git](docs/git_guide.md)
- [ADRs](docs/adr/)

## 🔀 Git Flow

Este proyecto sigue Git Flow:
- `main` - Producción
- `develop` - Integración
- `feature/*` - Nuevas funcionalidades

Ver [Guía de Git](docs/git_guide.md) para más detalles.

## 📝 Licencia

Este proyecto es privado y de uso personal.

---

*Desarrollado con 🤖 IA + ☕ Café*