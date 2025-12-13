"""
Calculador de features de Head-to-Head.

Genera features basadas en enfrentamientos históricos entre equipos.
"""

from typing import Dict, List, Optional
from datetime import datetime

from loguru import logger

from src.db import get_db_session
from src.db.models import Fixture


class H2HCalculator:
    """
    Calcula features basadas en enfrentamientos directos.
    """
    
    def __init__(self):
        """Inicializa el calculador."""
        pass
    
    def _get_h2h_fixtures(
        self,
        team1_id: int,
        team2_id: int,
        before_date: datetime,
        limit: int = 10
    ) -> List[Dict]:
        """
        Obtiene enfrentamientos históricos entre dos equipos.
        
        Args:
            team1_id: ID del primer equipo
            team2_id: ID del segundo equipo
            before_date: Fecha límite
            limit: Máximo de partidos
            
        Returns:
            Lista de diccionarios con datos H2H
        """
        with get_db_session() as db:
            from sqlalchemy import or_, and_
            
            fixtures = db.query(Fixture).filter(
                and_(
                    Fixture.date < before_date,
                    Fixture.status == "FT",
                    or_(
                        and_(
                            Fixture.home_team_id == team1_id,
                            Fixture.away_team_id == team2_id
                        ),
                        and_(
                            Fixture.home_team_id == team2_id,
                            Fixture.away_team_id == team1_id
                        )
                    )
                )
            ).order_by(Fixture.date.desc()).limit(limit).all()
            
            # Convertir a diccionarios dentro de la sesión
            return [{
                'id': f.id,
                'home_team_id': f.home_team_id,
                'away_team_id': f.away_team_id,
                'home_goals': f.home_goals,
                'away_goals': f.away_goals,
            } for f in fixtures]
    
    def calculate_h2h_features(
        self,
        home_team_id: int,
        away_team_id: int,
        before_date: datetime
    ) -> Dict[str, float]:
        """
        Calcula features de enfrentamientos directos.
        
        Args:
            home_team_id: ID del equipo local (hoy)
            away_team_id: ID del equipo visitante (hoy)
            before_date: Fecha límite
            
        Returns:
            Diccionario de features H2H
        """
        fixtures = self._get_h2h_fixtures(
            home_team_id, away_team_id, before_date, limit=10
        )
        
        features = {}
        
        if not fixtures:
            # Sin historial H2H
            features["h2h_total_matches"] = 0.0
            features["h2h_home_wins"] = 0.0
            features["h2h_away_wins"] = 0.0
            features["h2h_draws"] = 0.0
            features["h2h_home_win_rate"] = 0.5
            features["h2h_home_goals_avg"] = 0.0
            features["h2h_away_goals_avg"] = 0.0
            return features
        
        n = len(fixtures)
        home_wins = 0
        away_wins = 0
        draws = 0
        home_goals = 0
        away_goals = 0
        
        for f in fixtures:
            # Determinar quién es quién en este partido
            if f['home_team_id'] == home_team_id:
                # home_team_id era local en este partido
                h_goals = f['home_goals'] or 0
                a_goals = f['away_goals'] or 0
            else:
                # home_team_id era visitante en este partido
                h_goals = f['away_goals'] or 0
                a_goals = f['home_goals'] or 0
            
            home_goals += h_goals
            away_goals += a_goals
            
            if h_goals > a_goals:
                home_wins += 1
            elif a_goals > h_goals:
                away_wins += 1
            else:
                draws += 1
        
        features["h2h_total_matches"] = float(n)
        features["h2h_home_wins"] = float(home_wins)
        features["h2h_away_wins"] = float(away_wins)
        features["h2h_draws"] = float(draws)
        features["h2h_home_win_rate"] = home_wins / n
        features["h2h_away_win_rate"] = away_wins / n
        features["h2h_draw_rate"] = draws / n
        features["h2h_home_goals_avg"] = home_goals / n
        features["h2h_away_goals_avg"] = away_goals / n
        features["h2h_total_goals_avg"] = (home_goals + away_goals) / n
        
        # Dominancia H2H (positivo = domina local de hoy)
        features["h2h_dominance"] = (home_wins - away_wins) / n
        
        # Resultados recientes (últimos 5 H2H)
        recent = fixtures[:5]
        recent_home_wins = sum(
            1 for f in recent 
            if (f['home_team_id'] == home_team_id and (f['home_goals'] or 0) > (f['away_goals'] or 0))
            or (f['away_team_id'] == home_team_id and (f['away_goals'] or 0) > (f['home_goals'] or 0))
        )
        features["h2h_recent_home_wins"] = float(recent_home_wins)
        features["h2h_recent_home_rate"] = recent_home_wins / len(recent) if recent else 0.5
        
        return features

