# 🚀 Guía de Desarrollo

## Requisitos Previos

- Python 3.11+
- PostgreSQL 15+
- Node.js 18+ (para frontend)
- Git

## Setup Inicial

### 1. Clonar repositorio
```bash
git clone https://github.com/JaimeLaraC/AnalizadorFutbol.git
cd AnalizadorFutbol
```

### 2. Configurar Backend

```bash
cd backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Base de Datos

```bash
# Crear base de datos PostgreSQL
createdb analizador_futbol

# O usando psql:
psql -U postgres
CREATE DATABASE analizador_futbol;
```

### 4. Variables de Entorno

```bash
# Copiar template
cp .env.example backend/.env

# Editar con tus valores
nano backend/.env
```

```env
API_FOOTBALL_KEY=tu_api_key_aqui
DATABASE_URL=postgresql://usuario:password@localhost:5432/analizador_futbol
DEBUG=true
LOG_LEVEL=INFO
```

### 5. Ejecutar Migraciones

```bash
cd backend
alembic upgrade head
```

---

## Desarrollo

### Estructura de Ramas (Git Flow)

```bash
# Crear nueva feature
git checkout develop
git pull origin develop
git checkout -b feature/nombre-feature

# Trabajar...
git add .
git commit -m "feat: descripción"
git push origin feature/nombre-feature

# Crear PR en GitHub
```

### Ejecutar Backend

```bash
cd backend
source venv/bin/activate

# Desarrollo (con reload)
uvicorn src.api.app:app --reload --port 8000

# Ver logs
tail -f logs/analizador_*.log
```

### Ejecutar Tests

```bash
cd backend
pytest tests/ -v

# Con coverage
pytest tests/ -v --cov=src --cov-report=html
```

---

## Tareas Comunes

### Añadir Migración de BD

```bash
cd backend

# Generar migración automática
alembic revision --autogenerate -m "descripcion_cambio"

# Aplicar
alembic upgrade head

# Revertir
alembic downgrade -1
```

### Probar Cliente API

```python
from src.api_client import CachedAPIClient

with CachedAPIClient() as client:
    # Obtener partidos de hoy
    response = client.get_fixtures(date="2024-12-11")
    
    if response.success:
        for fixture in response.data:
            print(fixture)
    
    # Ver estadísticas del caché
    print(client.get_cache_stats())
```

### Limpiar Caché

```python
from src.api_client import CachedAPIClient

client = CachedAPIClient()
client.clear_cache()  # Limpiar todo
client.cleanup_cache()  # Solo expirados
```

---

## Convenciones de Código

### Python
- **Formato**: Black, isort
- **Linting**: Flake8
- **Types**: Mypy (opcional)
- **Docstrings**: Google style

```python
def calculate_features(
    team_id: int,
    num_matches: int = 5
) -> Dict[str, float]:
    """
    Calcula features de un equipo.
    
    Args:
        team_id: ID del equipo
        num_matches: Número de partidos a considerar
        
    Returns:
        Diccionario con features calculadas
    """
    pass
```

### Commits (Conventional Commits)

```
feat: nueva funcionalidad
fix: corrección de bug
docs: documentación
refactor: refactorización
test: tests
chore: mantenimiento
```

---

## Solución de Problemas

### Error de conexión a PostgreSQL
```bash
# Verificar que PostgreSQL está corriendo
sudo systemctl status postgresql

# Verificar conexión
psql -U postgres -d analizador_futbol
```

### Error de API Key
```bash
# Verificar que .env existe y tiene la key
cat backend/.env | grep API_FOOTBALL

# Probar key manualmente
curl -H "x-apisports-key: TU_KEY" \
  "https://v3.football.api-sports.io/status"
```

### Caché corrupto
```bash
# Limpiar caché manualmente
rm -rf backend/data/cache/*.json
```

---

## Recursos

- [API-Football Docs](https://www.api-football.com/documentation-v3)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Alembic Docs](https://alembic.sqlalchemy.org/)
