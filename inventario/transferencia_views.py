"""Vistas para entradas por transferencia."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.urls import reverse
from django.views.decorators.http import require_GET

from .llegada_views import EPA_ENCARGADA_AREA_ENTRADAS, EPA_ENCARGADA_OFICINA_INSUMOS
from .transferencia_forms import TransferenciaEntradaForm, ItemTransferenciaEntradaFormSet
from .transferencia_models import TransferenciaEntrada
from .transferencia_services import asignar_transferencia_a_staging


class ListaTransferenciasView(LoginRequiredMixin, View):
    def get(self, request):
        q = (request.GET.get('q') or '').strip()
        estado = (request.GET.get('estado') or '').strip()
        transferencias = TransferenciaEntrada.objects.select_related(
            'almacen_destino', 'creado_por'
        ).prefetch_related('items')
        if q:
            transferencias = transferencias.filter(
                Q(folio__icontains=q)
                | Q(remision__icontains=q)
                | Q(entidad_origen__icontains=q)
            )
        if estado:
            transferencias = transferencias.filter(estado=estado)
        return render(
            request,
            'inventario/transferencias/lista.html',
            {
                'transferencias': transferencias[:200],
                'q': q,
                'estado': estado,
                'estados': TransferenciaEntrada.ESTADO_CHOICES,
            },
        )


class CrearTransferenciaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'inventario.add_transferenciaentrada'

    def get(self, request):
        form = TransferenciaEntradaForm()
        formset = ItemTransferenciaEntradaFormSet(prefix='items')
        return render(
            request,
            'inventario/transferencias/crear.html',
            {
                'form': form,
                'formset': formset,
                'cancel_url': reverse('logistica:transferencias:lista_transferencias'),
            },
        )

    def post(self, request):
        form = TransferenciaEntradaForm(request.POST)
        formset = ItemTransferenciaEntradaFormSet(request.POST, prefix='items')
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                transferencia = form.save(commit=False)
                transferencia.creado_por = request.user
                transferencia.save()
                formset.instance = transferencia
                formset.save()
                total = transferencia.items.aggregate(t=Sum('cantidad_recibida'))['t'] or 0
                if not transferencia.numero_piezas_recibidas:
                    transferencia.numero_piezas_recibidas = total
                    transferencia.save(update_fields=['numero_piezas_recibidas'])
            messages.success(request, f'Transferencia {transferencia.folio} registrada.')
            return redirect('logistica:transferencias:detalle_transferencia', pk=transferencia.pk)
        return render(
            request,
            'inventario/transferencias/crear.html',
            {
                'form': form,
                'formset': formset,
                'cancel_url': reverse('logistica:transferencias:lista_transferencias'),
            },
        )


class DetalleTransferenciaView(LoginRequiredMixin, View):
    def get(self, request, pk):
        transferencia = get_object_or_404(
            TransferenciaEntrada.objects.select_related('almacen_destino', 'creado_por', 'usuario_aprobacion'),
            pk=pk,
        )
        items = transferencia.items.select_related('producto').all()
        total_piezas = items.aggregate(t=Sum('cantidad_recibida'))['t'] or 0
        return render(
            request,
            'inventario/transferencias/detalle.html',
            {
                'transferencia': transferencia,
                'items': items,
                'total_piezas': total_piezas,
            },
        )


class EditarTransferenciaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'inventario.change_transferenciaentrada'

    def get(self, request, pk):
        transferencia = get_object_or_404(TransferenciaEntrada, pk=pk)
        if not transferencia.puede_editar():
            messages.error(request, 'Solo se pueden editar transferencias en recepción.')
            return redirect('logistica:transferencias:detalle_transferencia', pk=pk)
        form = TransferenciaEntradaForm(instance=transferencia)
        formset = ItemTransferenciaEntradaFormSet(instance=transferencia, prefix='items')
        return render(
            request,
            'inventario/transferencias/crear.html',
            {
                'form': form,
                'formset': formset,
                'transferencia': transferencia,
                'page_title': f'Editar transferencia {transferencia.folio}',
                'cancel_url': reverse('logistica:transferencias:detalle_transferencia', kwargs={'pk': transferencia.pk}),
            },
        )

    def post(self, request, pk):
        transferencia = get_object_or_404(TransferenciaEntrada, pk=pk)
        if not transferencia.puede_editar():
            messages.error(request, 'Solo se pueden editar transferencias en recepción.')
            return redirect('logistica:transferencias:detalle_transferencia', pk=pk)
        form = TransferenciaEntradaForm(request.POST, instance=transferencia)
        formset = ItemTransferenciaEntradaFormSet(request.POST, instance=transferencia, prefix='items')
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
                total = transferencia.items.aggregate(t=Sum('cantidad_recibida'))['t'] or 0
                if not transferencia.numero_piezas_recibidas:
                    transferencia.numero_piezas_recibidas = total
                    transferencia.save(update_fields=['numero_piezas_recibidas'])
            messages.success(request, f'Transferencia {transferencia.folio} actualizada.')
            return redirect('logistica:transferencias:detalle_transferencia', pk=transferencia.pk)
        return render(
            request,
            'inventario/transferencias/crear.html',
            {
                'form': form,
                'formset': formset,
                'transferencia': transferencia,
                'page_title': f'Editar transferencia {transferencia.folio}',
                'cancel_url': reverse('logistica:transferencias:detalle_transferencia', kwargs={'pk': transferencia.pk}),
            },
        )


class AprobarTransferenciaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'inventario.change_transferenciaentrada'

    def post(self, request, pk):
        transferencia = get_object_or_404(TransferenciaEntrada, pk=pk)
        if not transferencia.puede_aprobar():
            messages.error(request, 'La transferencia no puede aprobarse en su estado actual.')
            return redirect('logistica:transferencias:detalle_transferencia', pk=pk)

        ok, result = asignar_transferencia_a_staging(transferencia, request.user)
        if ok:
            messages.success(
                request,
                f'Transferencia {transferencia.folio} aprobada. Existencias asignadas a staging.',
            )
            for aviso in result[:5]:
                messages.info(request, aviso)
        else:
            transferencia.estado = 'UBICACION'
            transferencia.save(update_fields=['estado'])
            messages.warning(request, result)
        return redirect('logistica:transferencias:detalle_transferencia', pk=transferencia.pk)


class ImprimirEPATransferenciaView(LoginRequiredMixin, View):
    def get(self, request, pk):
        transferencia = get_object_or_404(TransferenciaEntrada, pk=pk)
        if transferencia.estado not in ('APROBADA', 'UBICACION'):
            messages.error(request, 'Solo se puede imprimir EPA de transferencias aprobadas.')
            return redirect('logistica:transferencias:detalle_transferencia', pk=pk)
        items = transferencia.items.select_related('producto').all()
        total_items = items.aggregate(t=Sum('cantidad_recibida'))['t'] or 0
        return render(
            request,
            'inventario/transferencias/imprimir_epa.html',
            {
                'transferencia': transferencia,
                'items': items,
                'total_items': total_items,
                'nombre_titular_entrada': EPA_ENCARGADA_AREA_ENTRADAS,
                'nombre_encargada_insumos': EPA_ENCARGADA_OFICINA_INSUMOS,
            },
        )


@require_GET
def api_buscar_clave_producto(request):
    """Autocomplete de claves CNIS para captura de ítems."""
    from .models import Producto

    term = (request.GET.get('q') or '').strip()
    if len(term) < 2:
        return JsonResponse([], safe=False)
    productos = (
        Producto.objects.filter(Q(clave_cnis__icontains=term) | Q(descripcion__icontains=term))
        .order_by('clave_cnis')[:20]
    )
    data = [
        {
            'clave_cnis': p.clave_cnis,
            'descripcion': p.descripcion,
            'id': p.id,
        }
        for p in productos
    ]
    return JsonResponse(data, safe=False)
