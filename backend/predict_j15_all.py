#!/usr/bin/env python3
"""Predicciones Jornada 15 - Todas las ligas"""
import pandas as pd
import pickle
import numpy as np
from src.db import get_db_session, Fixture, Team

LEAGUES = [
    (140, 'laliga', 'La Liga', '🇪🇸'),
    (39, 'epl', 'Premier League', '🏴󠁧󠁢󠁥󠁮󠁧󠁿'),
    (135, 'seriea', 'Serie A', '🇮🇹'),
    (78, 'bundesliga', 'Bundesliga', '🇩🇪'),
    (61, 'ligue1', 'Ligue 1', '🇫🇷'),
]

# Cargar modelo
with open('models/trained/ensemble_model.pkl', 'rb') as f:
    model = pickle.load(f)

feature_names = model['feature_names']
scaler = model['scaler']
models = model['calibrated_models'] if model['use_calibration'] else model['models']
weights = model['weights']

def predict(X):
    X_scaled = scaler.transform(X)
    all_probas = []
    all_w = []
    for name, m in models.items():
        if name == 'logreg':
            probas = m.predict_proba(X_scaled)
        else:
            probas = m.predict_proba(X)
        all_probas.append(probas)
        all_w.append(weights[name])
    all_probas = np.array(all_probas)
    all_w = np.array(all_w) / sum(all_w)
    weighted = np.average(all_probas, axis=0, weights=all_w)
    preds = (weighted[:, 1] >= 0.5).astype(int)
    confs = np.maximum(weighted[:, 0], weighted[:, 1])
    return preds, confs

total_aciertos = 0
total_partidos = 0

with get_db_session() as db:
    teams = {t.id: t.name for t in db.query(Team).all()}
    
    for lid, key, name, flag in LEAGUES:
        # Cargar features
        try:
            if key == 'laliga':
                df = pd.read_csv('data/test_2025.csv')  # Tiene ambos nombres
            else:
                df = pd.read_csv(f'data/test_{key}_2025.csv')
        except FileNotFoundError:
            print(f"\n⚠️ {flag} {name}: sin datos")
            continue
        
        # Obtener jornada 15
        fixtures = db.query(Fixture).filter(
            Fixture.league_id == lid,
            Fixture.season == 2025,
            Fixture.round == 'Regular Season - 15',
            Fixture.status == 'FT'
        ).all()
        
        partidos = []
        for f in fixtures:
            if f.home_goals != f.away_goals and f.id in df['fixture_id'].values:
                partidos.append({
                    'id': f.id,
                    'home': teams.get(f.home_team_id, '?'),
                    'away': teams.get(f.away_team_id, '?'),
                    'hg': f.home_goals,
                    'ag': f.away_goals,
                    'real': 1 if f.home_goals > f.away_goals else 0
                })
        
        if not partidos:
            print(f"\n⚠️ {flag} {name}: sin partidos J15")
            continue
        
        fids = [p['id'] for p in partidos]
        df_j = df[df['fixture_id'].isin(fids)]
        
        if len(df_j) == 0:
            continue
        
        X = df_j[feature_names].fillna(0).values
        preds, confs = predict(X)
        
        print(f"\n{'='*75}")
        print(f"{flag} JORNADA 15 - {name.upper()}")
        print('='*75)
        
        aciertos = 0
        for i, fid in enumerate(df_j['fixture_id'].values):
            p = next((x for x in partidos if x['id'] == fid), None)
            if not p:
                continue
            
            pred = preds[i]
            real = p['real']
            conf = confs[i]
            
            pred_txt = 'Local' if pred == 1 else 'Visitante'
            real_txt = 'Local' if real == 1 else 'Visitante'
            
            ok = pred == real
            if ok:
                aciertos += 1
            sym = '✅' if ok else '❌'
            
            print(f"{sym} {p['home'][:16]:16} vs {p['away'][:16]:16} | {p['hg']}-{p['ag']} | Real: {real_txt:9} | Pred: {pred_txt:9} | Conf: {conf*100:.0f}%")
        
        acc = aciertos/len(df_j)*100 if len(df_j) > 0 else 0
        print(f"\n📈 RESUMEN: {aciertos}/{len(df_j)} = {acc:.1f}%")
        
        total_aciertos += aciertos
        total_partidos += len(df_j)

print(f"\n{'='*75}")
print(f"🌍 TOTAL JORNADA 15 (5 LIGAS): {total_aciertos}/{total_partidos} = {total_aciertos/total_partidos*100:.1f}%")
print('='*75)
