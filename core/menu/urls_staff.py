from django.urls import path
from . import views_staff

app_name = 'staff'

urlpatterns = [
    path('login/', views_staff.staff_login, name='login'),
    path('logout/', views_staff.staff_logout, name='logout'),
    path('dashboard/', views_staff.dashboard, name='dashboard'),
    path('bills/', views_staff.bills_list, name='bills_list'),
    path('api/orders/check/', views_staff.check_new_orders, name='check_new_orders'),
    path('api/bill/<uuid:order_uuid>/handled/', views_staff.mark_bill_handled, name='mark_bill_handled'),
    path('profile/', views_staff.profile, name='profile'),
    path('finance/', views_staff.finance, name='finance'),
    path('finance/export/pdf/', views_staff.export_finance_pdf, name='export_finance_pdf'),
    path('finance/export/excel/', views_staff.export_finance_excel, name='export_finance_excel'),
    path('finance/export/word/', views_staff.export_finance_word, name='export_finance_word'),
    path('orders/', views_staff.orders_list, name='orders_list'),
    path('orders/<uuid:order_uuid>/', views_staff.order_detail, name='order_detail'),
    path('orders/<uuid:order_uuid>/status/', views_staff.update_order_status, name='update_order_status'),
    path('tables/', views_staff.tables_list, name='tables_list'),
    path('tables/<uuid:table_uuid>/toggle/', views_staff.toggle_table_occupied, name='toggle_table_occupied'),
    path('tables/<uuid:table_uuid>/clear/', views_staff.clear_table, name='clear_table'),
    path('menu/', views_staff.menu_items, name='menu_items'),
    path('menu/ajouter/', views_staff.add_menu_item, name='add_menu_item'),
    path('menu/item/<int:item_id>/toggle/', views_staff.toggle_menu_item_availability, name='toggle_menu_item'),
    path('menu/item/<int:item_id>/delete/', views_staff.delete_menu_item, name='delete_menu_item'),
    path('menu/item/bulk-delete/', views_staff.bulk_delete_menu_items, name='bulk_delete_menu_items'),
    path('menu/item/bulk-toggle/', views_staff.bulk_toggle_menu_items, name='bulk_toggle_menu_items'),
    path('menu/item/edit/', views_staff.edit_menu_item, name='edit_menu_item'),
    path('menu/categorie/ajouter/', views_staff.add_category, name='add_category'),
]
