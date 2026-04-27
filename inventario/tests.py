from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import (
    Almacen,
    CategoriaProducto,
    Institucion,
    Lote,
    LoteUbicacion,
    Producto,
    TipoInstitucion,
    UbicacionAlmacen,
)
from .pedidos_models import ItemSolicitud, LoteAsignado, SolicitudPedido
from .propuesta_generator import PropuestaGenerator
from .propuesta_utils import (
    cantidad_existencia_fisica_lote_como_reporte_existencias,
    completar_surtimiento_propuesta,
    totales_reserva_activa_por_lote_ids,
)


class FlujoPedidosSurtimientoTest(TestCase):
    """
    Pruebas end-to-end del flujo base:
    solicitud validada -> propuesta -> surtimiento -> descuentos de inventario.
    """

    def setUp(self):
        user_model = get_user_model()
        self.usuario = user_model.objects.create_user(
            username="qa_jenkins",
            password="qa_jenkins_123",
        )

        tipo = TipoInstitucion.objects.create(tipo="OTRO", descripcion="Pruebas QA")
        self.institucion = Institucion.objects.create(
            clue="QA001",
            denominacion="Institucion QA",
            tipo_institucion=tipo,
        )
        self.almacen = Almacen.objects.create(
            institucion=self.institucion,
            nombre="Almacen QA",
            codigo="ALM-QA-01",
        )
        self.ubicacion = UbicacionAlmacen.objects.create(
            almacen=self.almacen,
            codigo="A-01",
        )

        categoria = CategoriaProducto.objects.create(nombre="Medicamentos QA")
        self.producto = Producto.objects.create(
            clave_cnis="060.189.0056",
            descripcion="Producto de prueba QA",
            categoria=categoria,
            unidad_medida="PIEZA",
        )

        self.lote = Lote.objects.create(
            numero_lote="QA-LOTE-001",
            producto=self.producto,
            institucion=self.institucion,
            almacen=self.almacen,
            ubicacion=self.ubicacion,
            cantidad_inicial=100,
            cantidad_disponible=100,
            precio_unitario=Decimal("10.00"),
            valor_total=Decimal("1000.00"),
            fecha_fabricacion=date.today() - timedelta(days=30),
            fecha_caducidad=date.today() + timedelta(days=180),
            fecha_recepcion=date.today(),
            estado=1,
            creado_por=self.usuario,
        )
        self.lote_ubicacion = LoteUbicacion.objects.create(
            lote=self.lote,
            ubicacion=self.ubicacion,
            cantidad=100,
            cantidad_reservada=0,
            usuario_asignacion=self.usuario,
        )

    def _crear_solicitud_validada(self, cantidad_aprobada=40):
        solicitud = SolicitudPedido.objects.create(
            institucion_solicitante=self.institucion,
            almacen_destino=self.almacen,
            usuario_solicitante=self.usuario,
            usuario_validacion=self.usuario,
            fecha_entrega_programada=date.today() + timedelta(days=1),
            estado="VALIDADA",
            observaciones_solicitud="PED-QA-0001",
        )
        ItemSolicitud.objects.create(
            solicitud=solicitud,
            producto=self.producto,
            cantidad_solicitada=cantidad_aprobada,
            cantidad_aprobada=cantidad_aprobada,
        )
        return solicitud

    def test_generacion_propuesta_reserva_cantidad_y_neto(self):
        solicitud = self._crear_solicitud_validada(cantidad_aprobada=40)

        propuesta = PropuestaGenerator(solicitud.id, self.usuario).generate()
        asignaciones = LoteAsignado.objects.filter(item_propuesta__propuesta=propuesta)

        self.assertEqual(propuesta.total_solicitado, 40)
        self.assertEqual(propuesta.total_propuesto, 40)
        self.assertEqual(asignaciones.count(), 1)
        self.assertEqual(sum(a.cantidad_asignada for a in asignaciones), 40)

        reservas = totales_reserva_activa_por_lote_ids([self.lote.id])
        reserva_activa = reservas.get(self.lote.id, 0)
        disponible = cantidad_existencia_fisica_lote_como_reporte_existencias(self.lote)
        neto = max(0, disponible - reserva_activa)

        self.assertEqual(reserva_activa, 40)
        self.assertEqual(disponible, 100)
        self.assertEqual(neto, 60)

    def test_completar_surtimiento_descuenta_disponible_y_limpia_reserva(self):
        solicitud = self._crear_solicitud_validada(cantidad_aprobada=40)
        propuesta = PropuestaGenerator(solicitud.id, self.usuario).generate()

        propuesta.estado = "SURTIDA"
        propuesta.save(update_fields=["estado"])
        LoteAsignado.objects.filter(item_propuesta__propuesta=propuesta).update(surtido=True)

        resultado = completar_surtimiento_propuesta(propuesta.id)

        self.assertTrue(resultado["exito"])

        self.lote.refresh_from_db()
        self.lote_ubicacion.refresh_from_db()

        self.assertEqual(self.lote.cantidad_disponible, 60)
        self.assertEqual(self.lote.cantidad_reservada, 0)
        self.assertEqual(self.lote_ubicacion.cantidad, 60)
        self.assertEqual(self.lote_ubicacion.cantidad_reservada, 0)

        reservas = totales_reserva_activa_por_lote_ids([self.lote.id])
        self.assertEqual(reservas.get(self.lote.id, 0), 0)
