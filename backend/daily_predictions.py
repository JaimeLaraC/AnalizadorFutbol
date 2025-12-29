#!/usr/bin/env python3
"""
🎯 PREDICCIONES DIARIAS - Kelly Conservador + Stop-Loss

Ejecutar cada mañana para obtener las apuestas del día:
    python daily_predictions.py

Opciones:
    python daily_predictions.py --bankroll 1500    # Especificar bankroll
    python daily_predictions.py --tomorrow         # Ver predicciones de mañana
"""

import argparse
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')
import logging
logging.disable(logging.CRITICAL)

from src.db.database import get_db_session
from src.db.models import Fixture, Team, League
from src.data.features.pipeline import FeaturePipeline


# ============================================================
# CONFIGURACIÓN DE LA ESTRATEGIA
# ============================================================
MIN_CONFIDENCE = 0.75      # Umbral mínimo de confianza
KELLY_FRACTION = 0.10      # Kelly fraccionario (10%)
MIN_STAKE = 10             # Stake mínimo €10
MAX_STAKE_PCT = 0.05       # Stake máximo 5% del bankroll
STOP_LOSS_PCT = 0.20       # Stop-loss diario 20%


def get_odds_dnb(conf: float) -> float:
    """Estima la cuota DNB según la confianza del modelo."""
    if conf >= 0.90:
        return 1.25
    elif conf >= 0.85:
        return 1.40
    elif conf >= 0.80:
        return 1.55
    elif conf >= 0.75:
        return 1.70
    else:
        return 1.85


def calculate_kelly_stake(bankroll: float, conf: float, odds: float) -> float:
    """Calcula el stake usando Kelly fraccionario."""
    b = odds - 1
    prob = conf
    kelly = (b * prob - (1 - prob)) / b
    
    if kelly <= 0:
        return 0
    
    stake_raw = bankroll * kelly * KELLY_FRACTION
    stake_min = MIN_STAKE
    stake_max = bankroll * MAX_STAKE_PCT
    
    return max(stake_min, min(stake_raw, stake_max))


def main():
    parser = argparse.ArgumentParser(description='Predicciones diarias con Kelly')
    parser.add_argument('--bankroll', type=float, default=1000, 
                        help='Tu bankroll actual (default: 1000)')
    parser.add_argument('--tomorrow', action='store_true',
                        help='Ver predicciones de mañana')
    parser.add_argument('--sync', action='store_true',
                        help='Sincronizar datos antes de predecir')
    args = parser.parse_args()
    
    bankroll = args.bankroll
    
    # Determinar fecha
    if args.tomorrow:
        target_date = datetime.now().date() + timedelta(days=1)
    else:
        target_date = datetime.now().date()
    
    day_name = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][target_date.weekday()]
    
    print()
    print('=' * 80)
    print(f'🎯 PREDICCIONES {day_name.upper()} {target_date.strftime("%d/%m/%Y")}')
    print('=' * 80)
    print(f'💰 Bankroll: €{bankroll:.2f}')
    print(f'📊 Estrategia: Kelly {KELLY_FRACTION*100:.0f}% | Conf ≥{MIN_CONFIDENCE*100:.0f}% | DNB')
    print()
    
    # Cargar modelo
    MODEL_PATH = 'models/trained/optimized_rf_v3.pkl'
    try:
        model_data = joblib.load(MODEL_PATH)
        model = model_data['model']
        feature_cols = model_data['feature_columns']
    except FileNotFoundError:
        print(f'❌ Error: No se encontró el modelo en {MODEL_PATH}')
        return
    
    pipeline = FeaturePipeline()
    
    # Obtener partidos del día
    start = datetime.combine(target_date, datetime.min.time())
    end = start + timedelta(days=1)
    
    with get_db_session() as db:
        teams = {t.id: t.name for t in db.query(Team).all()}
        leagues = {l.id: l.name for l in db.query(League).all()}
        
        fixtures = db.query(Fixture).filter(
            Fixture.date >= start,
            Fixture.date < end
        ).order_by(Fixture.date).all()
        
        fixture_data = [{
            'id': f.id,
            'home': teams.get(f.home_team_id, '?'),
            'away': teams.get(f.away_team_id, '?'),
            'league': leagues.get(f.league_id, '?'),
            'date': f.date,
            'status': f.status
        } for f in fixtures]
    
    if not fixture_data:
        print(f'⚠️  No hay partidos para {target_date}')
        print('   Puede que necesites sincronizar los datos:')
        print('   python daily_predictions.py --sync')
        return
    
    print(f'📋 Partidos encontrados: {len(fixture_data)}')
    print()
    
    # Generar predicciones
    predictions = []
    
    for fix in fixture_data:
        try:
            with get_db_session() as db:
                f = db.query(Fixture).filter(Fixture.id == fix['id']).first()
                if not f:
                    continue
                
                mf = pipeline.calculate_fixture_features(f)
                if not mf or not mf.features:
                    continue
                
                X = pd.DataFrame([mf.features])
                for col in feature_cols:
                    if col not in X.columns:
                        X[col] = 0
                X = X[feature_cols].fillna(0)
                
                pred = model.predict(X)[0]
                conf = max(model.predict_proba(X)[0])
                
                if conf >= MIN_CONFIDENCE:
                    odds = get_odds_dnb(conf)
                    stake = calculate_kelly_stake(bankroll, conf, odds)
                    winner = fix['home'] if pred == 1 else fix['away']
                    bet_type = 'LOCAL' if pred == 1 else 'VISIT'
                    
                    predictions.append({
                        'hora': fix['date'].strftime('%H:%M'),
                        'liga': fix['league'][:20],
                        'home': fix['home'],
                        'away': fix['away'],
                        'pred': bet_type,
                        'winner': winner,
                        'conf': conf,
                        'odds': odds,
                        'stake': stake
                    })
        except Exception as e:
            continue
    
    if not predictions:
        print('❌ No hay apuestas con confianza ≥75% para hoy')
        return
    
    # Ordenar por confianza
    predictions.sort(key=lambda x: x['conf'], reverse=True)
    
    # Mostrar predicciones
    print('🎯 APUESTAS RECOMENDADAS')
    print('-' * 80)
    print(f'{"#":>2} {"Hora":>5} {"Liga":<20} {"Partido":<35} {"Conf":>5} {"Stake":>7}')
    print('-' * 80)
    
    total_stake = 0
    max_potential = 0
    
    for i, p in enumerate(predictions, 1):
        partido = f"{p['home'][:15]} vs {p['away'][:15]}"
        icon = '🔥' if p['conf'] >= 0.85 else '  '
        print(f'{i:2}. {p["hora"]:>5} {p["liga"]:<20} {partido:<35} {p["conf"]*100:>4.0f}% €{p["stake"]:>6.0f} {icon}')
        total_stake += p['stake']
        max_potential += p['stake'] * (p['odds'] - 1)
    
    print('-' * 80)
    print()
    
    # Resumen
    print('📊 RESUMEN')
    print(f'   Total apuestas:     {len(predictions)}')
    print(f'   Total a apostar:    €{total_stake:.2f}')
    print(f'   Ganancia potencial: €{max_potential:.2f}')
    print(f'   Stop-loss del día:  €{bankroll * STOP_LOSS_PCT:.2f} (-20%)')
    print()
    
    # Instrucciones
    print('📋 INSTRUCCIONES')
    print('-' * 80)
    for i, p in enumerate(predictions, 1):
        print(f'{i}. {p["home"]} vs {p["away"]}')
        print(f'   → Apostar €{p["stake"]:.0f} a {p["winner"]} (DNB)')
        print(f'   → Cuota objetivo: ≥{p["odds"]:.2f}')
        print()
    
    print('=' * 80)
    print('⚠️  RECUERDA:')
    print('   • Siempre apuesta DNB (Draw No Bet)')
    print('   • Si pierdes €' + f'{bankroll * STOP_LOSS_PCT:.0f} hoy, PARA de apostar')
    print('   • Anota tus resultados para actualizar el bankroll mañana')
    print('=' * 80)


if __name__ == '__main__':
    main()
