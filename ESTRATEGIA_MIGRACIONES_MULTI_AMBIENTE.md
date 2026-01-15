# Estrategia de Migraciones Multi-Ambiente

## Problema Actual

Cuando trabajamos con múltiples ambientes (Desarrollo, Calidad, Producción), es común que surjan conflictos de migraciones porque:

1. **Ramas paralelas**: Cada ambiente puede tener su propia rama con migraciones
2. **Cambios simultáneos**: Múltiples desarrolladores crean migraciones en paralelo
3. **Sincronización**: Las migraciones no se sincronizan correctamente entre ambientes
4. **Merge conflicts**: Git detecta conflictos al hacer merge de ramas

## Solución: Flujo de Trabajo Recomendado

### 1. Estructura de Ramas

```
main (Producción)
  ↑
  ├── release/vX.X.X (Calidad)
  │     ↑
  │     └── develop (Desarrollo)
  │           ↑
  │           └── feature/nombre-feature (Features)
```

**Ramas principales:**
- **main**: Código en producción (solo merges de release)
- **release/vX.X.X**: Rama de calidad/staging (merges de develop)
- **develop**: Rama de desarrollo (merges de features)
- **feature/nombre-feature**: Ramas de características individuales

### 2. Política de Migraciones

#### A. Numeración Secuencial Global

**Regla**: Todos los ambientes usan la misma secuencia numérica de migraciones.

```
✓ Correcto:
- 0044_merge_20260110_1719.py (Merge anterior)
- 0045_logpropuesta.py (Nueva migración)
- 0046_agregar_campo_x.py (Siguiente)

✗ Incorrecto:
- 0044_merge_20260110_1719.py (Producción)
- 0044_logpropuesta.py (Desarrollo - CONFLICTO!)
- 0045_agregar_campo_x.py (Calidad - CONFLICTO!)
```

#### B. Crear Migraciones Solo en develop

**Regla**: Las migraciones se crean SOLO en la rama `develop`, nunca en feature branches.

```bash
# ✗ NO HACER ESTO (en feature branch):
git checkout feature/nueva-funcionalidad
python manage.py makemigrations
git commit -m "Agregar migración"

# ✓ HACER ESTO:
git checkout develop
python manage.py makemigrations
git commit -m "Agregar migración"
git push origin develop
```

#### C. Merge de Features Sin Migraciones

Las ramas feature deben hacer merge a develop ANTES de crear migraciones.

```bash
# 1. Crear feature branch desde develop
git checkout develop
git pull origin develop
git checkout -b feature/nueva-funcionalidad

# 2. Hacer cambios en modelos
# ... editar models.py ...

# 3. Hacer commit (SIN migración)
git add inventario/models.py
git commit -m "Agregar modelo NuevoModelo"
git push origin feature/nueva-funcionalidad

# 4. Crear Pull Request
# ... en GitHub ...

# 5. Hacer merge a develop
git checkout develop
git pull origin develop
git merge feature/nueva-funcionalidad
git push origin develop

# 6. AHORA crear migración en develop
python manage.py makemigrations
git add inventario/migrations/
git commit -m "Migración para NuevoModelo"
git push origin develop
```

### 3. Flujo de Deployments

```
DESARROLLO (develop)
    ↓ (cuando está listo)
CALIDAD (release/vX.X.X)
    ↓ (cuando pasa QA)
PRODUCCIÓN (main)
```

#### Paso 1: Merge develop → release

```bash
# En servidor de calidad
cd ~/inventario/inventario_hospitalario
git checkout release/v1.0.0
git pull origin release/v1.0.0
git merge develop
git push origin release/v1.0.0

# Ejecutar migraciones
docker exec -it inventario_dev python manage.py migrate
docker-compose restart web
```

#### Paso 2: Merge release → main

```bash
# En servidor de producción
cd ~/inventario/inventario_hospitalario
git checkout main
git pull origin main
git merge release/v1.0.0
git push origin main

# Ejecutar migraciones
docker exec -it inventario_dev_2 python manage.py migrate
docker-compose restart web
```

### 4. Resolución de Conflictos

Si ocurre un conflicto de migraciones:

#### Opción A: Crear Migración de Merge (Recomendado)

```bash
# En el ambiente donde ocurrió el conflicto
python manage.py makemigrations --merge

# Esto crea una migración merge que resuelve el conflicto
# Ejemplo: 0045_merge_20260115_1800.py

git add inventario/migrations/
git commit -m "Resolver conflicto de migraciones"
git push origin nombre-rama
```

#### Opción B: Rebase (Para ramas feature)

```bash
# Si estás en una rama feature y develop tiene nuevas migraciones
git checkout feature/tu-feature
git rebase develop

# Si hay conflictos, resolverlos manualmente
# Luego continuar
git rebase --continue
```

### 5. Checklist para Cada Cambio

Antes de hacer commit de cambios en modelos:

- [ ] ¿Estoy en la rama `develop`?
- [ ] ¿Hice `git pull origin develop` para sincronizar?
- [ ] ¿Edité los modelos correctamente?
- [ ] ¿Ejecuté `python manage.py makemigrations`?
- [ ] ¿Verifiqué que la migración se creó correctamente?
- [ ] ¿Ejecuté `python manage.py migrate` localmente para probar?
- [ ] ¿El archivo de migración tiene un nombre único y secuencial?
- [ ] ¿Hice commit de AMBOS: models.py Y migrations/?

### 6. Configuración de Git para Evitar Conflictos

#### A. Configurar merge strategy para migraciones

```bash
# En la raíz del proyecto, crear .gitattributes
echo "inventario/migrations/*.py merge=union" >> .gitattributes

# Esto hace que Git use estrategia "union" para archivos de migraciones
git add .gitattributes
git commit -m "Configurar merge strategy para migraciones"
```

#### B. Configurar pre-commit hooks (Opcional)

Crear archivo `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Verificar que no haya migraciones sin aplicar
python manage.py migrate --check

if [ $? -ne 0 ]; then
    echo "Error: Hay migraciones sin aplicar"
    exit 1
fi

exit 0
```

### 7. Mejores Prácticas

#### ✓ HACER

1. **Crear migraciones en develop**: Siempre en la rama principal de desarrollo
2. **Usar nombres descriptivos**: `0045_agregar_campo_descripcion_producto.py`
3. **Probar localmente**: Ejecutar `migrate` antes de hacer commit
4. **Documentar cambios**: Agregar comentarios en migraciones complejas
5. **Sincronizar frecuentemente**: `git pull` antes de empezar trabajo
6. **Hacer commits pequeños**: Una migración = un commit
7. **Usar merge commits**: Preserva historial de cambios

#### ✗ NO HACER

1. **Crear migraciones en feature branches**: Causa conflictos
2. **Editar migraciones después de hacer push**: Rompe sincronización
3. **Hacer merge de ramas sin sincronizar**: Causa conflictos
4. **Usar rebase en ramas compartidas**: Reescribe historio
5. **Ignorar conflictos de migraciones**: Causa problemas en BD
6. **Hacer push de migraciones sin probar**: Puede romper producción
7. **Mezclar cambios de modelos sin migraciones**: Inconsistencia

### 8. Ejemplo Completo de Flujo

```bash
# 1. Desarrollador en rama feature
git checkout feature/agregar-log-propuesta
# ... edita models.py ...
git add inventario/models.py
git commit -m "Agregar modelo LogPropuesta"
git push origin feature/agregar-log-propuesta

# 2. Crear Pull Request en GitHub
# ... esperar review y aprobación ...

# 3. Hacer merge a develop
git checkout develop
git pull origin develop
git merge feature/agregar-log-propuesta
git push origin develop

# 4. Crear migración en develop
python manage.py makemigrations
# Genera: 0045_logpropuesta.py
git add inventario/migrations/0045_logpropuesta.py
git commit -m "Migración: Agregar tabla LogPropuesta"
git push origin develop

# 5. Probar en ambiente de desarrollo
docker exec -it inventario_dev python manage.py migrate
# ✓ Migración aplicada correctamente

# 6. Cuando está listo para calidad
git checkout release/v1.0.0
git pull origin release/v1.0.0
git merge develop
git push origin release/v1.0.0

# 7. En servidor de calidad
docker exec -it inventario_qa python manage.py migrate
# ✓ Migración aplicada correctamente

# 8. Cuando pasa QA, merge a producción
git checkout main
git pull origin main
git merge release/v1.0.0
git push origin main

# 9. En servidor de producción
docker exec -it inventario_dev_2 python manage.py migrate
# ✓ Migración aplicada correctamente
```

### 9. Monitoreo y Auditoría

#### Verificar estado de migraciones

```bash
# Ver migraciones pendientes
docker exec -it inventario_dev python manage.py showmigrations

# Ver migraciones aplicadas
docker exec -it inventario_dev python manage.py showmigrations --list

# Ver SQL que se ejecutará
docker exec -it inventario_dev python manage.py sqlmigrate inventario 0045
```

#### Crear log de migraciones

```bash
# Guardar historial de migraciones
docker exec -it inventario_dev python manage.py showmigrations > migraciones_$(date +%Y%m%d_%H%M%S).log
```

### 10. Recuperación de Errores

#### Si una migración falla en producción

```bash
# 1. Revertir la migración
docker exec -it inventario_dev_2 python manage.py migrate inventario 0044

# 2. Investigar el error
# ... revisar logs ...

# 3. Crear nueva migración corregida
python manage.py makemigrations
# Genera: 0046_fix_logpropuesta.py

# 4. Probar localmente
python manage.py migrate

# 5. Hacer push y deploy nuevamente
git add inventario/migrations/0046_fix_logpropuesta.py
git commit -m "Corregir migración LogPropuesta"
git push origin main
```

## Resumen

| Aspecto | Regla |
|--------|-------|
| **Dónde crear migraciones** | Solo en rama `develop` |
| **Numeración** | Secuencial global (0045, 0046, 0047...) |
| **Conflictos** | Resolver con `makemigrations --merge` |
| **Flujo** | develop → release → main |
| **Pruebas** | Siempre probar localmente antes de push |
| **Documentación** | Comentar migraciones complejas |
| **Sincronización** | `git pull` antes de empezar trabajo |

## Herramientas Útiles

```bash
# Verificar estado de migraciones
python manage.py showmigrations

# Crear migración de merge
python manage.py makemigrations --merge

# Revertir a migración anterior
python manage.py migrate inventario 0044

# Ver SQL de migración
python manage.py sqlmigrate inventario 0045

# Validar estado de BD
python manage.py check
```

## Referencias

- [Django Migrations Documentation](https://docs.djangoproject.com/en/4.2/topics/migrations/)
- [Git Branching Model](https://nvie.com/posts/a-successful-git-branching-model/)
- [Semantic Versioning](https://semver.org/)
