"""
Calculador de features de forma del equipo.

Genera features basadas en resultados recientes de los equipos.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from loguru import logger

from src.db import get_db_session, FixtureRepository
from src.db.models import Fixture


class FormCalculator:
    """
    Calcula features de forma basadas en partidos recientes.
    """
    
    WINDOWS = [3, 5, 10]  # Partidos a considerar
    
    def __init__(self):
        """Inicializa el calculador."""
        pass
    
    def _get_recent_fixtures(
        self,
        team_id: int,
        before_date: datetime,
        limit: int = 10,
        home_only: bool = False,
        away_only: bool = False
    ) -> List[Dict]:
        """
        Obtiene partidos recientes de un equipo antes de una fecha.
        
        Args:
            team_id: ID del equipo
            before_date: Fecha límite (excluida)
            limit: Máximo de partidos
            home_only: Solo partidos como local
            away_only: Solo partidos como visitante
            
        Returns:
            Lista de fixtures como dicts ordenados por fecha descendente
        """
        from src.db.models import Fixture
        from sqlalchemy import or_
        
        with get_db_session() as db:
            # Query directa con filtro de fecha ANTES del partido
            query = db.query(Fixture).filter(
                Fixture.date < before_date,
                Fixture.status == "FT"
            )
            
            # Filtrar por equipo
            if home_only:
                query = query.filter(Fixture.home_team_id == team_id)
            elif away_only:
                query = query.filter(Fixture.away_team_id == team_id)
            else:
                query = query.filter(
                    or_(
                        Fixture.home_team_id == team_id,
                        Fixture.away_team_id == team_id
                    )
                )
            
            # Ordenar por fecha descendente y limitar
            fixtures = query.order_by(Fixture.date.desc()).limit(limit).all()
            
            # Extraer como dicts mientras sesión activa
            return [
                {
                    'id': f.id,
                    'home_team_id': f.home_team_id,
                    'away_team_id': f.away_team_id,
                    'home_goals': f.home_goals,
                    'away_goals': f.away_goals,
                    'date': f.date,
                    'status': f.status,
                }
                for f in fixtures
            ]
    
    def _calculate_points(
        self,
        fixtures: List[Dict],
        team_id: int
    ) -> int:
        """Calcula puntos obtenidos (W=3, D=1, L=0)."""
        points = 0
        for f in fixtures:
            is_home = f['home_team_id'] == team_id
            home_goals = f['home_goals'] or 0
            away_goals = f['away_goals'] or 0
            
            if is_home:
                if home_goals > away_goals:
                    points += 3
                elif home_goals == away_goals:
                    points += 1
            else:
                if away_goals > home_goals:
                    points += 3
                elif home_goals == away_goals:
                    points += 1
        
        return points
    
    def _calculate_goals(
        self,
        fixtures: List[Dict],
        team_id: int
    ) -> tuple:
        """Calcula goles a favor y en contra."""
        goals_for = 0
        goals_against = 0
        
        for f in fixtures:
            is_home = f['home_team_id'] == team_id
            home_goals = f['home_goals'] or 0
            away_goals = f['away_goals'] or 0
            
            if is_home:
                goals_for += home_goals
                goals_against += away_goals
            else:
                goals_for += away_goals
                goals_against += home_goals
        
        return goals_for, goals_against
    
    def _calculate_wins_draws_losses(
        self,
        fixtures: List[Dict],
        team_id: int
    ) -> tuple:
        """Calcula victorias, empates y derrotas."""
        wins = draws = losses = 0
        
        for f in fixtures:
            is_home = f['home_team_id'] == team_id
            home_goals = f['home_goals'] or 0
            away_goals = f['away_goals'] or 0
            
            if is_home:
                if home_goals > away_goals:
                    wins += 1
                elif home_goals == away_goals:
                    draws += 1
                else:
                    losses += 1
            else:
                if away_goals > home_goals:
                    wins += 1
                elif home_goals == away_goals:
                    draws += 1
                else:
                    losses += 1
        
        return wins, draws, losses
    
    def _calculate_streak(
        self,
        fixtures: List[Dict],
        team_id: int
    ) -> Dict[str, int]:
        """Calcula rachas actuales."""
        win_streak = 0
        unbeaten_streak = 0
        winless_streak = 0
        
        for f in fixtures:
            is_home = f['home_team_id'] == team_id
            home_goals = f['home_goals'] or 0
            away_goals = f['away_goals'] or 0
            
            if is_home:
                won = home_goals > away_goals
                drew = home_goals == away_goals
                lost = home_goals < away_goals
            else:
                won = away_goals > home_goals
                drew = home_goals == away_goals
                lost = away_goals < home_goals
            
            # Contar rachas consecutivas
            if won:
                if win_streak >= 0:
                    win_streak += 1
                if unbeaten_streak >= 0:
                    unbeaten_streak += 1
                winless_streak = 0
            elif drew:
                win_streak = 0
                if unbeaten_streak >= 0:
                    unbeaten_streak += 1
                if winless_streak >= 0:
                    winless_streak += 1
            else:  # lost
                win_streak = 0
                unbeaten_streak = 0
                if winless_streak >= 0:
                    winless_streak += 1
        
        return {
            "win_streak": win_streak,
            "unbeaten_streak": unbeaten_streak,
            "winless_streak": winless_streak
        }
    
    def _calculate_clean_sheets(
        self,
        fixtures: List[Dict],
        team_id: int
    ) -> tuple:
        """Calcula porterías a cero y partidos sin marcar."""
        clean_sheets = 0
        failed_to_score = 0
        
        for f in fixtures:
            is_home = f['home_team_id'] == team_id
            home_goals = f['home_goals'] or 0
            away_goals = f['away_goals'] or 0
            
            if is_home:
                if away_goals == 0:
                    clean_sheets += 1
                if home_goals == 0:
                    failed_to_score += 1
            else:
                if home_goals == 0:
                    clean_sheets += 1
                if away_goals == 0:
                    failed_to_score += 1
        
        return clean_sheets, failed_to_score
    
    def calculate_form_features(
        self,
        team_id: int,
        before_date: datetime,
        prefix: str = ""
    ) -> Dict[str, float]:
        """
        Calcula todas las features de forma para un equipo.
        
        Args:
            team_id: ID del equipo
            before_date: Fecha límite
            prefix: Prefijo para nombres (ej: "home_", "away_")
            
        Returns:
            Diccionario de features
        """
        features = {}
        
        # Obtener partidos recientes (máximo window)
        max_window = max(self.WINDOWS)
        fixtures = self._get_recent_fixtures(team_id, before_date, max_window)
        
        # Calcular para cada ventana - SIEMPRE generar todas las features
        for w in self.WINDOWS:
            window_fixtures = fixtures[:w] if fixtures else []
            n = len(window_fixtures)
            
            if n == 0:
                # Sin datos: usar valores por defecto
                features[f"{prefix}points_last_{w}"] = 0.0
                features[f"{prefix}points_avg_{w}"] = 0.0
                features[f"{prefix}goals_for_last_{w}"] = 0.0
                features[f"{prefix}goals_against_last_{w}"] = 0.0
                features[f"{prefix}goals_for_avg_{w}"] = 0.0
                features[f"{prefix}goals_against_avg_{w}"] = 0.0
                features[f"{prefix}goal_diff_{w}"] = 0.0
                features[f"{prefix}wins_last_{w}"] = 0.0
                features[f"{prefix}draws_last_{w}"] = 0.0
                features[f"{prefix}losses_last_{w}"] = 0.0
                features[f"{prefix}win_rate_{w}"] = 0.0
                features[f"{prefix}clean_sheets_{w}"] = 0.0
                features[f"{prefix}failed_to_score_{w}"] = 0.0
            else:
                # Puntos
                points = self._calculate_points(window_fixtures, team_id)
                features[f"{prefix}points_last_{w}"] = float(points)
                features[f"{prefix}points_avg_{w}"] = points / n
                
                # Goles
                gf, ga = self._calculate_goals(window_fixtures, team_id)
                features[f"{prefix}goals_for_last_{w}"] = float(gf)
                features[f"{prefix}goals_against_last_{w}"] = float(ga)
                features[f"{prefix}goals_for_avg_{w}"] = gf / n
                features[f"{prefix}goals_against_avg_{w}"] = ga / n
                features[f"{prefix}goal_diff_{w}"] = float(gf - ga)
                
                # W/D/L
                wins, draws, losses = self._calculate_wins_draws_losses(window_fixtures, team_id)
                features[f"{prefix}wins_last_{w}"] = float(wins)
                features[f"{prefix}draws_last_{w}"] = float(draws)
                features[f"{prefix}losses_last_{w}"] = float(losses)
                features[f"{prefix}win_rate_{w}"] = wins / n
                
                # Clean sheets
                cs, fts = self._calculate_clean_sheets(window_fixtures, team_id)
                features[f"{prefix}clean_sheets_{w}"] = float(cs)
                features[f"{prefix}failed_to_score_{w}"] = float(fts)
        
        # Rachas (solo con últimos 10 o lo que haya)
        if fixtures:
            streaks = self._calculate_streak(fixtures[:10], team_id)
            features[f"{prefix}win_streak"] = float(streaks["win_streak"])
            features[f"{prefix}unbeaten_streak"] = float(streaks["unbeaten_streak"])
            features[f"{prefix}winless_streak"] = float(streaks["winless_streak"])
        else:
            features[f"{prefix}win_streak"] = 0.0
            features[f"{prefix}unbeaten_streak"] = 0.0
            features[f"{prefix}winless_streak"] = 0.0
        
        return features
    
    def calculate_home_away_form(
        self,
        team_id: int,
        before_date: datetime,
        is_home: bool
    ) -> Dict[str, float]:
        """
        Calcula forma específica de local o visitante.
        
        Args:
            team_id: ID del equipo
            before_date: Fecha límite
            is_home: Si calcular forma como local o visitante
            
        Returns:
            Diccionario de features
        """
        prefix = "home_" if is_home else "away_"
        
        with get_db_session() as db:
            repo = FixtureRepository(db)
            fixtures = repo.get_team_fixtures(team_id, limit=20)
            
            # Filtrar por home/away y extraer como dicts
            filtered = []
            for f in fixtures:
                if f.date < before_date and f.status == "FT":
                    if is_home and f.home_team_id == team_id:
                        filtered.append({
                            'home_team_id': f.home_team_id,
                            'away_team_id': f.away_team_id,
                            'home_goals': f.home_goals,
                            'away_goals': f.away_goals,
                        })
                    elif not is_home and f.away_team_id == team_id:
                        filtered.append({
                            'home_team_id': f.home_team_id,
                            'away_team_id': f.away_team_id,
                            'home_goals': f.home_goals,
                            'away_goals': f.away_goals,
                        })
                    if len(filtered) >= 5:
                        break
        
        features = {}
        n = len(filtered)
        
        if n == 0:
            features[f"{prefix}form_points_5"] = 0.0
            features[f"{prefix}form_goals_avg"] = 0.0
        else:
            points = self._calculate_points(filtered, team_id)
            gf, ga = self._calculate_goals(filtered, team_id)
            
            features[f"{prefix}form_points_5"] = float(points)
            features[f"{prefix}form_goals_avg"] = gf / n
        
        return features
