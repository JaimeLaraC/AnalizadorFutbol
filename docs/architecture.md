# 🏗️ Arquitectura del Sistema

## Visión General

Sistema de predicción de partidos de fútbol basado en Machine Learning que procesa datos de API-Football para generar predicciones diarias con alta fiabilidad.

```mermaid
graph TB
    subgraph "Fuentes de Datos"
        API[API-Football Pro]
    end
    
    subgraph "Backend Python"
        CLIENT[API Client + Cache]
        COLLECTOR[Data Collector]
        FEATURES[Feature Engineer]
        MODEL[ML Model]
        SCHEDULER[Scheduler]
        FASTAPI[FastAPI REST]
    end
    
    subgraph "Base de Datos"
        POSTGRES[(PostgreSQL)]
    end
    
    subgraph "Frontend"
        NEXTJS[Next.js Dashboard]
    end
    
    API --> CLIENT
    CLIENT --> COLLECTOR
    COLLECTOR --> POSTGRES
    POSTGRES --> FEATURES
    FEATURES --> MODEL
    MODEL --> FASTAPI
    SCHEDULER --> COLLECTOR
    SCHEDULER --> MODEL
    FASTAPI --> NEXTJS
```

---

## Componentes Principales

### 1. API Client (`src/api_client/`)

```mermaid
classDiagram
    class APIFootballClient {
        +api_key: str
        +base_url: str
        +get_fixtures()
        +get_standings()
        +get_teams()
        +get_odds()
        +get_predictions()
    }
    
    class APICache {
        +cache_dir: Path
        +get()
        +set()
        +cleanup_expired()
    }
    
    class CachedAPIClient {
        +cache: APICache
        +get_fixtures()
        +force_refresh: bool
    }
    
    APIFootballClient <|-- CachedAPIClient
    CachedAPIClient --> APICache
```

**Características:**
- Rate limiting automático (100 req/min)
- Caché basado en archivos con TTL configurable
- Logging estructurado con loguru
- Manejo de errores robusto

---

### 2. Base de Datos (`src/db/`)

```mermaid
erDiagram
    LEAGUES ||--o{ TEAMS : contains
    LEAGUES ||--o{ FIXTURES : hosts
    LEAGUES ||--o{ STANDINGS : has
    
    TEAMS ||--o{ FIXTURES : plays_home
    TEAMS ||--o{ FIXTURES : plays_away
    TEAMS ||--o{ STANDINGS : has
    TEAMS ||--o{ TEAM_STATISTICS : has
    
    FIXTURES ||--o{ FIXTURE_STATISTICS : has
    FIXTURES ||--o{ PREDICTIONS : has
    
    LEAGUES {
        int id PK
        string name
        string country
        string type
    }
    
    TEAMS {
        int id PK
        string name
        string country
        int league_id FK
    }
    
    FIXTURES {
        int id PK
        int league_id FK
        int home_team_id FK
        int away_team_id FK
        datetime date
        int home_goals
        int away_goals
        int result
    }
    
    PREDICTIONS {
        int id PK
        int fixture_id FK
        float probability_home
        float probability_away
        float confidence
        bool is_top_5
        bool is_correct
    }
```

**Repositorios disponibles:**
- `LeagueRepository` - CRUD ligas
- `TeamRepository` - CRUD equipos
- `FixtureRepository` - CRUD partidos
- `StandingRepository` - CRUD clasificaciones
- `PredictionRepository` - CRUD predicciones + stats

---

### 3. Feature Engineering (`src/data/`)

```mermaid
graph LR
    subgraph "Datos Crudos"
        FIX[Fixtures]
        STAND[Standings]
        STATS[Statistics]
        H2H[Head-to-Head]
        ODDS[Odds]
    end
    
    subgraph "Features Calculadas"
        FORM[Forma 5-10 partidos]
        POS[Posición Liga]
        HOME[Stats Local/Visitante]
        HIST[Historial H2H]
        MARKET[Probabilidades Mercado]
    end
    
    subgraph "Dataset"
        TRAIN[Training Set]
        PRED[Prediction Set]
    end
    
    FIX --> FORM
    STAND --> POS
    STATS --> HOME
    H2H --> HIST
    ODDS --> MARKET
    
    FORM --> TRAIN
    POS --> TRAIN
    HOME --> TRAIN
    HIST --> TRAIN
    MARKET --> TRAIN
    
    FORM --> PRED
    POS --> PRED
    HOME --> PRED
    HIST --> PRED
    MARKET --> PRED
```

**Features principales (~69):**
- Forma histórica (rolling windows)
- Estadísticas de temporada
- Contexto de liga
- Head-to-head
- Cuotas del mercado

---

### 4. Modelo ML (`src/models/`)

```mermaid
flowchart TD
    A[Dataset Training] --> B[Preprocesamiento]
    B --> C[Train/Val Split]
    C --> D{Modelo}
    
    D --> E[Logistic Regression]
    D --> F[XGBoost]
    D --> G[LightGBM]
    
    E --> H[Calibración]
    F --> H
    G --> H
    
    H --> I[Evaluación]
    I --> J{Accuracy > 65%?}
    J -->|Sí| K[Guardar Modelo]
    J -->|No| L[Ajustar Hiperparámetros]
    L --> D
```

**Flujo de predicción:**
1. Obtener partidos del día
2. Calcular features pre-partido
3. Predecir P(home) y P(away)
4. Filtrar por umbral 75%
5. Seleccionar Top 5 por confianza

---

### 5. API REST (`src/api/`)

**Endpoints principales:**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/predictions/today` | Top 5 predicciones de hoy |
| GET | `/predictions/history` | Histórico de predicciones |
| GET | `/predictions/{id}` | Detalle de predicción |
| GET | `/stats/accuracy` | Estadísticas del modelo |
| GET | `/fixtures/upcoming` | Próximos partidos |

---

### 6. Frontend Dashboard

```mermaid
graph TB
    subgraph "Páginas"
        HOME[/ Dashboard Principal]
        HIST[/history Histórico]
        STATS[/stats Estadísticas]
    end
    
    subgraph "Componentes"
        TOP5[Top 5 Cards]
        CHART[Gráficos ROI]
        TABLE[Tabla Predicciones]
        FILTER[Filtros]
    end
    
    HOME --> TOP5
    HOME --> CHART
    HIST --> TABLE
    HIST --> FILTER
    STATS --> CHART
```

---

## Flujo de Datos Diario

```mermaid
sequenceDiagram
    participant S as Scheduler
    participant C as Collector
    participant DB as PostgreSQL
    participant M as ML Model
    participant API as FastAPI
    
    Note over S: 06:00 - Recopilar fixtures
    S->>C: Activar collector
    C->>DB: Guardar fixtures del día
    
    Note over S: 08:00 - Generar predicciones
    S->>M: Calcular predicciones
    M->>DB: Leer features históricas
    M->>DB: Guardar Top 5 predicciones
    
    Note over S: 23:00 - Verificar resultados
    S->>C: Obtener resultados
    C->>DB: Actualizar fixtures
    S->>DB: Verificar predicciones
```

---

## Estructura de Directorios

```
AnalizadorFutbol/
├── backend/
│   ├── src/
│   │   ├── api_client/     # Cliente API-Football + Cache
│   │   ├── data/           # Collectors + Feature Engineering
│   │   ├── models/         # ML Models + Training
│   │   ├── api/            # FastAPI REST
│   │   ├── db/             # SQLAlchemy Models + Repos
│   │   ├── scheduler/      # Jobs programados
│   │   └── utils/          # Config + Logging
│   ├── tests/
│   ├── alembic/            # Migraciones DB
│   └── requirements.txt
├── frontend/               # Next.js Dashboard
├── docs/                   # Documentación
└── notebooks/              # Exploración + Training
```

---

## Tecnologías

| Capa | Tecnología | Versión |
|------|------------|---------|
| Runtime | Python | 3.11 |
| API Framework | FastAPI | 0.104 |
| ORM | SQLAlchemy | 2.0 |
| ML | scikit-learn, XGBoost, LightGBM | Latest |
| Database | PostgreSQL | 15+ |
| Frontend | Next.js | 14 |
| Cache | File-based (JSON) | - |
| Migrations | Alembic | 1.13 |
