# 🔮 Guía de Validación del Modelo de Predicción

Este documento explica cómo validar el modelo de predicción de partidos de fútbol usando datos que **NO** fueron usados durante el entrenamiento.

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Requisitos](#requisitos)
3. [Uso del Script](#uso-del-script)
4. [Ejemplos](#ejemplos)
5. [Interpretación de Resultados](#interpretación-de-resultados)
6. [Métricas Obtenidas](#métricas-obtenidas)

---

## 📖 Introducción

El script `validate_model.py` permite validar el modelo entrenado usando partidos de temporadas nuevas que el modelo nunca ha visto. Esto es crucial para evaluar el rendimiento real del modelo en producción.

### ¿Por qué es importante?

- **Evitar overfitting**: El modelo puede tener buen rendimiento en datos de entrenamiento pero fallar en datos nuevos
- **Medir rendimiento real**: Las métricas en datos no vistos reflejan cómo funcionará el modelo en predicciones futuras
- **Validar por confianza**: Permite verificar si las predicciones con alta confianza son más precisas

---

## 🛠️ Requisitos

1. **Modelo entrenado**: El archivo `models/trained/ensemble_model.pkl` debe existir
2. **Base de datos**: PostgreSQL con datos de partidos
3. **API-Football**: Clave de API configurada en `.env` para descargar datos nuevos

---

## 💻 Uso del Script

### Sintaxis Básica

```bash
cd backend
source venv/bin/activate
python validate_model.py --league <liga> --season <temporada> --rounds <jornadas>
```

### Argumentos

| Argumento | Descripción | Default |
|-----------|-------------|---------|
| `--league`, `-l` | Liga a validar: `laliga`, `premier`, `seriea`, `bundesliga`, `ligue1`, `all` | `laliga` |
| `--season`, `-s` | Temporada (año de inicio) | `2025` |
| `--rounds`, `-r` | Jornadas: `10-15` o `1,5,10` | `10-15` |
| `--model`, `-m` | Ruta al modelo | `models/trained/ensemble_model.pkl` |

---

## 📝 Ejemplos

### Validar La Liga Jornadas 10-15

```bash
python validate_model.py --league laliga --season 2025 --rounds 10-15
```

### Validar Premier League

```bash
python validate_model.py --league premier --season 2025 --rounds 10-15
```

### Validar Todas las Ligas

```bash
python validate_model.py --league all --season 2025 --rounds 10-15
```

### Validar Jornadas Específicas

```bash
python validate_model.py --league laliga --season 2025 --rounds 1,5,10,15
```

---

## 📊 Interpretación de Resultados

### Output del Script

```
📊 JORNADA 10 (6/8 = 75.0%)
---------------------------------------------------------------------------
✅ Real Madrid       vs Valencia          | 4-0 | Real: Local     | Pred: Local     | Conf: 80%
❌ Athletic Club     vs Getafe            | 0-1 | Real: Visitante | Pred: Local     | Conf: 67%
```

### Columnas

| Columna | Descripción |
|---------|-------------|
| ✅/❌ | Acierto o fallo |
| Partido | Equipos (Local vs Visitante) |
| Score | Resultado real |
| Real | Quién ganó realmente |
| Pred | Predicción del modelo |
| Conf | Confianza de la predicción (%) |

### Umbral de Confianza

- **< 55%**: Baja confianza, resultado muy incierto
- **55-65%**: Confianza media
- **65-75%**: Alta confianza
- **> 75%**: Muy alta confianza - modelo "seguro" de su predicción

---

## 📈 Métricas Obtenidas

### Resultados de Validación (Diciembre 2025)

#### 🇪🇸 La Liga 2025/26 (J10-J15)

| Jornada | Aciertos | Accuracy |
|---------|----------|----------|
| J10 | 4/8 | 50.0% |
| J11 | 8/9 | 88.9% |
| J12 | 6/7 | 85.7% |
| J13 | 5/7 | 71.4% |
| J14 | 4/7 | 57.1% |
| J15 | 6/8 | 75.0% |
| **TOTAL** | **33/46** | **71.7%** |

#### 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League 2025/26 (J10-J15)

| Jornada | Aciertos | Accuracy |
|---------|----------|----------|
| J10 | 6/8 | 75.0% |
| J11 | 7/7 | **100%** 🎯 |
| J12 | 5/9 | 55.6% |
| J13 | 5/9 | 55.6% |
| J14 | 4/7 | 57.1% |
| J15 | 5/7 | 71.4% |
| **TOTAL** | **32/47** | **68.1%** |

#### 🌍 Resumen Global

| Liga | Accuracy |
|------|----------|
| La Liga | 71.7% |
| Premier League | 68.1% |
| **PROMEDIO** | **69.9%** |

---

## 🎯 Conclusiones

1. **El modelo tiene ~70% de accuracy** en datos completamente nuevos
2. **Las predicciones con alta confianza (>75%)** tienden a ser más precisas
3. **Los empates se excluyen** porque el modelo solo predice ganador
4. **Resultados sorpresa** (ej: Real Madrid 0-2 Celta Vigo) siempre ocurrirán en fútbol

---

## 🔧 Archivos Generados

El script genera archivos de caché para evitar re-descargar datos:

- `data/test_laliga_2025.csv` - Features La Liga 2025/26
- `data/test_premier_2025.csv` - Features Premier League 2025/26
- etc.

---

## 📁 Estructura de Archivos

```
backend/
├── validate_model.py          # Script principal de validación
├── models/trained/
│   └── ensemble_model.pkl     # Modelo entrenado
├── data/
│   ├── training_data.csv      # Datos de entrenamiento (2020-2024)
│   ├── test_laliga_2025.csv   # Datos de validación La Liga
│   └── test_premier_2025.csv  # Datos de validación Premier
└── docs/
    └── VALIDATION_GUIDE.md    # Esta documentación
```
