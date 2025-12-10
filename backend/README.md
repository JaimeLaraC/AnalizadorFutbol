# Backend - AnalizadorFutbol

API REST y modelos de Machine Learning para predicción de partidos de fútbol.

## Estructura

```
src/
├── api_client/     # Cliente API-Football
├── data/           # Procesamiento de datos
├── models/         # Modelos ML
├── api/            # FastAPI REST
├── db/             # Modelos de base de datos
└── scheduler/      # Jobs programados
```

## Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuración

Copiar `.env.example` a `.env` y completar las variables.

## Ejecución

```bash
# Desarrollo
uvicorn src.api.app:app --reload

# Producción
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

## Tests

```bash
pytest tests/ -v
```
