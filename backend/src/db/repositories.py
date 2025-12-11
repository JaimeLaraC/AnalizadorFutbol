"""
Repositorios para acceso a datos.

Proporciona métodos de alto nivel para CRUD de las entidades.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from .models import (
    League, Team, Fixture, Standing, 
    FixtureStatistics, TeamStatistics, Prediction, HeadToHead
)


class LeagueRepository:
    """Repositorio para ligas."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, league_id: int) -> Optional[League]:
        """Obtiene una liga por ID."""
        return self.db.query(League).filter(League.id == league_id).first()
    
    def get_all(self) -> List[League]:
        """Obtiene todas las ligas."""
        return self.db.query(League).all()
    
    def get_by_country(self, country: str) -> List[League]:
        """Obtiene ligas de un país."""
        return self.db.query(League).filter(League.country == country).all()
    
    def upsert(self, league_data: Dict[str, Any]) -> League:
        """Inserta o actualiza una liga."""
        league = self.get_by_id(league_data["id"])
        
        if league:
            for key, value in league_data.items():
                setattr(league, key, value)
        else:
            league = League(**league_data)
            self.db.add(league)
        
        self.db.flush()
        return league


class TeamRepository:
    """Repositorio para equipos."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, team_id: int) -> Optional[Team]:
        """Obtiene un equipo por ID."""
        return self.db.query(Team).filter(Team.id == team_id).first()
    
    def get_by_league(self, league_id: int) -> List[Team]:
        """Obtiene equipos de una liga."""
        return self.db.query(Team).filter(Team.league_id == league_id).all()
    
    def search_by_name(self, name: str) -> List[Team]:
        """Busca equipos por nombre."""
        return self.db.query(Team).filter(
            Team.name.ilike(f"%{name}%")
        ).all()
    
    def upsert(self, team_data: Dict[str, Any]) -> Team:
        """Inserta o actualiza un equipo."""
        team = self.get_by_id(team_data["id"])
        
        if team:
            for key, value in team_data.items():
                setattr(team, key, value)
        else:
            team = Team(**team_data)
            self.db.add(team)
        
        self.db.flush()
        return team


class FixtureRepository:
    """Repositorio para partidos."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, fixture_id: int) -> Optional[Fixture]:
        """Obtiene un partido por ID."""
        return self.db.query(Fixture).filter(Fixture.id == fixture_id).first()
    
    def get_by_date(self, target_date: date) -> List[Fixture]:
        """Obtiene partidos de una fecha."""
        return self.db.query(Fixture).filter(
            func.date(Fixture.date) == target_date
        ).all()
    
    def get_by_league_season(
        self, 
        league_id: int, 
        season: int
    ) -> List[Fixture]:
        """Obtiene partidos de una liga y temporada."""
        return self.db.query(Fixture).filter(
            and_(
                Fixture.league_id == league_id,
                Fixture.season == season
            )
        ).order_by(Fixture.date).all()
    
    def get_team_fixtures(
        self, 
        team_id: int, 
        season: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Fixture]:
        """Obtiene partidos de un equipo."""
        query = self.db.query(Fixture).filter(
            or_(
                Fixture.home_team_id == team_id,
                Fixture.away_team_id == team_id
            )
        )
        
        if season:
            query = query.filter(Fixture.season == season)
        
        query = query.order_by(Fixture.date.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_finished_fixtures(
        self,
        exclude_draws: bool = True
    ) -> List[Fixture]:
        """Obtiene partidos terminados para training."""
        query = self.db.query(Fixture).filter(
            Fixture.status == "FT"
        )
        
        if exclude_draws:
            query = query.filter(Fixture.result.isnot(None))
        
        return query.all()
    
    def get_pending_fixtures(self, target_date: date) -> List[Fixture]:
        """Obtiene partidos pendientes de una fecha."""
        return self.db.query(Fixture).filter(
            and_(
                func.date(Fixture.date) == target_date,
                Fixture.status == "NS"
            )
        ).all()
    
    def upsert(self, fixture_data: Dict[str, Any]) -> Fixture:
        """Inserta o actualiza un partido."""
        fixture = self.get_by_id(fixture_data["id"])
        
        if fixture:
            for key, value in fixture_data.items():
                setattr(fixture, key, value)
        else:
            fixture = Fixture(**fixture_data)
            self.db.add(fixture)
        
        self.db.flush()
        return fixture
    
    def update_result(self, fixture_id: int, home_goals: int, away_goals: int) -> Fixture:
        """Actualiza el resultado de un partido."""
        fixture = self.get_by_id(fixture_id)
        if fixture:
            fixture.home_goals = home_goals
            fixture.away_goals = away_goals
            fixture.status = "FT"
            
            # Calcular resultado para el modelo (excluir empates)
            if home_goals > away_goals:
                fixture.result = 1  # Local gana
            elif away_goals > home_goals:
                fixture.result = 0  # Visitante gana
            else:
                fixture.result = None  # Empate = nulo
            
            self.db.flush()
        return fixture


class StandingRepository:
    """Repositorio para clasificaciones."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_league_season(
        self, 
        league_id: int, 
        season: int
    ) -> List[Standing]:
        """Obtiene clasificación de una liga y temporada."""
        return self.db.query(Standing).filter(
            and_(
                Standing.league_id == league_id,
                Standing.season == season
            )
        ).order_by(Standing.rank).all()
    
    def get_team_standing(
        self,
        team_id: int,
        league_id: int,
        season: int
    ) -> Optional[Standing]:
        """Obtiene posición de un equipo."""
        return self.db.query(Standing).filter(
            and_(
                Standing.team_id == team_id,
                Standing.league_id == league_id,
                Standing.season == season
            )
        ).first()
    
    def upsert(self, standing_data: Dict[str, Any]) -> Standing:
        """Inserta o actualiza clasificación."""
        standing = self.get_team_standing(
            standing_data["team_id"],
            standing_data["league_id"],
            standing_data["season"]
        )
        
        if standing:
            for key, value in standing_data.items():
                setattr(standing, key, value)
        else:
            standing = Standing(**standing_data)
            self.db.add(standing)
        
        self.db.flush()
        return standing


class PredictionRepository:
    """Repositorio para predicciones."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_fixture(self, fixture_id: int) -> Optional[Prediction]:
        """Obtiene predicción de un partido."""
        return self.db.query(Prediction).filter(
            Prediction.fixture_id == fixture_id
        ).first()
    
    def get_top_5_by_date(self, target_date: date) -> List[Prediction]:
        """Obtiene top 5 predicciones de un día."""
        return self.db.query(Prediction).filter(
            and_(
                Prediction.is_top_5 == True,
                func.date(Prediction.created_at) == target_date
            )
        ).order_by(Prediction.rank_of_day).all()
    
    def get_predictions_by_date(self, target_date: date) -> List[Prediction]:
        """Obtiene todas las predicciones de un día."""
        return self.db.query(Prediction).filter(
            func.date(Prediction.created_at) == target_date
        ).order_by(Prediction.confidence.desc()).all()
    
    def get_unverified(self) -> List[Prediction]:
        """Obtiene predicciones sin verificar."""
        return self.db.query(Prediction).filter(
            Prediction.verified_at.is_(None)
        ).all()
    
    def create(self, prediction_data: Dict[str, Any]) -> Prediction:
        """Crea una nueva predicción."""
        prediction = Prediction(**prediction_data)
        self.db.add(prediction)
        self.db.flush()
        return prediction
    
    def verify(
        self, 
        prediction_id: int, 
        actual_result: int
    ) -> Prediction:
        """Verifica una predicción con el resultado real."""
        prediction = self.db.query(Prediction).filter(
            Prediction.id == prediction_id
        ).first()
        
        if prediction:
            prediction.actual_result = actual_result
            prediction.is_correct = (prediction.predicted_winner == actual_result)
            prediction.verified_at = datetime.utcnow()
            self.db.flush()
        
        return prediction
    
    def get_accuracy_stats(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        top_5_only: bool = False
    ) -> Dict[str, Any]:
        """Calcula estadísticas de precisión."""
        query = self.db.query(Prediction).filter(
            Prediction.verified_at.isnot(None)
        )
        
        if start_date:
            query = query.filter(Prediction.created_at >= start_date)
        if end_date:
            query = query.filter(Prediction.created_at <= end_date)
        if top_5_only:
            query = query.filter(Prediction.is_top_5 == True)
        
        predictions = query.all()
        
        total = len(predictions)
        correct = sum(1 for p in predictions if p.is_correct)
        
        return {
            "total": total,
            "correct": correct,
            "accuracy": correct / total if total > 0 else 0,
            "top_5_only": top_5_only
        }
