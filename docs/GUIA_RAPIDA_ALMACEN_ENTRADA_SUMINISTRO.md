# Guía rápida de almacén — Entrada a suministro

**Una página · Capacitación · Imprimir y colgar en almacén**

Sistema de Inventario Hospitalario · Flujo FEFO

---

## Los 8 pasos (orden obligatorio)

| Paso | Icono | Qué hacer | Estado / resultado |
|:----:|:-----:|-----------|-------------------|
| **1** | 📅 | **Cita:** programar entrega y **autorizar** antes de que llegue el proveedor | Cita **AUTORIZADA** |
| **2** | 🚚 | **Llegada:** registrar recepción (remisión, piezas, lote, caducidad) | EN_RECEPCION |
| **3** | 🔬 | **Calidad** → **Facturación** → **Supervisión** | Avanza por etapas |
| **4** | 📍 | **Ubicación en sistema** + **colocar en rack** (ver regla FEFO abajo) | Llegada **APROBADA** · Lote creado |
| **5** | 📋 | **Pedido:** institución solicita · almacén **valida** cantidades | Solicitud **VALIDADA** |
| **6** | 🤖 | **Propuesta:** sistema asigna lote/ubicación (caducidad primero) · **revisar/aprobar** | **REVISADA** |
| **7** | 🛒 | **Picking:** imprimir hoja · recorrer ubicaciones · recoger | Recolección física |
| **8** | ✅ | **Surtir:** confirmar en sistema | **SURTIDA** · salida de inventario |

---

## Regla de oro: FEFO en el rack

> **Primero sale lo que caduca antes.** El sistema propone en ese orden; el rack debe ayudar.

| Mercancía | Dónde ponerla en el rack | Icono |
|-----------|--------------------------|:-----:|
| **Ya estaba en almacén** (caduca antes) | **Al frente · a la mano · nivel bajo** | 👇🟢 |
| **Entrada nueva de hoy** (proveedor) | **Arriba del rack · o al fondo del pasillo** | ⬆️🔵 |
| **Al surtir** | Seguir **hoja de picking / propuesta** | 📄✅ |

```
   RACK (vista lateral)

   ⬆️  Entrada NUEVA  ─────────  (arriba o atrás)
   │
   │  Existencia VIEJA ───────  (frente / abajo = sale primero)
   │
   └── Suelo / pasillo de picking
```

**Si la ubicación en sistema no coincide con el rack → la propuesta fallará o surtirán mal.**

---

## Quién hace qué (por rol)

| Rol | Icono | Responsabilidad |
|-----|:-----:|-----------------|
| **Planificador / compras** | 📅 | Crear cita de proveedor |
| **Jefe de almacén** | ✔️ | Autorizar cita · supervisar |
| **Almacenero recepción** | 🚚 | Registrar llegada e ítems |
| **Calidad** | 🔬 | Aprobar o rechazar producto |
| **Facturación** | 💰 | Capturar factura y precios |
| **Supervisor** | 👁️ | Validar documentación |
| **Encargado ubicación** | 📍 | Ubicación en sistema + orden en rack (FEFO) |
| **Validador pedidos** | 📋 | Aprobar cantidades del pedido |
| **Almacenero surtido** | 🛒 | Revisar propuesta · picking · surtir |

---

## Checklist diario — Recepción (pasos 1–4)

- [ ] ¿La cita está **AUTORIZADA** antes de recibir al proveedor?
- [ ] ¿Remisión, lote y **fecha de caducidad** capturados en cada ítem?
- [ ] ¿Pasó **calidad**, **facturación** y **supervisión**?
- [ ] ¿Ubicación registrada en sistema = lugar real en rack?
- [ ] ¿Mercancía vieja al **frente/abajo** y entrada nueva **arriba/atrás**?

---

## Checklist diario — Suministro (pasos 5–8)

- [ ] ¿Pedido **validado** antes de generar propuesta?
- [ ] ¿Propuesta **revisada/aprobada** (REVISADA) antes de salir a piso?
- [ ] ¿Hoja de picking impresa o en pantalla?
- [ ] ¿Se recogió en el **orden de la propuesta** (caducidad / ubicación)?
- [ ] ¿Se confirmó **Surtir** en sistema al terminar?

---

## Errores frecuentes (evitar)

| ❌ Error | ✅ Correcto |
|---------|-------------|
| Recibir sin cita autorizada | Autorizar cita primero |
| Mezclar lote nuevo delante del viejo | FEFO: viejo al frente, nuevo arriba/atrás |
| Surtir sin revisar propuesta | Revisar → picking → surtir |
| Ubicación en sistema ≠ rack real | Verificar al guardar ubicación |
| No surtir en sistema tras entregar | Siempre confirmar **Surtir** |

---

## Orden del sistema al proponer (referencia)

Por cada **clave CNIS**:

1. **Caducidad** (la más próxima primero)  
2. **Número de lote**  
3. **Código de ubicación**

Solo lotes **disponibles** con caducidad vigente (regla del sistema, p. ej. ≥ 60 días).

---

## Contacto / escalamiento

| Situación | Acción |
|-----------|--------|
| Producto rechazado en calidad | No ubicar · seguir flujo de rechazo |
| Cantidad distinta a remisión | Registrar en observaciones · supervisor |
| Propuesta sin existencia | Reporte productos no disponibles · validador |
| Duda de ubicación | Encargado de almacén antes de APROBAR llegada |

---

**Documento completo con diagramas:** `docs/DIAGRAMA_FLUJO_ENTRADA_SUMINISTRO.md`  
**Manuales:** `MANUAL_CITAS_PROVEEDORES.md` · `MANUAL_LLEGADA_PROVEEDORES.md` · `MANUAL_PEDIDOS.md`

*Imprimir en tamaño carta u oficio · Revisar trimestralmente*
