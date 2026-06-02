from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('<uuid:table_uuid>/', views.menu, name='menu'),
    path('<uuid:table_uuid>/commander/', views.create_order, name='create_order'),
    path('<uuid:table_uuid>/commande/<uuid:order_uuid>/', views.order_detail, name='order_detail'),
    path('<uuid:table_uuid>/commande/<uuid:order_uuid>/status/', views.order_status, name='order_status'),
    path('<uuid:table_uuid>/commande/<uuid:order_uuid>/facture/', views.order_invoice_pdf, name='order_invoice'),
    path('<uuid:table_uuid>/commande/<uuid:order_uuid>/annuler/', views.cancel_order, name='cancel_order'),
    path('<uuid:table_uuid>/commande/<uuid:order_uuid>/addition/', views.request_bill, name='request_bill'),
    path('<uuid:table_uuid>/liberer/', views.free_table, name='free_table'),
    path('api/update-currency/', views.update_currency, name='update_currency'),
]
