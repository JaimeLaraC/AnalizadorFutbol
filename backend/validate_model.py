#!/usr/bin/env python3
"""
validate_model.py - Script de Validación del Modelo de Predicción de Fútbol

Este script permite validar el modelo entrenado usando datos de temporadas
que NO fueron incluidas en el entrenamiento.

Uso:
    python validate_model.py --league laliga --season 2025 --rounds 10-15
    python validate_model.py --league premier --season 2025 --rounds 10-15
    python validate_model.py --league all --season 2025 --rounds 10-15

Autor: AnalizadorFutbol
"""

import argparse
import pandas as pd
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Configuración de ligas
LEAGUES = {
    'laliga': {'id': 140, 'name': 'La Liga', 'flag': '🇪🇸'},
    'premier': {'id': 39, 'name': 'Premier League', 'flag': '🏴󠁧󠁢󠁥󠁮󠁧󠁿'},
    'seriea': {'id': 135, 'name': 'Serie A', 'flag': '🇮🇹'},
    'bundesliga': {'id': 78, 'name': 'Bundesliga', 'flag': '🇩🇪'},
    'ligue1': {'id': 61, 'name': 'Ligue 1', 'flag': '🇫🇷'},
}


class ModelValidator:
    """Clase para validar el modelo de predicción."""
    
    def __init__(self, model_path: str = 'models/trained/ensemble_model.pkl'):
        """
        Inicializa el validador.
        
        Args:
            model_path: Ruta al archivo del modelo entrenado
        """
        self.model_path = Path(model_path)
        self.model = None
        self.feature_names = None
        self.scaler = None
        self.models = None
        self.weights = None
        self._load_model()
    
    def _load_model(self):
        """Carga el modelo desde el archivo pickle."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {self.model_path}")
        
        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        self.feature_names = self.model['feature_names']
        self.scaler = self.model['scaler']
        self.models = (self.model['calibrated_models'] 
                      if self.model.get('use_calibration', True) 
                      else self.model['models'])
        self.weights = self.model['weights']
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Hace predicciones sobre features.
        
        Args:
            X: Features en formato numpy array
            
        Returns:
            Tuple de (predicciones, confianzas)
        """
        X_scaled = self.scaler.transform(X)
        
        all_probas = []
        all_weights = []
        
        for name, model in self.models.items():
            if name == 'logreg':
                probas = model.predict_proba(X_scaled)
            else:
                probas = model.predict_proba(X)
            all_probas.append(probas)
            all_weights.append(self.weights[name])
        
        all_probas = np.array(all_probas)
        all_weights = np.array(all_weights) / sum(all_weights)
        weighted_probas = np.average(all_probas, axis=0, weights=all_weights)
        
        predictions = (weighted_probas[:, 1] >= 0.5).astype(int)
        confidences = np.maximum(weighted_probas[:, 0], weighted_probas[:, 1])
        
        return predictions, confidences


def download_and_generate_features(league_id: int, season: int) -> Optional[pd.DataFrame]:
    """
    Descarga datos de la API y genera features.
    
    Args:
        league_id: ID de la liga en API-Football
        season: Temporada (año de inicio)
        
    Returns:
        DataFrame con features o None si falla
    """
    from src.db import get_db_session, Fixture
    from src.data import MasterCollector
    from src.api_client import CachedAPIClient
    from src.data.features import FeaturePipeline
    
    # Verificar si ya hay datos
    with get_db_session() as db:
        existing = db.query(Fixture).filter(
            Fixture.league_id == league_id,
            Fixture.season == season
        ).count()
    
    if existing == 0:
        print(f"⬇️  Descargando datos de la API...")
        client = CachedAPIClient()
        collector = MasterCollector(client)
        collector.sync_full_season(
            season=season,
            league_ids=[league_id],
            include_standings=True
        )
        collector.close()
    
    # Generar features
    print(f"⚙️  Generando features...")
    pipeline = FeaturePipeline()
    df = pipeline.generate_training_dataset(
        league_ids=[league_id],
        season=season,
        exclude_draws=True
    )
    
    return df


def validate_rounds(
    validator: ModelValidator,
    df: pd.DataFrame,
    league_id: int,
    season: int,
    rounds: List[int]
) -> Dict:
    """
    Valida el modelo en las jornadas especificadas.
    
    Args:
        validator: Instancia del validador
        df: DataFrame con features
        league_id: ID de la liga
        season: Temporada
        rounds: Lista de jornadas a validar
        
    Returns:
        Diccionario con resultados
    """
    from src.db import get_db_session, Fixture, Team
    
    results = {
        'league_id': league_id,
        'season': season,
        'rounds': {},
        'total': {'aciertos': 0, 'partidos': 0}
    }
    
    with get_db_session() as db:
        teams = {t.id: t.name for t in db.query(Team).all()}
        
        for r in rounds:
            jornada = f'Regular Season - {r}'
            
            fixtures = db.query(Fixture).filter(
                Fixture.league_id == league_id,
                Fixture.season == season,
                Fixture.round == jornada,
                Fixture.status == 'FT'
            ).all()
            
            # Filtrar sin empates y con features disponibles
            partidos = []
            for f in fixtures:
                if f.home_goals != f.away_goals and f.id in df['fixture_id'].values:
                    partidos.append({
                        'id': f.id,
                        'home': teams.get(f.home_team_id, '?'),
                        'away': teams.get(f.away_team_id, '?'),
                        'home_goals': f.home_goals,
                        'away_goals': f.away_goals,
                        'real': 1 if f.home_goals > f.away_goals else 0
                    })
            
            if not partidos:
                continue
            
            # Obtener features
            fids = [p['id'] for p in partidos]
            df_round = df[df['fixture_id'].isin(fids)]
            
            if len(df_round) == 0:
                continue
            
            # Predecir
            X = df_round[validator.feature_names].fillna(0).values
            predictions, confidences = validator.predict(X)
            
            # Procesar resultados
            round_results = []
            aciertos = 0
            
            for i, fid in enumerate(df_round['fixture_id'].values):
                p = next((x for x in partidos if x['id'] == fid), None)
                if not p:
                    continue
                
                pred = predictions[i]
                real = p['real']
                conf = confidences[i]
                
                ok = pred == real
                if ok:
                    aciertos += 1
                
                round_results.append({
                    'home': p['home'],
                    'away': p['away'],
                    'score': f"{p['home_goals']}-{p['away_goals']}",
                    'real': 'Local' if real == 1 else 'Visitante',
                    'pred': 'Local' if pred == 1 else 'Visitante',
                    'conf': conf,
                    'ok': ok
                })
            
            results['rounds'][r] = {
                'partidos': round_results,
                'aciertos': aciertos,
                'total': len(round_results),
                'accuracy': aciertos / len(round_results) if round_results else 0
            }
            
            results['total']['aciertos'] += aciertos
            results['total']['partidos'] += len(round_results)
    
    if results['total']['partidos'] > 0:
        results['total']['accuracy'] = (
            results['total']['aciertos'] / results['total']['partidos']
        )
    else:
        results['total']['accuracy'] = 0
    
    return results


def print_results(results: Dict, league_info: Dict):
    """Imprime los resultados de forma formateada."""
    flag = league_info['flag']
    name = league_info['name']
    
    print(f"\n{'='*75}")
    print(f"{flag} VALIDACIÓN {name.upper()} - TEMPORADA {results['season']}/{results['season']+1}")
    print('='*75)
    
    for r, data in sorted(results['rounds'].items()):
        acc = data['accuracy'] * 100
        print(f"\n📊 JORNADA {r} ({data['aciertos']}/{data['total']} = {acc:.1f}%)")
        print("-"*75)
        
        for p in data['partidos']:
            symbol = '✅' if p['ok'] else '❌'
            print(f"{symbol} {p['home'][:18]:18} vs {p['away'][:18]:18} | "
                  f"{p['score']} | Real: {p['real']:9} | Pred: {p['pred']:9} | "
                  f"Conf: {p['conf']*100:.0f}%")
    
    # Resumen
    total = results['total']
    if total['partidos'] > 0:
        print(f"\n{'='*75}")
        print(f"🏆 TOTAL: {total['aciertos']}/{total['partidos']} = "
              f"{total['accuracy']*100:.1f}%")
        print('='*75)


def main():
    parser = argparse.ArgumentParser(
        description='Validar el modelo de predicción con datos no entrenados',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python validate_model.py --league laliga --season 2025 --rounds 10-15
  python validate_model.py --league premier --season 2025 --rounds 10-15
  python validate_model.py --league all --season 2025 --rounds 10-15
        """
    )
    
    parser.add_argument(
        '--league', '-l',
        choices=['laliga', 'premier', 'seriea', 'bundesliga', 'ligue1', 'all'],
        default='laliga',
        help='Liga a validar (default: laliga)'
    )
    
    parser.add_argument(
        '--season', '-s',
        type=int,
        default=2025,
        help='Temporada a validar (default: 2025)'
    )
    
    parser.add_argument(
        '--rounds', '-r',
        default='10-15',
        help='Jornadas a validar en formato "inicio-fin" (default: 10-15)'
    )
    
    parser.add_argument(
        '--model', '-m',
        default='models/trained/ensemble_model.pkl',
        help='Ruta al modelo (default: models/trained/ensemble_model.pkl)'
    )
    
    args = parser.parse_args()
    
    # Parsear jornadas
    if '-' in args.rounds:
        start, end = map(int, args.rounds.split('-'))
        rounds = list(range(start, end + 1))
    else:
        rounds = [int(r) for r in args.rounds.split(',')]
    
    # Cargar validador
    print("🤖 Cargando modelo...")
    validator = ModelValidator(args.model)
    print(f"   ✅ Modelo cargado: {len(validator.feature_names)} features")
    
    # Determinar ligas a validar
    if args.league == 'all':
        leagues_to_validate = list(LEAGUES.keys())
    else:
        leagues_to_validate = [args.league]
    
    # Validar cada liga
    all_results = []
    
    for league_key in leagues_to_validate:
        league = LEAGUES[league_key]
        print(f"\n{league['flag']} Procesando {league['name']}...")
        
        # Buscar o generar features
        cache_file = Path(f"data/test_{league_key}_{args.season}.csv")
        
        if cache_file.exists():
            print(f"   📂 Cargando features desde caché...")
            df = pd.read_csv(cache_file)
        else:
            df = download_and_generate_features(league['id'], args.season)
            if df is not None and len(df) > 0:
                df.to_csv(cache_file, index=False)
                print(f"   💾 Features guardadas en {cache_file}")
        
        if df is None or len(df) == 0:
            print(f"   ⚠️ No hay datos disponibles")
            continue
        
        print(f"   📊 {len(df)} partidos con features")
        
        # Validar
        results = validate_rounds(validator, df, league['id'], args.season, rounds)
        results['league_name'] = league['name']
        all_results.append((league, results))
        
        # Mostrar resultados
        print_results(results, league)
    
    # Resumen global si hay múltiples ligas
    if len(all_results) > 1:
        total_aciertos = sum(r[1]['total']['aciertos'] for r in all_results)
        total_partidos = sum(r[1]['total']['partidos'] for r in all_results)
        
        print(f"\n{'='*75}")
        print("🌍 RESUMEN GLOBAL")
        print('='*75)
        
        for league, results in all_results:
            t = results['total']
            if t['partidos'] > 0:
                print(f"  {league['flag']} {league['name']:20} | "
                      f"{t['aciertos']:2}/{t['partidos']:2} = {t['accuracy']*100:.1f}%")
        
        if total_partidos > 0:
            global_acc = total_aciertos / total_partidos
            print(f"\n  🏆 TOTAL: {total_aciertos}/{total_partidos} = {global_acc*100:.1f}%")


if __name__ == '__main__':
    main()
