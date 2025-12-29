"""
Simulación de Estrategia de Apuestas - Modelo V3
Oct-Nov-Dic 2025

Estrategia:
- Lun-Jue: Top 2 predicciones con confianza >= 80%
- Vie-Dom: Top 8 predicciones con confianza >= 80%
- Apuesta: 20€ sin empate (Draw No Bet)
- Modelo: optimized_rf_v3.pkl
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
STAKE = 20.0  # Euros por apuesta
MIN_CONFIDENCE = 0.80  # 80% mínimo
MODEL_PATH = "models/trained/optimized_rf_v3.pkl"

# Cuotas realistas simuladas basadas en confianza
def simulate_odds(confidence, is_favorite=True):
    """
    Simula cuotas realistas basadas en la confianza del modelo.
    A mayor confianza del modelo, menor cuota (favorito más claro).
    """
    if is_favorite:
        # Favorito: cuota entre 1.20 (muy favorito) y 1.90 (favorito ligero)
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
        # Underdog: inverso
        return np.random.uniform(2.50, 5.00)


def get_day_type(date):
    """Retorna si es día de semana o fin de semana."""
    weekday = date.weekday()
    if weekday < 4:  # Lun=0, Mar=1, Mie=2, Jue=3
        return "weekday"
    else:  # Vie=4, Sab=5, Dom=6
        return "weekend"


def get_top_n(day_type):
    """Retorna número de apuestas según día."""
    return 2 if day_type == "weekday" else 8


def main():
    print("=" * 80)
    print("SIMULACIÓN DE APUESTAS - MODELO V3")
    print("Período: Octubre - Diciembre 2025")
    print("=" * 80)
    
    # Cargar modelo
    print("\n📦 Cargando modelo v3...")
    model_data = joblib.load(MODEL_PATH)
    model = model_data['model']
    feature_cols = model_data['feature_columns']
    print(f"   Modelo: {model_data.get('model_type', 'Unknown')}")
    print(f"   Features: {len(feature_cols)}")
    print(f"   Accuracy reportada: {model_data.get('accuracy', 'N/A')}")
    
    # Inicializar pipeline
    pipeline = FeaturePipeline()
    
    # Definir período
    start_date = datetime(2025, 10, 1)
    end_date = datetime(2025, 12, 16)  # Hasta hoy
    
    # Obtener fixtures del período
    print(f"\n📅 Obteniendo partidos del {start_date.date()} al {end_date.date()}...")
    
    with get_db_session() as db:
        teams = {t.id: t.name for t in db.query(Team).all()}
        leagues = {l.id: l.name for l in db.query(League).all()}
        
        fixtures = db.query(Fixture).filter(
            Fixture.season == 2025,
            Fixture.date >= start_date,
            Fixture.date < end_date,
            Fixture.status == "FT"  # Solo partidos terminados
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
                'result': f.result  # 1=home, 0=away, None=draw
            })
    
    print(f"   Total partidos terminados: {len(fixture_data)}")
    
    # Agrupar por día
    fixtures_by_day = defaultdict(list)
    for f in fixture_data:
        day_key = f['date'].date()
        fixtures_by_day[day_key].append(f)
    
    # Procesar día por día
    print("\n🎯 Procesando predicciones día por día...")
    
    all_bets = []
    days_with_bets = 0
    
    for day in sorted(fixtures_by_day.keys()):
        day_fixtures = fixtures_by_day[day]
        day_type = get_day_type(datetime.combine(day, datetime.min.time()))
        top_n = get_top_n(day_type)
        
        # Calcular predicciones para todos los partidos del día
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
                        'prob_home': proba[1] if len(proba) > 1 else proba[0],
                        'prob_away': proba[0] if len(proba) > 1 else 1 - proba[0]
                    })
            except Exception as e:
                continue
        
        # Filtrar por confianza >= 80%
        high_conf = [p for p in predictions if p['confidence'] >= MIN_CONFIDENCE]
        
        # Ordenar por confianza y tomar top N
        high_conf.sort(key=lambda x: x['confidence'], reverse=True)
        selected = high_conf[:top_n]
        
        if selected:
            days_with_bets += 1
        
        for bet in selected:
            # Determinar ganador predicho
            predicted_winner = 'home' if bet['pred'] == 1 else 'away'
            predicted_team = bet['home'] if predicted_winner == 'home' else bet['away']
            
            # Determinar resultado real
            home_goals = bet['home_goals'] or 0
            away_goals = bet['away_goals'] or 0
            
            if home_goals > away_goals:
                actual_winner = 'home'
            elif away_goals > home_goals:
                actual_winner = 'away'
            else:
                actual_winner = 'draw'
            
            # Simular cuota
            odds = simulate_odds(bet['confidence'], is_favorite=True)
            
            # Calcular resultado de la apuesta
            if actual_winner == 'draw':
                # Draw No Bet: se devuelve el dinero
                profit = 0
                status = 'VOID'
            elif predicted_winner == actual_winner:
                # Ganamos
                profit = STAKE * (odds - 1)
                status = 'WIN'
            else:
                # Perdemos
                profit = -STAKE
                status = 'LOSS'
            
            all_bets.append({
                'date': bet['date'],
                'day_type': day_type,
                'league': bet['league'][:20],
                'home': bet['home'],
                'away': bet['away'],
                'predicted': predicted_team,
                'confidence': bet['confidence'],
                'odds': odds,
                'score': f"{home_goals}-{away_goals}",
                'actual_winner': actual_winner,
                'status': status,
                'stake': STAKE if status != 'VOID' else 0,
                'profit': profit
            })
    
    # Crear DataFrame de resultados
    df_bets = pd.DataFrame(all_bets)
    
    if len(df_bets) == 0:
        print("\n❌ No se encontraron apuestas con los criterios especificados.")
        return
    
    # Análisis de resultados
    print("\n" + "=" * 80)
    print("📊 RESULTADOS DE LA SIMULACIÓN")
    print("=" * 80)
    
    # Estadísticas generales
    total_bets = len(df_bets)
    wins = len(df_bets[df_bets['status'] == 'WIN'])
    losses = len(df_bets[df_bets['status'] == 'LOSS'])
    voids = len(df_bets[df_bets['status'] == 'VOID'])
    
    total_staked = df_bets[df_bets['status'] != 'VOID']['stake'].sum()
    total_profit = df_bets['profit'].sum()
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
    
    print(f"\n📈 RESUMEN GENERAL")
    print(f"   Período: {start_date.date()} - {end_date.date()}")
    print(f"   Días con apuestas: {days_with_bets}")
    print(f"   Total apuestas: {total_bets}")
    print(f"   ✅ Ganadas: {wins}")
    print(f"   ❌ Perdidas: {losses}")
    print(f"   🔄 Anuladas (empate): {voids}")
    print(f"   Precisión (sin anuladas): {wins/(wins+losses)*100:.1f}%" if (wins+losses) > 0 else "N/A")
    
    print(f"\n💰 BALANCE FINANCIERO")
    print(f"   Total apostado: €{total_staked:.2f}")
    print(f"   Ganancias/Pérdidas: €{total_profit:+.2f}")
    print(f"   ROI: {roi:+.1f}%")
    print(f"   Balance final: €{total_profit:+.2f}")
    
    # Desglose por tipo de día
    print(f"\n📅 DESGLOSE POR TIPO DE DÍA")
    for day_type in ['weekday', 'weekend']:
        day_bets = df_bets[df_bets['day_type'] == day_type]
        if len(day_bets) > 0:
            d_wins = len(day_bets[day_bets['status'] == 'WIN'])
            d_losses = len(day_bets[day_bets['status'] == 'LOSS'])
            d_profit = day_bets['profit'].sum()
            d_total = d_wins + d_losses
            d_acc = d_wins / d_total * 100 if d_total > 0 else 0
            label = "Lun-Jue (Top 2)" if day_type == 'weekday' else "Vie-Dom (Top 8)"
            print(f"   {label}: {len(day_bets)} apuestas, {d_wins}W-{d_losses}L ({d_acc:.1f}%), €{d_profit:+.2f}")
    
    # Desglose por mes
    print(f"\n📆 DESGLOSE POR MES")
    df_bets['month'] = pd.to_datetime(df_bets['date']).dt.month
    for month in sorted(df_bets['month'].unique()):
        month_bets = df_bets[df_bets['month'] == month]
        m_wins = len(month_bets[month_bets['status'] == 'WIN'])
        m_losses = len(month_bets[month_bets['status'] == 'LOSS'])
        m_profit = month_bets['profit'].sum()
        m_total = m_wins + m_losses
        m_acc = m_wins / m_total * 100 if m_total > 0 else 0
        month_names = {10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        print(f"   {month_names.get(month, month)}: {len(month_bets)} apuestas, {m_wins}W-{m_losses}L ({m_acc:.1f}%), €{m_profit:+.2f}")
    
    # Desglose por rango de confianza
    print(f"\n🎯 DESGLOSE POR CONFIANZA")
    for conf_min, conf_max, label in [(0.80, 0.85, '80-85%'), (0.85, 0.90, '85-90%'), (0.90, 0.95, '90-95%'), (0.95, 1.01, '95%+')]:
        conf_bets = df_bets[(df_bets['confidence'] >= conf_min) & (df_bets['confidence'] < conf_max)]
        if len(conf_bets) > 0:
            c_wins = len(conf_bets[conf_bets['status'] == 'WIN'])
            c_losses = len(conf_bets[conf_bets['status'] == 'LOSS'])
            c_profit = conf_bets['profit'].sum()
            c_total = c_wins + c_losses
            c_acc = c_wins / c_total * 100 if c_total > 0 else 0
            print(f"   {label}: {len(conf_bets)} apuestas, {c_wins}W-{c_losses}L ({c_acc:.1f}%), €{c_profit:+.2f}")
    
    # Mostrar últimas 20 apuestas
    print(f"\n📋 ÚLTIMAS 20 APUESTAS")
    print("-" * 100)
    print(f"{'Fecha':<12} {'Liga':<20} {'Partido':<35} {'Pred':<15} {'Conf':<6} {'Odds':<5} {'Score':<6} {'Status':<6} {'P/L':<8}")
    print("-" * 100)
    
    for _, bet in df_bets.tail(20).iterrows():
        date_str = bet['date'].strftime('%d/%m')
        partido = f"{bet['home'][:15]} vs {bet['away'][:15]}"
        status_emoji = '✅' if bet['status'] == 'WIN' else ('❌' if bet['status'] == 'LOSS' else '🔄')
        print(f"{date_str:<12} {bet['league']:<20} {partido:<35} {bet['predicted'][:15]:<15} {bet['confidence']:.1%} {bet['odds']:.2f}  {bet['score']:<6} {status_emoji:<6} €{bet['profit']:+.2f}")
    
    print("\n" + "=" * 80)
    if total_profit > 0:
        print(f"🎉 ¡GANANCIA TOTAL: €{total_profit:+.2f}!")
    else:
        print(f"📉 PÉRDIDA TOTAL: €{total_profit:.2f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
