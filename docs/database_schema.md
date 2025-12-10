# 🗄️ Esquema de Base de Datos

## Diagrama ER Completo

```mermaid
erDiagram
    leagues ||--o{ teams : "has"
    leagues ||--o{ fixtures : "hosts"
    leagues ||--o{ standings : "contains"
    leagues ||--o{ team_statistics : "season_stats"
    
    teams ||--o{ fixtures : "home_team"
    teams ||--o{ fixtures : "away_team"
    teams ||--o{ standings : "position"
    teams ||--o{ team_statistics : "stats"
    teams ||--o{ head_to_head : "team1"
    teams ||--o{ head_to_head : "team2"
    
    fixtures ||--o{ fixture_statistics : "match_stats"
    fixtures ||--o{ predictions : "prediction"
    
    leagues {
        integer id PK "API-Football ID"
        varchar name "Nombre de la liga"
        varchar country "País"
        varchar country_code "Código ISO"
        varchar logo "URL del logo"
        varchar type "League/Cup"
        timestamp created_at
        timestamp updated_at
    }
    
    teams {
        integer id PK "API-Football ID"
        varchar name "Nombre del equipo"
        varchar code "Código 3 letras"
        varchar country "País"
        varchar logo "URL del logo"
        integer founded "Año fundación"
        varchar venue_name "Estadio"
        integer venue_capacity "Capacidad"
        integer league_id FK
        timestamp created_at
        timestamp updated_at
    }
    
    fixtures {
        integer id PK "API-Football ID"
        integer league_id FK
        integer season "Año temporada"
        varchar round "Jornada"
        integer home_team_id FK
        integer away_team_id FK
        timestamp date "Fecha y hora"
        integer timestamp "Unix timestamp"
        varchar status "NS/FT/PST/etc"
        integer home_goals
        integer away_goals
        integer home_goals_halftime
        integer away_goals_halftime
        integer result "1=home 0=away null=draw"
        varchar venue_name
        varchar venue_city
        timestamp created_at
        timestamp updated_at
    }
    
    standings {
        integer id PK
        integer league_id FK
        integer season
        integer team_id FK
        integer rank "Posición"
        integer points
        integer goals_diff
        varchar group_name
        varchar form "WWDLW"
        varchar status "up/down/same"
        varchar description "Champions/Relegation"
        integer played
        integer win
        integer draw
        integer lose
        integer goals_for
        integer goals_against
        integer home_played
        integer home_win
        integer home_draw
        integer home_lose
        integer home_goals_for
        integer home_goals_against
        integer away_played
        integer away_win
        integer away_draw
        integer away_lose
        integer away_goals_for
        integer away_goals_against
        timestamp updated_at
    }
    
    fixture_statistics {
        integer id PK
        integer fixture_id FK
        integer team_id FK
        integer shots_total
        integer shots_on_goal
        integer shots_off_goal
        integer shots_blocked
        integer shots_inside_box
        integer shots_outside_box
        float possession
        integer passes_total
        integer passes_accurate
        float passes_percentage
        integer fouls
        integer corners
        integer offsides
        integer yellow_cards
        integer red_cards
        integer goalkeeper_saves
        float expected_goals "xG"
        timestamp created_at
    }
    
    team_statistics {
        integer id PK
        integer team_id FK
        integer league_id FK
        integer season
        varchar form
        integer goals_for_total
        integer goals_for_home
        integer goals_for_away
        integer goals_against_total
        integer goals_against_home
        integer goals_against_away
        float goals_for_avg
        float goals_against_avg
        integer clean_sheet_total
        integer clean_sheet_home
        integer clean_sheet_away
        integer failed_to_score_total
        integer penalty_scored
        integer penalty_missed
        varchar most_used_formation
        json extra_data
        timestamp updated_at
    }
    
    predictions {
        integer id PK
        integer fixture_id FK
        integer predicted_winner "1=home 2=away"
        float probability_home
        float probability_away
        float confidence "max(p_home p_away)"
        integer api_predicted_winner
        float api_probability_home
        float api_probability_away
        varchar api_advice
        float odds_home
        float odds_draw
        float odds_away
        integer actual_result
        boolean is_correct
        boolean is_top_5
        integer rank_of_day "1-5"
        timestamp created_at
        timestamp verified_at
        varchar model_version
        json features_snapshot
    }
    
    head_to_head {
        integer id PK
        integer team1_id FK
        integer team2_id FK
        integer total_matches
        integer team1_wins
        integer team2_wins
        integer draws
        integer team1_goals
        integer team2_goals
        integer last_fixture_id
        timestamp updated_at
    }
```

---

## Tablas Detalladas

### `leagues`
Almacena información de ligas y competiciones.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| id | INTEGER | NO | PK, ID de API-Football |
| name | VARCHAR(255) | NO | Nombre de la liga |
| country | VARCHAR(100) | SÍ | País |
| country_code | VARCHAR(3) | SÍ | Código ISO |
| logo | VARCHAR(500) | SÍ | URL del logo |
| type | VARCHAR(50) | SÍ | League/Cup |

---

### `teams`
Información de equipos.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| id | INTEGER | NO | PK, ID de API-Football |
| name | VARCHAR(255) | NO | Nombre del equipo |
| code | VARCHAR(10) | SÍ | Código 3 letras |
| country | VARCHAR(100) | SÍ | País |
| founded | INTEGER | SÍ | Año de fundación |
| venue_name | VARCHAR(255) | SÍ | Nombre del estadio |
| venue_capacity | INTEGER | SÍ | Capacidad |
| league_id | INTEGER | SÍ | FK → leagues.id |

---

### `fixtures`
Partidos/fixtures con resultados.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| id | INTEGER | NO | PK, ID de API-Football |
| league_id | INTEGER | NO | FK → leagues.id |
| season | INTEGER | NO | Año de temporada |
| round | VARCHAR(100) | SÍ | Jornada/Ronda |
| home_team_id | INTEGER | NO | FK → teams.id |
| away_team_id | INTEGER | NO | FK → teams.id |
| date | TIMESTAMP | NO | Fecha y hora |
| status | VARCHAR(50) | SÍ | NS, FT, PST, etc. |
| home_goals | INTEGER | SÍ | Goles local |
| away_goals | INTEGER | SÍ | Goles visitante |
| **result** | INTEGER | SÍ | **1=local, 0=visitante, NULL=empate** |

**Índices:**
- `ix_fixtures_date` - Por fecha
- `ix_fixtures_league_season` - Por liga y temporada

---

### `predictions`
Predicciones del modelo con verificación.

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| id | INTEGER | NO | PK, autoincrement |
| fixture_id | INTEGER | NO | FK → fixtures.id |
| predicted_winner | INTEGER | SÍ | 1=home, 2=away |
| probability_home | FLOAT | NO | P(local gana) |
| probability_away | FLOAT | NO | P(visitante gana) |
| confidence | FLOAT | NO | max(p_home, p_away) |
| is_top_5 | BOOLEAN | NO | ¿Está en Top 5 del día? |
| rank_of_day | INTEGER | SÍ | Posición 1-5 si es Top 5 |
| is_correct | BOOLEAN | SÍ | ¿Predicción acertada? |
| verified_at | TIMESTAMP | SÍ | Fecha de verificación |

**Índices:**
- `ix_predictions_created` - Por fecha creación
- `ix_predictions_top5` - Por is_top_5 + fecha

---

## Migraciones

### Crear migración inicial
```bash
cd backend
alembic revision --autogenerate -m "initial_schema"
```

### Aplicar migraciones
```bash
alembic upgrade head
```

### Revertir última migración
```bash
alembic downgrade -1
```

---

## Notas de Diseño

> [!IMPORTANT]
> **Campo `result` en `fixtures`:**  
> - `1` = Victoria local  
> - `0` = Victoria visitante  
> - `NULL` = Empate o partido no jugado  
> 
> Los empates se marcan como NULL para excluirlos del entrenamiento del modelo.

> [!TIP]
> **Uso de JSON:**  
> Los campos `extra_data` y `features_snapshot` permiten almacenar datos adicionales sin modificar el esquema.
