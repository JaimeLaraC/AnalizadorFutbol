#!/usr/bin/env python3
"""Script de predicciones Jornada 11 La Liga 2025/26"""
import pandas as pd
import pickle
import numpy as np

# 1. Cargar datos
df = pd.read_csv('data/test_2025.csv')
print(f"📊 Total partidos 2025: {len(df)}")

# 2. Jornada 11 IDs (sin empates)
j11_ids = [1390923, 1390928, 1390920, 1390926, 1390925, 1390924, 1390919, 1390921, 1390922]

partidos_info = {
    1390923: {'home': 'Getafe', 'away': 'Girona', 'score': '2-1'},
    1390928: {'home': 'Villarreal', 'away': 'Rayo Vallecano', 'score': '4-0'},
    1390920: {'home': 'Atletico Madrid', 'away': 'Sevilla', 'score': '3-0'},
    1390926: {'home': 'Real Sociedad', 'away': 'Athletic Club', 'score': '3-2'},
    1390925: {'home': 'Real Madrid', 'away': 'Valencia', 'score': '4-0'},
    1390924: {'home': 'Levante', 'away': 'Celta Vigo', 'score': '1-2'},
    1390919: {'home': 'Alaves', 'away': 'Espanyol', 'score': '2-1'},
    1390921: {'home': 'Barcelona', 'away': 'Elche', 'score': '3-1'},
    1390922: {'home': 'Real Betis', 'away': 'Mallorca', 'score': '3-0'},
}

df_j10 = df[df['fixture_id'].isin(j11_ids)]
print(f"📊 Partidos J11 (sin empates): {len(df_j10)}")

# 3. Cargar modelo
print("🤖 Cargando modelo...")
with open('models/trained/ensemble_model.pkl', 'rb') as f:
    model = pickle.load(f)

feature_names = model['feature_names']
scaler = model['scaler']
models = model['calibrated_models'] if model['use_calibration'] else model['models']
weights = model['weights']

# 4. Preparar features
X = df_j10[feature_names].fillna(0).values
y_real = df_j10['target'].values
fixture_ids = df_j10['fixture_id'].values

X_scaled = scaler.transform(X)

# 5. Combinar predicciones
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
weighted_probas = np.average(all_probas, axis=0, weights=all_weights)

predictions = (weighted_probas[:, 1] >= 0.5).astype(int)
confidences = np.maximum(weighted_probas[:, 0], weighted_probas[:, 1])

# 6. Resultados
print("\n" + "="*70)
print("📊 PREDICCIONES JORNADA 11 - LA LIGA 2025/26")
print("   (Datos NUNCA vistos por el modelo)")
print("="*70 + "\n")

aciertos = 0
for i, fid in enumerate(fixture_ids):
    info = partidos_info.get(int(fid), {'home': '?', 'away': '?', 'score': '?-?'})
    
    pred = predictions[i]
    real = y_real[i]
    conf = confidences[i]
    
    pred_txt = "Local" if pred == 1 else "Visitante"
    real_txt = "Local" if real == 1 else "Visitante"
    
    acierto = pred == real
    if acierto:
        aciertos += 1
    symbol = "✅" if acierto else "❌"
    
    print(f"{symbol} {info['home']:18} vs {info['away']:18} | {info['score']} | Real: {real_txt:9} | Pred: {pred_txt:9} | Conf: {conf*100:.0f}%")

# 7. Resumen
total = len(predictions)
print("\n" + "="*70)
print(f"📈 RESUMEN: {aciertos}/{total} aciertos = {aciertos/total*100:.1f}% ACCURACY")
print("="*70)
