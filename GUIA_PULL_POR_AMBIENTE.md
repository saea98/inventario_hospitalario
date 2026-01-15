# Guía: Secuencia de Pull por Ambiente

## Flujo General

```
Yo (Desarrollador)
  ↓ (git push origin develop)
GitHub (develop)
  ↓ (git pull)
Tu máquina (DESARROLLO)
  ↓ (cuando está listo)
  ↓ (git push origin release/v1.0.0)
GitHub (release/v1.0.0)
  ↓ (git pull)
Tu máquina (CALIDAD)
  ↓ (cuando pasa QA)
  ↓ (git push origin main)
GitHub (main)
  ↓ (git pull)
Tu máquina (PRODUCCIÓN)
```

## Escenario: Liberar cambios de Desarrollo → Calidad → Producción

### PASO 1: Yo hago push a develop (desde mi máquina)

```bash
# En mi máquina (desarrollo local)
cd ~/inventario_hospitalario
git checkout develop
git add -A
git commit -m "Cambios finales de la funcionalidad"
git push origin develop
```

**Resultado en GitHub**: `develop` branch actualizado

---

### PASO 2: Tú haces pull en DESARROLLO

```bash
# En servidor de DESARROLLO
cd ~/inventario/inventario_hospitalario

# 1. Asegurarse de estar en develop
git checkout develop

# 2. Sincronizar con GitHub
git pull origin develop

# 3. Aplicar migraciones si hay
docker exec -it inventario_dev python manage.py migrate

# 4. Reiniciar contenedor
docker-compose restart web

# 5. Verificar que todo está bien
docker exec -it inventario_dev python manage.py check
```

**Resultado**: Servidor de DESARROLLO actualizado con los cambios

---

### PASO 3: Tú haces push a release (desde DESARROLLO)

```bash
# En servidor de DESARROLLO
cd ~/inventario/inventario_hospitalario

# 1. Asegurarse de estar en develop
git checkout develop

# 2. Verificar que todo está sincronizado
git pull origin develop

# 3. Cambiar a rama release
git checkout release/v1.0.0

# 4. Hacer merge desde develop
git merge develop

# 5. Hacer push a GitHub
git push origin release/v1.0.0
```

**Resultado en GitHub**: `release/v1.0.0` branch actualizado con cambios de develop

---

### PASO 4: Tú haces pull en CALIDAD

```bash
# En servidor de CALIDAD
cd ~/inventario/inventario_hospitalario

# 1. Asegurarse de estar en release
git checkout release/v1.0.0

# 2. Sincronizar con GitHub
git pull origin release/v1.0.0

# 3. Aplicar migraciones si hay
docker exec -it inventario_qa python manage.py migrate

# 4. Reiniciar contenedor
docker-compose restart web

# 5. Verificar que todo está bien
docker exec -it inventario_qa python manage.py check
```

**Resultado**: Servidor de CALIDAD actualizado con los cambios

---

### PASO 5: Tú haces push a main (desde CALIDAD)

```bash
# En servidor de CALIDAD
cd ~/inventario/inventario_hospitalario

# 1. Asegurarse de estar en release
git checkout release/v1.0.0

# 2. Verificar que todo está sincronizado
git pull origin release/v1.0.0

# 3. Cambiar a rama main
git checkout main

# 4. Hacer merge desde release
git merge release/v1.0.0

# 5. Hacer push a GitHub
git push origin main
```

**Resultado en GitHub**: `main` branch actualizado con cambios de release

---

### PASO 6: Tú haces pull en PRODUCCIÓN

```bash
# En servidor de PRODUCCIÓN
cd ~/inventario/inventario_hospitalario

# 1. Asegurarse de estar en main
git checkout main

# 2. Sincronizar con GitHub
git pull origin main

# 3. Aplicar migraciones si hay
docker exec -it inventario_dev_2 python manage.py migrate

# 4. Reiniciar contenedor
docker-compose restart web

# 5. Verificar que todo está bien
docker exec -it inventario_dev_2 python manage.py check
```

**Resultado**: Servidor de PRODUCCIÓN actualizado con los cambios

---

## Resumen de Comandos por Ambiente

### DESARROLLO

```bash
# Pull
cd ~/inventario/inventario_hospitalario
git checkout develop
git pull origin develop
docker exec -it inventario_dev python manage.py migrate
docker-compose restart web

# Push (cuando listo para calidad)
git checkout develop
git pull origin develop
git checkout release/v1.0.0
git merge develop
git push origin release/v1.0.0
```

### CALIDAD

```bash
# Pull
cd ~/inventario/inventario_hospitalario
git checkout release/v1.0.0
git pull origin release/v1.0.0
docker exec -it inventario_qa python manage.py migrate
docker-compose restart web

# Push (cuando pasa QA)
git checkout release/v1.0.0
git pull origin release/v1.0.0
git checkout main
git merge release/v1.0.0
git push origin main
```

### PRODUCCIÓN

```bash
# Pull
cd ~/inventario/inventario_hospitalario
git checkout main
git pull origin main
docker exec -it inventario_dev_2 python manage.py migrate
docker-compose restart web
```

---

## Scripts Automatizados

### Script para DESARROLLO: `deploy-dev.sh`

```bash
#!/bin/bash
set -e

echo "=== DEPLOY DESARROLLO ==="
cd ~/inventario/inventario_hospitalario

echo "1. Checkout develop..."
git checkout develop

echo "2. Pull desde GitHub..."
git pull origin develop

echo "3. Aplicar migraciones..."
docker exec -it inventario_dev python manage.py migrate

echo "4. Reiniciar contenedor..."
docker-compose restart web

echo "5. Verificar estado..."
docker exec -it inventario_dev python manage.py check

echo "✓ DESARROLLO actualizado correctamente"
```

### Script para CALIDAD: `deploy-qa.sh`

```bash
#!/bin/bash
set -e

echo "=== DEPLOY CALIDAD ==="
cd ~/inventario/inventario_hospitalario

echo "1. Checkout release..."
git checkout release/v1.0.0

echo "2. Pull desde GitHub..."
git pull origin release/v1.0.0

echo "3. Aplicar migraciones..."
docker exec -it inventario_qa python manage.py migrate

echo "4. Reiniciar contenedor..."
docker-compose restart web

echo "5. Verificar estado..."
docker exec -it inventario_qa python manage.py check

echo "✓ CALIDAD actualizado correctamente"
```

### Script para PRODUCCIÓN: `deploy-prod.sh`

```bash
#!/bin/bash
set -e

echo "=== DEPLOY PRODUCCIÓN ==="
cd ~/inventario/inventario_hospitalario

echo "1. Checkout main..."
git checkout main

echo "2. Pull desde GitHub..."
git pull origin main

echo "3. Aplicar migraciones..."
docker exec -it inventario_dev_2 python manage.py migrate

echo "4. Reiniciar contenedor..."
docker-compose restart web

echo "5. Verificar estado..."
docker exec -it inventario_dev_2 python manage.py check

echo "✓ PRODUCCIÓN actualizado correctamente"
```

**Uso:**
```bash
chmod +x deploy-dev.sh
./deploy-dev.sh

chmod +x deploy-qa.sh
./deploy-qa.sh

chmod +x deploy-prod.sh
./deploy-prod.sh
```

---

## Checklist de Deployment

### Antes de hacer Pull

- [ ] ¿Estoy en la rama correcta? (develop, release, o main)
- [ ] ¿He hecho backup de la BD? (opcional pero recomendado)
- [ ] ¿Hay usuarios usando el sistema? (considerar downtime)
- [ ] ¿He leído los cambios en GitHub?

### Durante el Pull

- [ ] `git pull` completó sin errores
- [ ] `python manage.py migrate` completó sin errores
- [ ] `docker-compose restart` completó sin errores
- [ ] `python manage.py check` sin errores críticos

### Después del Pull

- [ ] ¿El sistema está respondiendo? (http://localhost:8700/)
- [ ] ¿Las funcionalidades nuevas funcionan?
- [ ] ¿No hay errores en los logs?
- [ ] ¿Las migraciones se aplicaron correctamente?

---

## Casos Especiales

### Caso 1: Hay conflictos en el merge

```bash
# Si hay conflicto al hacer merge
git merge release/v1.0.0
# ❌ CONFLICT (content): Merge conflict in archivo.py

# 1. Ver los conflictos
git status

# 2. Resolver conflictos manualmente
# ... editar archivo.py ...

# 3. Marcar como resuelto
git add archivo.py

# 4. Completar merge
git commit -m "Resolver conflicto de merge"

# 5. Hacer push
git push origin main
```

### Caso 2: Necesito revertir un cambio

```bash
# Ver historial
git log --oneline -10

# Revertir último commit
git revert HEAD

# O revertir a un commit específico
git revert abc1234

# Hacer push
git push origin main
```

### Caso 3: Hay migraciones pendientes

```bash
# Ver migraciones pendientes
docker exec -it inventario_dev python manage.py showmigrations

# Ver migraciones aplicadas
docker exec -it inventario_dev python manage.py showmigrations --list

# Si falla una migración, revertir
docker exec -it inventario_dev python manage.py migrate inventario 0044

# Luego investigar y corregir
```

---

## Monitoreo Post-Deployment

### Verificar logs

```bash
# Ver logs del contenedor
docker logs -f inventario_dev

# Ver últimas 100 líneas
docker logs --tail 100 inventario_dev

# Ver logs de una hora atrás
docker logs --since 1h inventario_dev
```

### Verificar BD

```bash
# Conectar a la BD
docker exec -it inventario_dev psql -U postgres -d inventario_hospitalario

# Ver migraciones aplicadas
SELECT * FROM django_migrations ORDER BY id DESC LIMIT 10;

# Salir
\q
```

---

## Resumen Visual

```
┌─────────────────────────────────────────────────────────────┐
│ YO (Desarrollador Local)                                    │
│ git push origin develop                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ GITHUB                                                      │
│ develop | release/v1.0.0 | main                            │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ DEVELOP │  │ CALIDAD │  │ PROD    │
   │ (pull)  │  │ (pull)  │  │ (pull)  │
   └────┬────┘  └────┬────┘  └────┬────┘
        │            │            │
        │ (push)     │ (push)     │
        ▼            ▼            ▼
   release/v1.0.0  main
```

---

## Preguntas Frecuentes

**P: ¿Puedo hacer pull directamente a main?**
R: No. Siempre debe pasar por develop → release → main para mantener control de calidad.

**P: ¿Qué pasa si hay conflictos?**
R: Git los detectará. Debes resolverlos manualmente antes de hacer push.

**P: ¿Puedo hacer rollback?**
R: Sí, con `git revert` o `git reset`, pero es mejor evitarlo con buenas prácticas.

**P: ¿Cuánto tiempo tarda una migración?**
R: Depende del tamaño de la BD. Puede ser desde segundos hasta minutos.

**P: ¿Necesito downtime?**
R: Generalmente no, pero es recomendable hacer deployments en horarios de bajo uso.

---

## Próximos Pasos

1. Crear los scripts de deployment
2. Configurar permisos de acceso a ramas
3. Implementar notificaciones de deployment
4. Crear runbook de rollback
5. Documentar SLA de deployments
