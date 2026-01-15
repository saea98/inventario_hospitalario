from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import connection
from django.contrib import messages
from .sql_forms import RawSQLForm

@login_required
@user_passes_test(lambda u: u.is_superuser)
def execute_raw_sql(request):
    """
    Vista para ejecutar consultas SQL directamente en la base de datos.
    Solo accesible para superusuarios.
    """
    form = RawSQLForm()
    results = None
    columns = None
    error = None
    
    if request.method == 'POST':
        form = RawSQLForm(request.POST)
        if form.is_valid():
            sql_query = form.cleaned_data['sql_query']
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql_query)
                    if cursor.description:
                        columns = [col[0] for col in cursor.description]
                        results = cursor.fetchall()
                        messages.success(request, f"✅ Consulta ejecutada correctamente. {len(results)} filas devueltas.")
                    else:
                        messages.success(request, "✅ Comando ejecutado correctamente (sin resultados).")
            except Exception as e:
                error = str(e)
                messages.error(request, f"❌ Error al ejecutar la consulta: {error}")
    
    context = {
        'form': form,
        'results': results,
        'columns': columns,
        'error': error,
    }
    return render(request, 'inventario/sql_interface.html', context)
