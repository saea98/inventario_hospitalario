from django.urls import path
from . import sql_views

urlpatterns = [
    path("execute-sql/", sql_views.execute_raw_sql, name="execute_raw_sql"),
]
