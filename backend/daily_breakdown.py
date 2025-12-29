"""
Desglose Diario de Apuestas - Modelo V3
Oct-Nov-Dic 2025
"""

import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
from collections import defaultdict

from src.db.database import get_db_session
from src.db.models import Fixture, Team, League
from src.data.features.pipeline import FeaturePipeline

# Configuración
STAKE = 20.0
MIN_CONFIDENCE = 0.80
MODEL_PATH = "models/trained/optimized_rf_v3.pkl"

def simulate_odds(confidence, is_favorite=True):
    if is_favorite:
        if confidence >= 0.95:
            return np.random.uniform(1.15, 1.30)
        elif confidence >= 0.90:
            return np.random.uniform(1.25, 1.45)
        elif confidence >= 0.85:
            return np.random.uniform(1.40, 1.60)
        elif confidence >= 0.80:
            return np.random.uniform(1.55, 1.80)
        else:
            return np.random.uniform(1.70, 2.00)
    else:
        return np.random.uniform(2.50, 5.00)

def get_day_type(date):
    weekday = date.weekday()
    return "weekday" if weekday < 4 else "weekend"

def get_top_n(day_type):
    return 2 if day_type == "weekday" else 8

def main():
    print("=" * 100)
    print("DESGLOSE DIARIO DE APUESTAS - MODELO V3")
    print("Período: Octubre - Diciembre 2025")
    print("=" * 100)
    
    # Cargar modelo
    np.random.seed(42)  # Para reproducibilidad de cuotas
    model_data = joblib.load(MODEL_PATH)
    model = model_data['model']
    feature_cols = model_data['feature_columns']
    
    pipeline = FeaturePipeline()
    
    start_date = datetime(2025, 10, 1)
    end_date = datetime(2025, 12, 16)
    
    with get_db_session() as db:
        teams = {t.id: t.name for t in db.query(Team).all()}
        leagues = {l.id: l.name for l in db.query(League).all()}
        
        fixtures = db.query(Fixture).filter(
            Fixture.season == 2025,
            Fixture.date >= start_date,
            Fixture.date < end_date,
            Fixture.status == "FT"
        ).order_by(Fixture.date).all()
        
        fixture_data = []
        for f in fixtures:
            fixture_data.append({
                'id': f.id,
                'home_team_id': f.home_team_id,
                'away_team_id': f.away_team_id,
                'home': teams.get(f.home_team_id, 'Unknown'),
                'away': teams.get(f.away_team_id, 'Unknown'),
                'date': f.date,
                'league': leagues.get(f.league_id, 'Unknown'),
                'home_goals': f.home_goals,
                'away_goals': f.away_goals,
                'result': f.result
            })
    
    fixtures_by_day = defaultdict(list)
    for f in fixture_data:
        day_key = f['date'].date()
        fixtures_by_day[day_key].append(f)
    
    all_bets = []
    
    for day in sorted(fixtures_by_day.keys()):
        day_fixtures = fixtures_by_day[day]
        day_type = get_day_type(datetime.combine(day, datetime.min.time()))
        top_n = get_top_n(day_type)
        
        predictions = []
        
        for fix in day_fixtures:
            try:
                with get_db_session() as db:
                    fixture = db.query(Fixture).filter(Fixture.id == fix['id']).first()
                    if not fixture:
                        continue
                    
                    match_features = pipeline.calculate_fixture_features(fixture)
                    if not match_features or not match_features.features:
                        continue
                    
                    X = pd.DataFrame([match_features.features])
                    for col in feature_cols:
                        if col not in X.columns:
                            X[col] = 0
                    X = X[feature_cols].fillna(0)
                    
                    pred = model.predict(X)[0]
                    proba = model.predict_proba(X)[0]
                    confidence = max(proba)
                    
                    predictions.append({
                        **fix,
                        'pred': pred,
                        'confidence': confidence,
                    })
            except:
                continue
        
        high_conf = [p for p in predictions if p['confidence'] >= MIN_CONFIDENCE]
        high_conf.sort(key=lambda x: x['confidence'], reverse=True)
        selected = high_conf[:top_n]
        
        for bet in selected:
            predicted_winner = 'home' if bet['pred'] == 1 else 'away'
            predicted_team = bet['home'] if predicted_winner == 'home' else bet['away']
            
            home_goals = bet['home_goals'] or 0
            away_goals = bet['away_goals'] or 0
            
            if home_goals > away_goals:
                actual_winner = 'home'
            elif away_goals > home_goals:
                actual_winner = 'away'
            else:
                actual_winner = 'draw'
            
            odds = simulate_odds(bet['confidence'], is_favorite=True)
            
            if actual_winner == 'draw':
                profit = 0
                status = 'VOID'
            elif predicted_winner == actual_winner:
                profit = STAKE * (odds - 1)
                status = 'WIN'
            else:
                profit = -STAKE
                status = 'LOSS'
            
            all_bets.append({
                'date': bet['date'].date(),
                'day_name': bet['date'].strftime('%a'),
                'day_type': day_type,
                'league': bet['league'][:25],
                'home': bet['home'][:15],
                'away': bet['away'][:15],
                'predicted': predicted_team[:15],
                'confidence': bet['confidence'],
                'odds': odds,
                'score': f"{home_goals}-{away_goals}",
                'status': status,
                'profit': profit
            })
    
    df = pd.DataFrame(all_bets)
    
    # Agrupar por día
    daily_summary = df.groupby('date').agg({
        'profit': 'sum',
        'status': lambda x: f"{(x=='WIN').sum()}W-{(x=='LOSS').sum()}L-{(x=='VOID').sum()}V"
    }).reset_index()
    
    # Calcular balance acumulado
    daily_summary['balance'] = daily_summary['profit'].cumsum()
    
    print("\n" + "=" * 100)
    print("📅 DESGLOSE DIARIO")
    print("=" * 100)
    
    current_month = None
    month_profit = 0
    
    for _, row in daily_summary.iterrows():
        date = row['date']
        month = date.month
        
        if month != current_month:
            if current_month is not None:
                print(f"   {'─'*90}")
                print(f"   📊 TOTAL MES: €{month_profit:+.2f}")
                print()
            month_names = {10: '🎃 OCTUBRE', 11: '🍂 NOVIEMBRE', 12: '🎄 DICIEMBRE'}
            print(f"\n{month_names.get(month, month)}")
            print("-" * 100)
            current_month = month
            month_profit = 0
        
        month_profit += row['profit']
        day_name = date.strftime('%a')
        
        # Emoji según resultado del día
        if row['profit'] > 0:
            emoji = '✅'
        elif row['profit'] < 0:
            emoji = '❌'
        else:
            emoji = '🔄'
        
        print(f"   {emoji} {date.strftime('%d/%m')} ({day_name}): {row['status']:<12} | Día: €{row['profit']:+8.2f} | Balance: €{row['balance']:+9.2f}")
    
    # Último mes
    print(f"   {'─'*90}")
    print(f"   📊 TOTAL MES: €{month_profit:+.2f}")
    
    # Mostrar días con pérdidas
    print("\n" + "=" * 100)
    print("❌ DÍAS CON PÉRDIDAS (detalle)")
    print("=" * 100)
    
    loss_days = df[df['status'] == 'LOSS']['date'].unique()
    
    for loss_day in loss_days:
        day_bets = df[df['date'] == loss_day]
        print(f"\n📅 {loss_day.strftime('%d/%m/%Y')} ({loss_day.strftime('%A')})")
        print("-" * 80)
        
        for _, bet in day_bets.iterrows():
            status_emoji = '✅' if bet['status'] == 'WIN' else ('❌' if bet['status'] == 'LOSS' else '🔄')
            print(f"   {status_emoji} [{bet['league'][:20]}] {bet['home']} vs {bet['away']}")
            print(f"      → Predicción: {bet['predicted']} ({bet['confidence']:.1%}) @ {bet['odds']:.2f}")
            print(f"      → Resultado: {bet['score']} | P/L: €{bet['profit']:+.2f}")
    
    # Resumen final
    print("\n" + "=" * 100)
    print("📊 RESUMEN FINAL")
    print("=" * 100)
    
    total_days = len(daily_summary)
    win_days = len(daily_summary[daily_summary['profit'] > 0])
    loss_days_count = len(daily_summary[daily_summary['profit'] < 0])
    even_days = len(daily_summary[daily_summary['profit'] == 0])
    
    print(f"\n   🗓️ Total días con apuestas: {total_days}")
    print(f"   ✅ Días en verde: {win_days} ({win_days/total_days*100:.1f}%)")
    print(f"   ❌ Días en rojo: {loss_days_count} ({loss_days_count/total_days*100:.1f}%)")
    print(f"   🔄 Días neutros: {even_days} ({even_days/total_days*100:.1f}%)")
    print(f"\n   💰 Balance final: €{daily_summary['balance'].iloc[-1]:+.2f}")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    main()
