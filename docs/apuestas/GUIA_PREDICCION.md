# 📋 GUÍA DE PREDICCIÓN - Estrategia HYPER COMPOUND

> **Documento de referencia para generar predicciones de apuestas**  
> Estrategia: HYPER COMPOUND | ROI: +11,400%  
> Última actualización: 29 Diciembre 2025

---

## 🎯 PROPÓSITO

Este documento define **exactamente** cómo generar predicciones siguiendo la estrategia HYPER COMPOUND, la más rentable encontrada tras probar 100+ estrategias.

---

## 🏆 RESUMEN DE LA ESTRATEGIA

| Aspecto | Valor |
|---------|-------|
| **Nombre** | HYPER COMPOUND |
| **ROI probado** | +11,400% |
| **Win Rate** | 91% |
| **Resultado ejemplo** | €20 → €2,300 en 2 meses |

---

## ⚙️ PARÁMETROS EXACTOS

```python
MIN_CONFIDENCE = 0.75      # Confianza mínima: 75%
VALUE_MARGIN = 0.01        # Margen de valor: 1%
STAKE_BASE = 0.35          # Stake base: 35% del bankroll
MAX_STAKE = 0.50           # Máximo por apuesta: 50%
MAX_BETS_DAY = 15          # Máximo apuestas por día
HIGH_CONF_MULT = 1.5       # Multiplicador si conf >= 85%
MED_CONF_MULT = 1.2        # Multiplicador si conf >= 80%
ONLY_HOME = True           # SOLO predicciones locales
ONLY_WEEKEND = True        # SOLO sábado y domingo
BET_TYPE = "DNB"           # SIEMPRE Draw No Bet
```

---

## 📊 TABLA DE CUOTAS DNB

| Confianza | Cuota DNB Objetivo |
|-----------|-------------------|
| ≥85% | 1.15 |
| 80-84% | 1.28 |
| 75-79% | 1.42 |

---

## 🔄 FLUJO DE DECISIÓN

```
┌─────────────────────────────────────────┐
│         PARTIDO DETECTADO               │
└─────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ ¿Es Sábado o Domingo? │
        └───────────────────────┘
                    │
           NO ◄─────┴─────► SÍ
            │               │
            ▼               ▼
    ┌─────────────┐ ┌───────────────────────┐
    │   IGNORAR   │ │ ¿Predicción es LOCAL? │
    └─────────────┘ └───────────────────────┘
                            │
                   NO ◄─────┴─────► SÍ
                    │               │
                    ▼               ▼
            ┌─────────────┐ ┌───────────────────┐
            │   IGNORAR   │ │ ¿Confianza ≥ 75%? │
            └─────────────┘ └───────────────────┘
                                    │
                           NO ◄─────┴─────► SÍ
                            │               │
                            ▼               ▼
                    ┌─────────────┐ ┌──────────────────────┐
                    │   IGNORAR   │ │ ¿Hay Value Bet?      │
                    └─────────────┘ │ conf > prob_impl+1%  │
                                    └──────────────────────┘
                                            │
                                   NO ◄─────┴─────► SÍ
                                    │               │
                                    ▼               ▼
                            ┌─────────────┐ ┌─────────────────┐
                            │   IGNORAR   │ │ CALCULAR STAKE  │
                            └─────────────┘ │ COMPOUND Y      │
                                            │ RECOMENDAR      │
                                            └─────────────────┘
```

---

## 💰 FÓRMULA DEL STAKE COMPOUND

### Paso 1: Calcular Stake Base Compound

```python
stake = bankroll × 0.35 × (1 + (bankroll / bankroll_inicial - 1) × 0.5)
```

### Paso 2: Aplicar Multiplicador por Confianza

```python
if confianza >= 0.85:
    stake = stake × 1.5
elif confianza >= 0.80:
    stake = stake × 1.2
```

### Paso 3: Aplicar Límites

```python
stake_final = max(1.0, min(stake, bankroll × 0.50))
```

### Ejemplo Completo

```
Bankroll inicial: €20
Bankroll actual: €150
Confianza: 82%

Paso 1: stake = 150 × 0.35 × (1 + (150/20 - 1) × 0.5)
              = 52.5 × (1 + 6.5 × 0.5)
              = 52.5 × 4.25
              = €223.12

Paso 2: stake = 223.12 × 1.2 = €267.75 (porque 82% >= 80%)

Paso 3: max_stake = 150 × 0.50 = €75
        stake_final = min(267.75, 75) = €75
```

---

## ✅ VALUE BET CHECK

```python
def is_value_bet(confianza, cuota):
    prob_implicita = 1 / cuota
    return confianza > prob_implicita + 0.01
```

### Ejemplo

```
Confianza: 78%
Cuota DNB: 1.42
Prob. implícita: 1/1.42 = 70.4%

¿Value? 78% > 70.4% + 1%?
        78% > 71.4%?
        SÍ ✅ → APOSTAR
```

---

## 🚫 CUÁNDO NO APOSTAR

| Condición | Acción |
|-----------|--------|
| Lunes a Viernes | ❌ No apostar |
| Predicción visitante | ❌ Ignorar |
| Confianza < 75% | ❌ Ignorar |
| Sin value (conf ≤ prob_impl + 1%) | ❌ Ignorar |
| Cuota real < objetivo | ❌ No apostar |
| Ya 15 apuestas hoy | ❌ Parar |
| Stop-loss (perdido 40%) | ❌ Parar |

---

## 📝 FORMATO DE SALIDA

```
🏆 HYPER COMPOUND - [DÍA] [DD/MM/YYYY]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Bankroll: €XXX.XX
📋 Estrategia: HYPER COMPOUND (35% Compound + 75% conf)

💰 VALUE BETS DEL DÍA
────────────────────────────────────────

⭐⭐⭐ 1. [EQUIPO_LOCAL] vs [EQUIPO_VISITANTE]
   📍 HH:MM | [LIGA]
   🎯 LOCAL: [EQUIPO_LOCAL] (DNB)
   📊 Confianza: XX%
   💵 Apostar: €XX.XX | Cuota objetivo: ≥X.XX
   💰 Ganancia potencial: €XX.XX

────────────────────────────────────────
📊 RESUMEN:
   Total apuestas: X
   Total a invertir: €XXX.XX
   Ganancia potencial: €XXX.XX

⚠️ IMPORTANTE:
   • Solo apostar si cuota real ≥ cuota objetivo
   • SIEMPRE Draw No Bet
   • Stop-loss: 40% del bankroll
🏆━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━🏆
```

### Sistema de Estrellas

```
⭐⭐⭐ = Confianza ≥ 85% (stake ×1.5)
⭐⭐   = Confianza 80-84% (stake ×1.2)
⭐     = Confianza 75-79% (stake ×1.0)
```

---

## 🔧 SCRIPT DE EJECUCIÓN

```bash
cd AnalizadorFutbol/backend
source venv/bin/activate
python value_betting_hyper.py --bankroll 50
```

---

## 📊 REGLAS DE ORO

1. **SOLO FIN DE SEMANA** - Win rate 89% vs 76%
2. **SOLO LOCALES** - Win rate 91% vs 83%
3. **SIEMPRE DNB** - Empates no cuentan como pérdida
4. **COMPOUND** - Stake crece con el bankroll
5. **CONFIANZA 75%+** - Umbral estricto
6. **STOP-LOSS 40%** - Protección del capital

---

## ⚠️ ADVERTENCIA DE RIESGO

```
DRAWDOWN HISTÓRICO: -62% (€20 → €7.63 → €2,300)

Esta estrategia es AGRESIVA. El bankroll puede bajar 
significativamente antes de recuperarse. Solo usar 
con dinero que puedas permitirte perder.
```

---

*Guía para uso interno del sistema AnalizadorFutbol*
*100+ estrategias probadas | 1,604 partidos analizados*
