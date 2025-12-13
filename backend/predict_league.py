#!/usr/bin/env python3
"""
predict_league.py - Predictor de Liga Completo

Este script:
1. Descarga datos de la liga si no existen
2. Genera features FRESCAS (no usa caché)
3. Verifica la calidad de las features
4. Ejecuta predicciones

Uso:
    python predict_league.py --league laliga --round 15
    python predict_league.py --league premier --round 10-15
    python predict_league.py --league ligue1 --round 15 --force-refresh

Autor: AnalizadorFutbol
"""

import argparse
import os
import sys
import pandas as pd
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime

# Silenciar logs de SQLAlchemy
os.environ['LOGURU_LEVEL'] = 'WARNING'

LEAGUES = {
    'laliga': {'id': 140, 'name': 'La Liga', 'flag': '🇪🇸'},
    'premier': {'id': 39, 'name': 'Premier League', 'flag': '🏴󠁧󠁢󠁥󠁮󠁧󠁿'},
    'seriea': {'id': 135, 'name': 'Serie A', 'flag': '🇮🇹'},
    'bundesliga': {'id': 78, 'name': 'Bundesliga', 'flag': '🇩🇪'},
    'ligue1': {'id': 61, 'name': 'Ligue 1', 'flag': '🇫🇷'},
}


def download_data(league_id: int, season: int):
    """Descarga datos de la API si no existen."""
    from src.db import get_db_session, Fixture
    from src.data import MasterCollector
    from src.api_client import CachedAPIClient
    
    with get_db_session() as db:
        existing = db.query(Fixture).filter(
            Fixture.league_id == league_id,
            Fixture.season == season
        ).count()
    
    if existing == 0:
        print("⬇️  Descargando datos de la API...")
        client = CachedAPIClient()
        collector = MasterCollector(client)
        collector.sync_full_season(
            season=season,
            league_ids=[league_id],
            include_standings=True
        )
        collector.close()
        print("   ✅ Datos descargados")
    else:
        print(f"   ✅ {existing} partidos ya en BD")


def generate_features(league_id: int, season: int) -> pd.DataFrame:
    """Genera features frescas (sin caché)."""
    from src.data.features import FeaturePipeline
    
    print("⚙️  Generando features...")
    pipeline = FeaturePipeline()
    df = pipeline.generate_training_dataset(
        league_ids=[league_id],
        season=season,
        exclude_draws=True
    )
    print(f"   ✅ {len(df)} partidos con features")
    return df


def verify_features(df: pd.DataFrame, league_name: str) -> bool:
    """Verifica la calidad de las features."""
    print("\n🔍 VERIFICACIÓN DE FEATURES")
    print("-" * 50)
    
    # Features clave que deben tener valores
    key_features = [
        'home_points_last_5', 'away_points_last_5',
        'home_goals_for_avg_5', 'away_goals_for_avg_5',
        'home_position', 'away_position',
        'h2h_total_matches'
    ]
    
    issues = []
    
    for feat in key_features:
        if feat not in df.columns:
            issues.append(f"   ❌ {feat}: NO EXISTE")
            continue
        
        nulls = df[feat].isnull().sum()
        zeros = (df[feat] == 0).sum()
        mean = df[feat].mean()
        
        status = "✅" if nulls == 0 and zeros < len(df) * 0.9 else "⚠️"
        print(f"   {status} {feat}: mean={mean:.2f}, nulls={nulls}, zeros={zeros}")
        
        if nulls > len(df) * 0.5:
            issues.append(f"   ⚠️ {feat}: {nulls} valores nulos ({nulls/len(df)*100:.0f}%)")
    
    if issues:
        print("\n⚠️  ADVERTENCIAS:")
        for issue in issues:
            print(issue)
        return False
    else:
        print("\n✅ Features verificadas correctamente")
        return True


def load_model(model_path: str):
    """Carga el modelo."""
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model


def predict(model, X: np.ndarray):
    """Hace predicciones con el modelo."""
    feature_names = model['feature_names']
    scaler = model['scaler']
    models = model['calibrated_models'] if model.get('use_calibration', True) else model['models']
    weights = model['weights']
    
    X_scaled = scaler.transform(X)
    
    all_probas = []
    all_weights = []
    
    for name, m in models.items():
        if name == 'logreg':
            probas = m.predict_proba(X_scaled)
        else:
            probas = m.predict_proba(X)
        all_probas.append(probas)
        all_weights.append(weights[name])
    
    all_probas = np.array(all_probas)
    all_weights = np.array(all_weights) / sum(all_weights)
    weighted = np.average(all_probas, axis=0, weights=all_weights)
    
    predictions = (weighted[:, 1] >= 0.5).astype(int)
    confidences = np.maximum(weighted[:, 0], weighted[:, 1])
    
    return predictions, confidences


def run_predictions(df: pd.DataFrame, model, league_info: dict, season: int, rounds: list):
    """Ejecuta predicciones para las jornadas especificadas."""
    from src.db import get_db_session, Fixture, Team
    
    feature_names = model['feature_names']
    
    with get_db_session() as db:
        teams = {t.id: t.name for t in db.query(Team).all()}
        
        total_aciertos = 0
        total_partidos = 0
        
        for r in rounds:
            jornada = f'Regular Season - {r}'
            
            fixtures = db.query(Fixture).filter(
                Fixture.league_id == league_info['id'],
                Fixture.season == season,
                Fixture.round == jornada,
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
                print(f"\n⚠️ Jornada {r}: sin partidos disponibles")
                continue
            
            fids = [p['id'] for p in partidos]
            df_round = df[df['fixture_id'].isin(fids)]
            
            if len(df_round) == 0:
                continue
            
            X = df_round[feature_names].fillna(0).values
            preds, confs = predict(model, X)
            
            print(f"\n{'='*75}")
            print(f"{league_info['flag']} JORNADA {r} - {league_info['name'].upper()}")
            print('='*75)
            
            aciertos = 0
            for i, fid in enumerate(df_round['fixture_id'].values):
                p = next((x for x in partidos if x['id'] == fid), None)
                if not p:
                    continue
                
                pred_val = preds[i]
                real_val = p['real']
                conf = confs[i]
                
                pred_txt = 'Local' if pred_val == 1 else 'Visitante'
                real_txt = 'Local' if real_val == 1 else 'Visitante'
                
                ok = pred_val == real_val
                if ok:
                    aciertos += 1
                sym = '✅' if ok else '❌'
                
                conf_mark = '🔥' if conf >= 0.75 else ''
                print(f"{sym} {p['home'][:17]:17} vs {p['away'][:17]:17} | {p['hg']}-{p['ag']} | "
                      f"Real: {real_txt:9} | Pred: {pred_txt:9} | Conf: {conf*100:.0f}% {conf_mark}")
            
            acc = aciertos / len(df_round) * 100 if len(df_round) > 0 else 0
            print(f"\n📈 RESUMEN J{r}: {aciertos}/{len(df_round)} = {acc:.1f}%")
            
            total_aciertos += aciertos
            total_partidos += len(df_round)
        
        if total_partidos > 0:
            print(f"\n{'='*75}")
            print(f"🏆 TOTAL: {total_aciertos}/{total_partidos} = {total_aciertos/total_partidos*100:.1f}%")
            print('='*75)


def main():
    parser = argparse.ArgumentParser(description='Predictor de liga con verificación de features')
    parser.add_argument('--league', '-l', choices=list(LEAGUES.keys()), required=True,
                       help='Liga a predecir')
    parser.add_argument('--round', '-r', default='15',
                       help='Jornada(s) a predecir: "15" o "10-15"')
    parser.add_argument('--season', '-s', type=int, default=2025,
                       help='Temporada (default: 2025)')
    parser.add_argument('--model', '-m', default='models/trained/ensemble_model.pkl',
                       help='Ruta al modelo')
    parser.add_argument('--force-refresh', '-f', action='store_true',
                       help='Forzar regeneración de features')
    
    args = parser.parse_args()
    
    # Parsear jornadas
    if '-' in args.round:
        start, end = map(int, args.round.split('-'))
        rounds = list(range(start, end + 1))
    else:
        rounds = [int(args.round)]
    
    league = LEAGUES[args.league]
    
    print("="*75)
    print(f"{league['flag']} PREDICTOR {league['name'].upper()} - TEMPORADA {args.season}/{args.season+1}")
    print("="*75)
    
    # 1. Descargar datos si necesario
    print("\n📥 PASO 1: Verificar datos")
    download_data(league['id'], args.season)
    
    # 2. Generar features
    print("\n📊 PASO 2: Generar features")
    df = generate_features(league['id'], args.season)
    
    # 3. Verificar features
    print("\n🔍 PASO 3: Verificar calidad")
    verify_features(df, league['name'])
    
    # 4. Cargar modelo
    print("\n🤖 PASO 4: Cargar modelo")
    model = load_model(args.model)
    print(f"   ✅ Modelo cargado: {len(model['feature_names'])} features")
    
    # 5. Ejecutar predicciones
    print("\n🎯 PASO 5: Ejecutar predicciones")
    run_predictions(df, model, league, args.season, rounds)


if __name__ == '__main__':
    main()
