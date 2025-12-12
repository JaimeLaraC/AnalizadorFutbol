"""
Modelos de base de datos para el sistema de predicción de fútbol.

Almacena ligas, equipos, partidos, estadísticas y predicciones.
"""

from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    ForeignKey, Text, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from .database import Base


class League(Base):
    """Modelo para ligas/competiciones."""
    
    __tablename__ = "leagues"
    
    id = Column(Integer, primary_key=True)  # ID de API-Football
    name = Column(String(255), nullable=False)
    country = Column(String(100))
    country_code = Column(String(10))
    logo = Column(String(500))
    type = Column(String(50))  # League, Cup
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    teams = relationship("Team", back_populates="league")
    fixtures = relationship("Fixture", back_populates="league")
    standings = relationship("Standing", back_populates="league")
    
    def __repr__(self):
        return f"<League {self.name} ({self.country})>"


class Team(Base):
    """Modelo para equipos."""
    
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)  # ID de API-Football
    name = Column(String(255), nullable=False)
    code = Column(String(10))  # Código de 3 letras
    country = Column(String(100))
    logo = Column(String(500))
    founded = Column(Integer)
    venue_name = Column(String(255))
    venue_capacity = Column(Integer)
    
    # Liga principal (puede jugar en varias)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    league = relationship("League", back_populates="teams")
    home_fixtures = relationship("Fixture", foreign_keys="Fixture.home_team_id", back_populates="home_team")
    away_fixtures = relationship("Fixture", foreign_keys="Fixture.away_team_id", back_populates="away_team")
    standings = relationship("Standing", back_populates="team")
    statistics = relationship("TeamStatistics", back_populates="team")
    
    def __repr__(self):
        return f"<Team {self.name}>"


class Fixture(Base):
    """Modelo para partidos/fixtures."""
    
    __tablename__ = "fixtures"
    
    id = Column(Integer, primary_key=True)  # ID de API-Football
    
    # Liga y temporada
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    season = Column(Integer, nullable=False)
    round = Column(String(100))
    
    # Equipos
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Fecha y hora
    date = Column(DateTime, nullable=False)
    timestamp = Column(Integer)
    
    # Estado
    status = Column(String(50))  # NS, FT, PST, etc.
    
    # Resultados
    home_goals = Column(Integer)
    away_goals = Column(Integer)
    home_goals_halftime = Column(Integer)
    away_goals_halftime = Column(Integer)
    
    # Resultado para el modelo (1=home, 0=away, null=empate o no jugado)
    result = Column(Integer)  # 1=local gana, 0=visitante gana, null=empate/pending
    
    # Venue
    venue_name = Column(String(255))
    venue_city = Column(String(100))
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    league = relationship("League", back_populates="fixtures")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_fixtures")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_fixtures")
    statistics = relationship("FixtureStatistics", back_populates="fixture")
    predictions = relationship("Prediction", back_populates="fixture")
    
    # Índices
    __table_args__ = (
        Index("ix_fixtures_date", "date"),
        Index("ix_fixtures_league_season", "league_id", "season"),
    )
    
    def __repr__(self):
        return f"<Fixture {self.home_team_id} vs {self.away_team_id} ({self.date})>"


class Standing(Base):
    """Modelo para clasificaciones de liga."""
    
    __tablename__ = "standings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Liga y temporada
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    season = Column(Integer, nullable=False)
    
    # Equipo
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Posición
    rank = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)
    goals_diff = Column(Integer)
    group_name = Column(String(100))
    form = Column(String(20))  # "WWDLW"
    status = Column(String(20))  # same, up, down
    description = Column(String(255))  # Champions League, Relegation
    
    # Estadísticas totales
    played = Column(Integer, default=0)
    win = Column(Integer, default=0)
    draw = Column(Integer, default=0)
    lose = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    
    # Estadísticas como local
    home_played = Column(Integer, default=0)
    home_win = Column(Integer, default=0)
    home_draw = Column(Integer, default=0)
    home_lose = Column(Integer, default=0)
    home_goals_for = Column(Integer, default=0)
    home_goals_against = Column(Integer, default=0)
    
    # Estadísticas como visitante
    away_played = Column(Integer, default=0)
    away_win = Column(Integer, default=0)
    away_draw = Column(Integer, default=0)
    away_lose = Column(Integer, default=0)
    away_goals_for = Column(Integer, default=0)
    away_goals_against = Column(Integer, default=0)
    
    # Metadatos
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    league = relationship("League", back_populates="standings")
    team = relationship("Team", back_populates="standings")
    
    # Restricción única
    __table_args__ = (
        UniqueConstraint("league_id", "season", "team_id", name="uq_standing_league_season_team"),
    )
    
    def __repr__(self):
        return f"<Standing {self.rank}. {self.team_id} ({self.points}pts)>"


class FixtureStatistics(Base):
    """Estadísticas de un partido específico."""
    
    __tablename__ = "fixture_statistics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Estadísticas del partido
    shots_total = Column(Integer)
    shots_on_goal = Column(Integer)
    shots_off_goal = Column(Integer)
    shots_blocked = Column(Integer)
    shots_inside_box = Column(Integer)
    shots_outside_box = Column(Integer)
    
    possession = Column(Float)  # Porcentaje
    
    passes_total = Column(Integer)
    passes_accurate = Column(Integer)
    passes_percentage = Column(Float)
    
    fouls = Column(Integer)
    corners = Column(Integer)
    offsides = Column(Integer)
    
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    
    goalkeeper_saves = Column(Integer)
    
    expected_goals = Column(Float)  # xG
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    fixture = relationship("Fixture", back_populates="statistics")
    
    # Restricción única
    __table_args__ = (
        UniqueConstraint("fixture_id", "team_id", name="uq_fixture_stats_fixture_team"),
    )


class TeamStatistics(Base):
    """Estadísticas agregadas de temporada de un equipo."""
    
    __tablename__ = "team_statistics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    season = Column(Integer, nullable=False)
    
    # Estadísticas de forma
    form = Column(String(20))
    
    # Goles
    goals_for_total = Column(Integer)
    goals_for_home = Column(Integer)
    goals_for_away = Column(Integer)
    goals_against_total = Column(Integer)
    goals_against_home = Column(Integer)
    goals_against_away = Column(Integer)
    
    # Promedios por partido
    goals_for_avg = Column(Float)
    goals_against_avg = Column(Float)
    
    # Clean sheets y failed to score
    clean_sheet_total = Column(Integer)
    clean_sheet_home = Column(Integer)
    clean_sheet_away = Column(Integer)
    failed_to_score_total = Column(Integer)
    
    # Penaltis
    penalty_scored = Column(Integer)
    penalty_missed = Column(Integer)
    
    # Formación más usada
    most_used_formation = Column(String(20))
    
    # Datos adicionales en JSON
    extra_data = Column(JSON)
    
    # Metadatos
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    team = relationship("Team", back_populates="statistics")
    
    # Restricción única
    __table_args__ = (
        UniqueConstraint("team_id", "league_id", "season", name="uq_team_stats"),
    )


class Prediction(Base):
    """Predicciones generadas por el modelo."""
    
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Partido
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)
    
    # Predicción del modelo
    predicted_winner = Column(Integer)  # 1=home, 2=away
    probability_home = Column(Float, nullable=False)
    probability_away = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)  # max(prob_home, prob_away)
    
    # Predicción de API-Football (benchmark)
    api_predicted_winner = Column(Integer)
    api_probability_home = Column(Float)
    api_probability_away = Column(Float)
    api_advice = Column(String(255))
    
    # Cuotas del mercado
    odds_home = Column(Float)
    odds_draw = Column(Float)
    odds_away = Column(Float)
    
    # Resultado real (después del partido)
    actual_result = Column(Integer)  # 1=home, 2=away, null=empate/pending
    is_correct = Column(Boolean)
    
    # Si fue incluida en Top 5
    is_top_5 = Column(Boolean, default=False)
    rank_of_day = Column(Integer)  # 1-5 si está en top 5
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)
    
    # Modelo usado
    model_version = Column(String(50))
    features_snapshot = Column(JSON)  # Features usadas para la predicción
    
    # Relaciones
    fixture = relationship("Fixture", back_populates="predictions")
    
    # Índices
    __table_args__ = (
        Index("ix_predictions_created", "created_at"),
        Index("ix_predictions_top5", "is_top_5", "created_at"),
    )
    
    def __repr__(self):
        return f"<Prediction fixture={self.fixture_id} winner={self.predicted_winner} conf={self.confidence:.2f}>"


class HeadToHead(Base):
    """Registro de enfrentamientos directos."""
    
    __tablename__ = "head_to_head"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    team1_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team2_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Estadísticas agregadas
    total_matches = Column(Integer, default=0)
    team1_wins = Column(Integer, default=0)
    team2_wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    team1_goals = Column(Integer, default=0)
    team2_goals = Column(Integer, default=0)
    
    # Última actualización
    last_fixture_id = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Restricción única (ordenar team_ids para evitar duplicados)
    __table_args__ = (
        UniqueConstraint("team1_id", "team2_id", name="uq_h2h_teams"),
    )
