#!/usr/bin/env python3
"""
Simulación de Apuestas Deportivas - Oct/Nov/Dic 2025

Estrategia:
- Días diarios (Lun-Jue): TOP 2 predicciones con confianza ≥80%
- Fines de semana (Vie-Dom): TOP 8 predicciones con confianza ≥80%
- Apuesta: 20€ por partido
- Tipo: Sin empate (Draw No Bet) - empate devuelve dinero
"""

import pandas as pd
import joblib
from datetime import datetime, timedelta
from collections import defaultdict
from src.db import get_db_session
from src.db.models import Fixture, Team, League
from src.data.features.pipeline import FeaturePipeline

# Configuración
APUESTA = 20  # euros por partido
CONFIANZA_MINIMA = 0.80  # 80%
TOP_DIARIO = 2  # Lun-Jue
TOP_FINDE = 8  # Vie-Dom

def calcular_cuota(confianza):
    """Calcula cuota realista basada en la confianza del modelo.
    
    Cuotas más altas = menos probabilidad implícita
    Confianza 80% -> cuota ~1.45 (favorito claro)
    Confianza 95% -> cuota ~1.15 (super favorito)
    """
    # Margen de la casa ~5-8%
    margen = 0.07
    prob_real = confianza
    cuota_pura = 1 / prob_real
    # Cuota con margen reducido para favoritos fuertes
    cuota_final = cuota_pura * (1 - margen + (confianza - 0.8) * 0.1)
    return max(1.10, min(1.50, cuota_final))

def es_fin_de_semana(fecha):
    """Viernes=4, Sábado=5, Domingo=6"""
    return fecha.weekday() >= 4

def main():
    print("=" * 80)
    print("🎰 SIMULACIÓN DE APUESTAS - OCTUBRE, NOVIEMBRE Y DICIEMBRE 2025")
    print("=" * 80)
    print(f"\n📋 ESTRATEGIA:")
    print(f"   • Días diarios (Lun-Jue): TOP {TOP_DIARIO} predicciones")
    print(f"   • Fines de semana (Vie-Dom): TOP {TOP_FINDE} predicciones")
    print(f"   • Confianza mínima: {CONFIANZA_MINIMA*100:.0f}%")
    print(f"   • Apuesta por partido: {APUESTA}€")
    print(f"   • Tipo: Sin empate (empate = devolución)")
    print()
    
    # Cargar modelo
    print("🔄 Cargando modelo...")
    model_data = joblib.load('models/trained/main_model.pkl')
    model = model_data['model']
    feature_cols = model_data['feature_columns']
    
    pipeline = FeaturePipeline()
    
    # Cargar datos de equipos y ligas
    with get_db_session() as db:
        teams = {t.id: t.name for t in db.query(Team).all()}
        leagues = {l.id: l.name for l in db.query(League).all()}
    
    # Estadísticas
    stats = {
        'total_apuestas': 0,
        'aciertos': 0,
        'fallos': 0,
        'empates': 0,
        'invertido': 0.0,
        'ganado': 0.0,
        'por_mes': defaultdict(lambda: {'apuestas': 0, 'aciertos': 0, 'fallos': 0, 'empates': 0, 'invertido': 0.0, 'ganado': 0.0})
    }
    
    # Iterar por cada día desde 1 Oct hasta 15 Dic 2025
    fecha_inicio = datetime(2025, 10, 1)
    fecha_fin = datetime(2025, 12, 15)  # Hasta hoy
    
    fecha_actual = fecha_inicio
    
    while fecha_actual <= fecha_fin:
        fecha_siguiente = fecha_actual + timedelta(days=1)
        
        # Obtener partidos del día
        with get_db_session() as db:
            fixtures = db.query(Fixture).filter(
                Fixture.season == 2025,
                Fixture.date >= fecha_actual,
                Fixture.date < fecha_siguiente,
                Fixture.status == 'FT'  # Solo partidos finalizados
            ).all()
            
            if not fixtures:
                fecha_actual = fecha_siguiente
                continue
            
            fixture_data = []
            for f in fixtures:
                fixture_data.append({
                    'id': f.id,
                    'home': teams.get(f.home_team_id, 'Unknown'),
                    'away': teams.get(f.away_team_id, 'Unknown'),
                    'home_goals': f.home_goals,
                    'away_goals': f.away_goals,
                    'league': leagues.get(f.league_id, 'Unknown'),
                    'date': f.date
                })
        
        # Generar predicciones
        predictions = []
        for fix in fixture_data:
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
                    confianza = max(proba)
                    
                    predictions.append({
                        'id': fix['id'],
                        'home': fix['home'],
                        'away': fix['away'],
                        'home_goals': fix['home_goals'],
                        'away_goals': fix['away_goals'],
                        'pred': pred,  # 1=local, 0=visitante
                        'confidence': confianza,
                        'league': fix['league']
                    })
            except Exception as e:
                continue
        
        # Filtrar por confianza mínima y ordenar
        predictions = [p for p in predictions if p['confidence'] >= CONFIANZA_MINIMA]
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Seleccionar TOP según día
        top_n = TOP_FINDE if es_fin_de_semana(fecha_actual) else TOP_DIARIO
        seleccionados = predictions[:top_n]
        
        if seleccionados:
            dia_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][fecha_actual.weekday()]
            mes = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'][fecha_actual.month - 1]
            mes_key = fecha_actual.strftime('%Y-%m')
            
            print(f"\n📅 {dia_semana} {fecha_actual.day} {mes} 2025 - TOP {top_n}" + 
                  f" ({'FINDE' if es_fin_de_semana(fecha_actual) else 'DIARIO'})")
            print("-" * 70)
            
            for p in seleccionados:
                # Determinar resultado real
                if p['home_goals'] == p['away_goals']:
                    resultado_real = 'EMPATE'
                elif p['home_goals'] > p['away_goals']:
                    resultado_real = 'LOCAL'
                else:
                    resultado_real = 'VISITANTE'
                
                # Predicción
                prediccion = 'LOCAL' if p['pred'] == 1 else 'VISITANTE'
                
                # Calcular cuota y resultado de apuesta
                cuota = calcular_cuota(p['confidence'])
                
                if resultado_real == 'EMPATE':
                    # Empate = devolución
                    ganancia = 0
                    emoji = "🔄"
                    stats['empates'] += 1
                    stats['por_mes'][mes_key]['empates'] += 1
                elif resultado_real == prediccion:
                    # Acierto
                    ganancia = APUESTA * cuota - APUESTA
                    emoji = "✅"
                    stats['aciertos'] += 1
                    stats['por_mes'][mes_key]['aciertos'] += 1
                else:
                    # Fallo
                    ganancia = -APUESTA
                    emoji = "❌"
                    stats['fallos'] += 1
                    stats['por_mes'][mes_key]['fallos'] += 1
                
                stats['total_apuestas'] += 1
                stats['invertido'] += APUESTA
                stats['ganado'] += ganancia
                stats['por_mes'][mes_key]['apuestas'] += 1
                stats['por_mes'][mes_key]['invertido'] += APUESTA
                stats['por_mes'][mes_key]['ganado'] += ganancia
                
                ganador_pred = p['home'] if prediccion == 'LOCAL' else p['away']
                print(f"{emoji} {p['home'][:18]:18} vs {p['away'][:18]:18} | "
                      f"{p['home_goals']}-{p['away_goals']} | "
                      f"Pred: {prediccion:9} ({p['confidence']*100:.0f}%) | "
                      f"Cuota: {cuota:.2f} | "
                      f"{'+'if ganancia >= 0 else ''}{ganancia:.2f}€")
        
        fecha_actual = fecha_siguiente
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN POR MES")
    print("=" * 80)
    
    for mes_key in sorted(stats['por_mes'].keys()):
        m = stats['por_mes'][mes_key]
        mes_nombre = {'2025-10': 'OCTUBRE', '2025-11': 'NOVIEMBRE', '2025-12': 'DICIEMBRE'}[mes_key]
        balance = m['ganado']
        total = m['aciertos'] + m['fallos']
        precision = (m['aciertos'] / total * 100) if total > 0 else 0
        
        print(f"\n📅 {mes_nombre} 2025:")
        print(f"   • Apuestas: {m['apuestas']} (Aciertos: {m['aciertos']}, Fallos: {m['fallos']}, Empates: {m['empates']})")
        print(f"   • Precisión (excluyendo empates): {precision:.1f}%")
        print(f"   • Invertido: {m['invertido']:.2f}€")
        print(f"   • Balance: {'+'if balance >= 0 else ''}{balance:.2f}€")
    
    print("\n" + "=" * 80)
    print("💰 BALANCE FINAL")
    print("=" * 80)
    
    total_decisivos = stats['aciertos'] + stats['fallos']
    precision_final = (stats['aciertos'] / total_decisivos * 100) if total_decisivos > 0 else 0
    roi = (stats['ganado'] / stats['invertido'] * 100) if stats['invertido'] > 0 else 0
    
    print(f"\n🎯 Total apuestas: {stats['total_apuestas']}")
    print(f"   ✅ Aciertos: {stats['aciertos']}")
    print(f"   ❌ Fallos: {stats['fallos']}")
    print(f"   🔄 Empates (devolución): {stats['empates']}")
    print(f"\n📈 Precisión (excluyendo empates): {precision_final:.1f}%")
    print(f"\n💵 Total invertido: {stats['invertido']:.2f}€")
    print(f"💵 Balance neto: {'+'if stats['ganado'] >= 0 else ''}{stats['ganado']:.2f}€")
    print(f"📊 ROI: {'+'if roi >= 0 else ''}{roi:.1f}%")
    
    if stats['ganado'] >= 0:
        print(f"\n🎉 ¡FELICIDADES! Has ganado {stats['ganado']:.2f}€")
    else:
        print(f"\n😔 Has perdido {abs(stats['ganado']):.2f}€")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
