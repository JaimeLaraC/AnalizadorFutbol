"""
Router para gestión de ligas.

Endpoints para obtener ligas disponibles y configurar el dataset.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

router = APIRouter()


# =====================================
# Schemas
# =====================================

class LeagueInfo(BaseModel):
    id: int
    name: str
    country: str
    flag: Optional[str] = None
    type: str
    is_enabled: bool = False
    fixtures_count: int = 0


class LeagueListResponse(BaseModel):
    total: int
    enabled: int
    leagues: List[LeagueInfo]


class EnableLeaguesRequest(BaseModel):
    league_ids: List[int]


# =====================================
# Ligas principales recomendadas
# =====================================

# Top ligas por país/región (selección curada para dataset completo)
RECOMMENDED_LEAGUES = {
    # Europa - Top 5
    140: ("La Liga", "Spain", "🇪🇸"),
    39: ("Premier League", "England", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    135: ("Serie A", "Italy", "🇮🇹"),
    78: ("Bundesliga", "Germany", "🇩🇪"),
    61: ("Ligue 1", "France", "🇫🇷"),
    
    # Europa - Segundas divisiones
    141: ("La Liga 2", "Spain", "🇪🇸"),
    40: ("Championship", "England", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    136: ("Serie B", "Italy", "🇮🇹"),
    79: ("2. Bundesliga", "Germany", "🇩🇪"),
    62: ("Ligue 2", "France", "🇫🇷"),
    
    # Europa - Otras ligas principales
    88: ("Eredivisie", "Netherlands", "🇳🇱"),
    94: ("Primeira Liga", "Portugal", "🇵🇹"),
    144: ("Jupiler Pro League", "Belgium", "🇧🇪"),
    203: ("Süper Lig", "Turkey", "🇹🇷"),
    179: ("Premiership", "Scotland", "🏴󠁧󠁢󠁳󠁣󠁴󠁿"),
    218: ("Bundesliga", "Austria", "🇦🇹"),
    207: ("Super League", "Switzerland", "🇨🇭"),
    119: ("Superliga", "Denmark", "🇩🇰"),
    113: ("Allsvenskan", "Sweden", "🇸🇪"),
    103: ("Eliteserien", "Norway", "🇳🇴"),
    244: ("Ekstraklasa", "Poland", "🇵🇱"),
    210: ("Czech Liga", "Czech-Republic", "🇨🇿"),
    271: ("Super League", "Greece", "🇬🇷"),
    197: ("Super Lig", "Russia", "🇷🇺"),
    307: ("Premier League", "Ukraine", "🇺🇦"),
    
    # Sudamérica
    128: ("Liga Profesional", "Argentina", "🇦🇷"),
    71: ("Serie A", "Brazil", "🇧🇷"),
    72: ("Serie B", "Brazil", "🇧🇷"),
    239: ("Primera División", "Chile", "🇨🇱"),
    239: ("Liga BetPlay", "Colombia", "🇨🇴"),
    
    # Norteamérica
    253: ("MLS", "USA", "🇺🇸"),
    262: ("Liga MX", "Mexico", "🇲🇽"),
    
    # Asia
    169: ("J1 League", "Japan", "🇯🇵"),
    292: ("K League 1", "Korea", "🇰🇷"),
    169: ("Super League", "China", "🇨🇳"),
    
    # África
    233: ("Premier League", "Egypt", "🇪🇬"),
    
    # Oceanía
    188: ("A-League", "Australia", "🇦🇺"),
}


# =====================================
# Endpoints
# =====================================

@router.get("/available")
async def get_available_leagues() -> LeagueListResponse:
    """
    Obtiene todas las ligas disponibles en API-Football.
    Marca cuáles están habilitadas en el dataset actual.
    """
    from src.api_client import CachedAPIClient
    from src.db import get_db_session, League, Fixture
    
    try:
        client = CachedAPIClient()
        resp = client.get_leagues()
        
        # Obtener ligas actualmente en BD
        with get_db_session() as db:
            enabled_ids = set(l.id for l in db.query(League).all())
            
            # Contar fixtures por liga
            fixture_counts = {}
            for lid in enabled_ids:
                count = db.query(Fixture).filter(Fixture.league_id == lid).count()
                fixture_counts[lid] = count
        
        leagues = []
        for l in resp.data:
            if l.get('league', {}).get('type') != 'League':
                continue
                
            league = l['league']
            country = l['country']
            
            # Solo incluir ligas con temporadas recientes
            seasons = l.get('seasons', [])
            recent = [s for s in seasons if s.get('year') >= 2024]
            if not recent:
                continue
            
            lid = league['id']
            leagues.append(LeagueInfo(
                id=lid,
                name=league['name'],
                country=country.get('name', 'Unknown'),
                flag=country.get('flag'),
                type=league.get('type', 'League'),
                is_enabled=lid in enabled_ids,
                fixtures_count=fixture_counts.get(lid, 0)
            ))
        
        # Ordenar: primero habilitadas, luego por país
        leagues.sort(key=lambda x: (not x.is_enabled, x.country, x.name))
        
        return LeagueListResponse(
            total=len(leagues),
            enabled=len(enabled_ids),
            leagues=leagues
        )
        
    except Exception as e:
        logger.error(f"Error getting leagues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommended")
async def get_recommended_leagues() -> List[LeagueInfo]:
    """
    Obtiene la lista de ligas recomendadas para un dataset completo.
    """
    from src.db import get_db_session, League, Fixture
    
    with get_db_session() as db:
        enabled_ids = set(l.id for l in db.query(League).all())
        fixture_counts = {}
        for lid in enabled_ids:
            count = db.query(Fixture).filter(Fixture.league_id == lid).count()
            fixture_counts[lid] = count
    
    leagues = []
    for lid, (name, country, flag) in RECOMMENDED_LEAGUES.items():
        leagues.append(LeagueInfo(
            id=lid,
            name=name,
            country=country,
            flag=flag,
            type="League",
            is_enabled=lid in enabled_ids,
            fixtures_count=fixture_counts.get(lid, 0)
        ))
    
    return leagues


@router.get("/enabled")
async def get_enabled_leagues() -> List[LeagueInfo]:
    """
    Obtiene las ligas actualmente habilitadas en la base de datos.
    """
    from src.db import get_db_session, League, Fixture
    
    with get_db_session() as db:
        leagues_db = db.query(League).all()
        
        result = []
        for l in leagues_db:
            count = db.query(Fixture).filter(Fixture.league_id == l.id).count()
            
            # Buscar flag en recomendadas
            flag = RECOMMENDED_LEAGUES.get(l.id, (None, None, None))[2]
            
            result.append(LeagueInfo(
                id=l.id,
                name=l.name,
                country=l.country or "Unknown",
                flag=flag,
                type="League",
                is_enabled=True,
                fixtures_count=count
            ))
        
        return result
