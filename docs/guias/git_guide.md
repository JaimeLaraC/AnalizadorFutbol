# 📖 Guía de Desarrollo - Git Flow

## Ramas Principales

| Rama | Propósito | Protegida |
|------|-----------|-----------|
| `main` | Código en producción | ✅ |
| `develop` | Integración de features | ✅ |

## Ramas de Trabajo

| Prefijo | Uso | Ejemplo |
|---------|-----|---------|
| `feature/` | Nueva funcionalidad | `feature/api-client` |
| `fix/` | Corrección de bug | `fix/cache-issue` |
| `refactor/` | Refactorización | `refactor/clean-models` |
| `docs/` | Documentación | `docs/readme-update` |
| `release/` | Preparar release | `release/v1.0.0` |
| `hotfix/` | Fix urgente en prod | `hotfix/critical-bug` |

---

## Workflow

### 1. Nueva Feature
```bash
# Desde develop
git checkout develop
git pull origin develop
git checkout -b feature/nombre-feature

# Trabajar...
git add .
git commit -m "feat: descripción"

# Push y crear PR
git push origin feature/nombre-feature
# Crear PR en GitHub: feature/xxx → develop
```

### 2. Review y Merge
- Crear Pull Request hacia `develop`
- Esperar revisión
- Mergear cuando esté aprobado

### 3. Release
```bash
git checkout develop
git checkout -b release/v1.0.0
# Ajustes finales, bump version...
git push origin release/v1.0.0
# PR: release/v1.0.0 → main
# Después: merge también a develop
```

---

## Conventional Commits

### Formato
```
<tipo>(<scope>): <descripción>

[cuerpo opcional]

[footer opcional]
```

### Tipos
| Tipo | Cuándo usar |
|------|-------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Solo documentación |
| `style` | Formato (no afecta lógica) |
| `refactor` | Cambio sin nueva func. ni fix |
| `test` | Añadir/modificar tests |
| `chore` | Mantenimiento (deps, config) |
| `perf` | Mejora de rendimiento |

### Ejemplos
```
feat(api): añadir endpoint de predicciones
fix(model): corregir cálculo de probabilidades
docs: actualizar README con instrucciones
test(collector): añadir tests para fixtures
chore: actualizar dependencias
```

---

## Template de PR

```markdown
## Descripción
[Qué hace este PR]

## Tipo de cambio
- [ ] feat: Nueva funcionalidad
- [ ] fix: Corrección de bug
- [ ] refactor: Refactorización
- [ ] docs: Documentación

## Checklist
- [ ] Tests pasan
- [ ] Código documentado
- [ ] Sin conflictos con develop
```
