#!/usr/bin/env python3
"""Script de predicciones múltiples jornadas La Liga 2025/26"""
import pandas as pd
import pickle
import numpy as np
from src.db import get_db_session, Fixture, Team

# 1. Cargar datos
df = pd.read_csv('data/test_2025.csv')
print(f"📊 Total partidos 2025: {len(df)}")

# 2. Cargar modelo
print("🤖 Cargando modelo...")
with open('models/trained/ensemble_model.pkl', 'rb') as f:
    model = pickle.load(f)

feature_names = model['feature_names']
scaler = model['scaler']
models = model['calibrated_models'] if model['use_calibration'] else model['models']
weights = model['weights']

# 3. Obtener equipos y jornadas
with get_db_session() as db:
    teams = {t.id: t.name for t in db.query(Team).all()}
    
    jornadas = ['Regular Season - 15']
    
    for jornada in jornadas:
        fixtures = db.query(Fixture).filter(
            Fixture.league_id == 140,
            Fixture.season == 2025,
            Fixture.round == jornada,
            Fixture.status == 'FT'
        ).all()
        
        # Filtrar sin empates y que estén en test
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
            print(f"\n⚠️ {jornada}: Sin partidos disponibles")
            continue
        
        # Obtener features
        fids = [p['id'] for p in partidos]
        df_j = df[df['fixture_id'].isin(fids)]
        
        if len(df_j) == 0:
            print(f"\n⚠️ {jornada}: Sin features")
            continue
        
        X = df_j[feature_names].fillna(0).values
        X_scaled = scaler.transform(X)
        
        # Predecir
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
        
        # Mostrar
        num = jornada.split(' - ')[1]
        print(f"\n{'='*70}")
        print(f"📊 JORNADA {num} - LA LIGA 2025/26")
        print("="*70)
        
        aciertos = 0
        for i, fid in enumerate(df_j['fixture_id'].values):
            p = next((x for x in partidos if x['id'] == fid), None)
            if not p:
                continue
            
            pred = preds[i]
            real = p['real']
            conf = confs[i]
            
            pred_txt = "Local" if pred == 1 else "Visitante"
            real_txt = "Local" if real == 1 else "Visitante"
            
            ok = pred == real
            if ok:
                aciertos += 1
            sym = "✅" if ok else "❌"
            
            print(f"{sym} {p['home'][:16]:16} vs {p['away'][:16]:16} | {p['hg']}-{p['ag']} | Real: {real_txt:9} | Pred: {pred_txt:9} | Conf: {conf*100:.0f}%")
        
        total = len(df_j)
        print(f"\n📈 RESUMEN J{num}: {aciertos}/{total} = {aciertos/total*100:.1f}%")
