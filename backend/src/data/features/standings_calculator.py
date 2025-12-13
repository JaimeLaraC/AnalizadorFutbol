"""
Calculador de features de contexto de liga.

Genera features basadas en posiciones y estadísticas de temporada.
"""

from typing import Dict, Optional

from loguru import logger

from src.db import get_db_session, StandingRepository
from src.db.models import Standing


class StandingsCalculator:
    """
    Calcula features basadas en posiciones de liga.
    """
    
    def __init__(self):
        """Inicializa el calculador."""
        pass
    
    def _get_standing(
        self,
        team_id: int,
        league_id: int,
        season: int,
        before_date: Optional['datetime'] = None
    ) -> Optional[Dict]:
        """
        Calcula la posición de un equipo en la liga HASTA una fecha específica.
        
        IMPORTANTE: Calcula dinámicamente desde los fixtures para evitar data leakage.
        """
        from datetime import datetime
        from src.db import get_db_session, Fixture
        from sqlalchemy import or_, and_
        
        with get_db_session() as db:
            # Query base: partidos terminados del equipo en esta liga/temporada
            query = db.query(Fixture).filter(
                and_(
                    Fixture.league_id == league_id,
                    Fixture.season == season,
                    Fixture.status == "FT",
                    or_(
                        Fixture.home_team_id == team_id,
                        Fixture.away_team_id == team_id
                    )
                )
            )
            
            # Filtrar por fecha si se proporciona
            if before_date:
                query = query.filter(Fixture.date < before_date)
            
            fixtures = query.all()
            
            if not fixtures:
                return None
            
            # Calcular estadísticas desde los fixtures
            stats = {
                'rank': 10,  # Se calculará después
                'points': 0,
                'goals_diff': 0,
                'played': 0,
                'win': 0,
                'draw': 0,
                'lose': 0,
                'goals_for': 0,
                'goals_against': 0,
                'home_played': 0,
                'home_win': 0,
                'home_draw': 0,
                'home_lose': 0,
                'home_goals_for': 0,
                'home_goals_against': 0,
                'away_played': 0,
                'away_win': 0,
                'away_draw': 0,
                'away_lose': 0,
                'away_goals_for': 0,
                'away_goals_against': 0,
            }
            
            for fixture in fixtures:
                is_home = fixture.home_team_id == team_id
                home_goals = fixture.home_goals or 0
                away_goals = fixture.away_goals or 0
                
                if is_home:
                    team_goals = home_goals
                    opponent_goals = away_goals
                    stats['home_played'] += 1
                    stats['home_goals_for'] += team_goals
                    stats['home_goals_against'] += opponent_goals
                    
                    if home_goals > away_goals:
                        stats['home_win'] += 1
                        stats['win'] += 1
                        stats['points'] += 3
                    elif home_goals == away_goals:
                        stats['home_draw'] += 1
                        stats['draw'] += 1
                        stats['points'] += 1
                    else:
                        stats['home_lose'] += 1
                        stats['lose'] += 1
                else:
                    team_goals = away_goals
                    opponent_goals = home_goals
                    stats['away_played'] += 1
                    stats['away_goals_for'] += team_goals
                    stats['away_goals_against'] += opponent_goals
                    
                    if away_goals > home_goals:
                        stats['away_win'] += 1
                        stats['win'] += 1
                        stats['points'] += 3
                    elif away_goals == home_goals:
                        stats['away_draw'] += 1
                        stats['draw'] += 1
                        stats['points'] += 1
                    else:
                        stats['away_lose'] += 1
                        stats['lose'] += 1
                
                stats['played'] += 1
                stats['goals_for'] += team_goals
                stats['goals_against'] += opponent_goals
            
            stats['goals_diff'] = stats['goals_for'] - stats['goals_against']
            
            return stats
    
    def _calculate_rank(
        self,
        team_stats: Dict,
        league_id: int,
        season: int,
        before_date: Optional['datetime'] = None
    ) -> int:
        """Calcula la posición del equipo en la liga."""
        from src.db import get_db_session, Fixture
        from sqlalchemy import or_, and_
        
        with get_db_session() as db:
            # Obtener todos los equipos que han jugado en esta liga/temporada
            query = db.query(Fixture).filter(
                and_(
                    Fixture.league_id == league_id,
                    Fixture.season == season,
                    Fixture.status == "FT"
                )
            )
            if before_date:
                query = query.filter(Fixture.date < before_date)
            
            fixtures = query.all()
            
            if not fixtures:
                return 10  # Posición media por defecto
            
            # Obtener IDs de todos los equipos
            team_ids = set()
            for f in fixtures:
                team_ids.add(f.home_team_id)
                team_ids.add(f.away_team_id)
            
            # Calcular puntos de cada equipo
            team_points = {}
            for tid in team_ids:
                team_pts = 0
                team_gd = 0
                for f in fixtures:
                    if f.home_team_id == tid:
                        hg, ag = f.home_goals or 0, f.away_goals or 0
                        team_gd += hg - ag
                        if hg > ag:
                            team_pts += 3
                        elif hg == ag:
                            team_pts += 1
                    elif f.away_team_id == tid:
                        hg, ag = f.home_goals or 0, f.away_goals or 0
                        team_gd += ag - hg
                        if ag > hg:
                            team_pts += 3
                        elif hg == ag:
                            team_pts += 1
                team_points[tid] = (team_pts, team_gd)
            
            # Ordenar equipos por puntos y diferencia de goles
            sorted_teams = sorted(
                team_points.items(),
                key=lambda x: (x[1][0], x[1][1]),
                reverse=True
            )
            
            # Encontrar posición del equipo actual
            target_pts = team_stats['points']
            target_gd = team_stats['goals_diff']
            
            for rank, (tid, (pts, gd)) in enumerate(sorted_teams, 1):
                if pts == target_pts and gd == target_gd:
                    return rank
            
            return 10  # Default
    
    def calculate_standing_features(
        self,
        team_id: int,
        league_id: int,
        season: int,
        prefix: str = "",
        before_date: Optional['datetime'] = None
    ) -> Dict[str, float]:
        """
        Calcula features de posición en liga HASTA una fecha específica.
        
        Args:
            team_id: ID del equipo
            league_id: ID de la liga
            season: Temporada
            prefix: Prefijo para nombres
            before_date: Fecha límite para evitar data leakage
            
        Returns:
            Diccionario de features
        """
        standing = self._get_standing(team_id, league_id, season, before_date)
        
        if not standing:
            # Sin datos, retornar valores por defecto
            return {
                f"{prefix}position": 10.0,  # Posición media por defecto
                f"{prefix}points": 0.0,
                f"{prefix}goal_diff": 0.0,
                f"{prefix}ppg": 0.0,
            }
        
        features = {}
        
        # Posición y puntos
        features[f"{prefix}position"] = float(standing['rank'])
        features[f"{prefix}points"] = float(standing['points'])
        features[f"{prefix}goal_diff"] = float(standing['goals_diff'] or 0)
        
        # Puntos por partido
        played = standing['played'] or 1
        features[f"{prefix}ppg"] = standing['points'] / played
        
        # Estadísticas generales
        features[f"{prefix}played"] = float(standing['played'] or 0)
        features[f"{prefix}wins"] = float(standing['win'] or 0)
        features[f"{prefix}draws"] = float(standing['draw'] or 0)
        features[f"{prefix}losses"] = float(standing['lose'] or 0)
        features[f"{prefix}goals_for"] = float(standing['goals_for'] or 0)
        features[f"{prefix}goals_against"] = float(standing['goals_against'] or 0)
        
        # Ratios
        features[f"{prefix}win_ratio"] = (standing['win'] or 0) / played
        features[f"{prefix}goals_per_game"] = (standing['goals_for'] or 0) / played
        features[f"{prefix}conceded_per_game"] = (standing['goals_against'] or 0) / played
        
        # Stats como local
        home_played = standing['home_played'] or 1
        features[f"{prefix}home_wins"] = float(standing['home_win'] or 0)
        features[f"{prefix}home_ppg"] = (
            (standing['home_win'] or 0) * 3 + (standing['home_draw'] or 0)
        ) / home_played
        features[f"{prefix}home_goals_per_game"] = (standing['home_goals_for'] or 0) / home_played
        
        # Stats como visitante
        away_played = standing['away_played'] or 1
        features[f"{prefix}away_wins"] = float(standing['away_win'] or 0)
        features[f"{prefix}away_ppg"] = (
            (standing['away_win'] or 0) * 3 + (standing['away_draw'] or 0)
        ) / away_played
        features[f"{prefix}away_goals_per_game"] = (standing['away_goals_for'] or 0) / away_played
        
        return features
    
    def calculate_relative_features(
        self,
        home_team_id: int,
        away_team_id: int,
        league_id: int,
        season: int,
        before_date: Optional['datetime'] = None
    ) -> Dict[str, float]:
        """
        Calcula features relativas entre dos equipos HASTA una fecha específica.
        
        Args:
            home_team_id: ID del equipo local
            away_team_id: ID del equipo visitante
            league_id: ID de la liga
            season: Temporada
            before_date: Fecha límite para evitar data leakage
            
        Returns:
            Diccionario de features diferenciales
        """
        home_features = self.calculate_standing_features(
            home_team_id, league_id, season, "home_", before_date
        )
        away_features = self.calculate_standing_features(
            away_team_id, league_id, season, "away_", before_date
        )
        
        features = {}
        
        # Combinar features individuales
        features.update(home_features)
        features.update(away_features)
        
        # Calcular diferencias
        features["diff_position"] = (
            home_features["home_position"] - away_features["away_position"]
        )
        features["diff_points"] = (
            home_features["home_points"] - away_features["away_points"]
        )
        features["diff_goal_diff"] = (
            home_features["home_goal_diff"] - away_features["away_goal_diff"]
        )
        features["diff_ppg"] = (
            home_features["home_ppg"] - away_features["away_ppg"]
        )
        features["diff_win_ratio"] = (
            home_features["home_win_ratio"] - away_features["away_win_ratio"]
        )
        
        return features
