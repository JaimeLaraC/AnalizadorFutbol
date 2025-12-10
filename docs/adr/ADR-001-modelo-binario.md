# ADR-001: Modelo de Clasificación Binaria (Sin Empates)

## Estado
**Aceptado** - 2024-12-10

## Contexto
El sistema debe predecir resultados de partidos de fútbol con el objetivo de maximizar la fiabilidad de las predicciones para apuestas. 

En fútbol, los resultados posibles son:
- **1**: Victoria del equipo local
- **X**: Empate
- **2**: Victoria del equipo visitante

Los empates son inherentemente difíciles de predecir y representan ~25-30% de los partidos. Incluirlos reduce significativamente la precisión general del modelo.

## Decisión
**Implementar un modelo de clasificación binaria que excluye completamente los empates.**

- Los partidos históricos que terminaron en empate se **excluyen del dataset de entrenamiento**
- El modelo predice únicamente P(Local gana) vs P(Visitante gana)
- Los partidos futuros solo se recomiendan si la probabilidad del ganador supera el 75%

## Consecuencias

### Positivas
- Mayor precisión en las predicciones (solo 2 clases en vez de 3)
- Modelo más simple y fácil de interpretar
- Probabilidades mejor calibradas

### Negativas
- Se descartan ~25-30% de partidos históricos para entrenamiento
- Algunos partidos del día podrían quedar sin predicción recomendada
- No se puede apostar a empates (el usuario acepta esto)

### Riesgos
- Si el modelo tiene sesgo hacia una clase, podría afectar ROI
- Partidos que terminan en empate se consideran "pérdidas" en apuestas

## Alternativas Consideradas

### 1. Modelo de 3 clases + filtro
- Predecir 1/X/2 pero filtrar partidos con P(X) alto
- **Rechazado**: Mayor complejidad, difícil calibrar 3 probabilidades

### 2. Modelo de 3 clases con peso reducido para empates
- Downsampling de empates en training
- **Rechazado**: Aún introduce ruido y complejidad innecesaria

### 3. Dos modelos separados
- Uno para detectar empates, otro para 1/2
- **Rechazado**: Excesiva complejidad para el beneficio

## Referencias
- Requisitos del usuario: "Quiero 1/2, o gana uno o gana el otro. Empate no vale"
- Objetivo: "Máxima fiabilidad en las predicciones top 5"
