import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Restaurant, Table, Order, OrderItem, Category, MenuItem
from .forms import RestaurantProfileForm
from .forms_staff import MenuItemForm


def staff_login(request):
    """Page de connexion pour le staff du restaurant"""
    if request.user.is_authenticated:
        return redirect('staff:dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Vérifier que l'utilisateur a les permissions pour un restaurant
            if user.groups.filter(name__in=['Restaurant Staff', 'Restaurant Manager']).exists():
                login(request, user)
                messages.success(request, f'Bienvenue {user.first_name or user.username} !')
                return redirect('staff:dashboard')
            else:
                error = "Vous n'avez pas accès à cette interface."
        else:
            error = "Nom d'utilisateur ou mot de passe incorrect."
    
    return render(request, 'staff/login.html', {'error': error})


def get_restaurant_for_user(user):
    """Récupère le restaurant associé à un utilisateur"""
    # Méthode 1: Via un champ ForeignKey sur User (à implémenter si besoin)
    # if hasattr(user, 'restaurant'):
    #     return user.restaurant
    
    # Méthode 2: Récupérer le premier restaurant actif
    # Pour une vraie implémentation, il faudrait lier user à restaurant
    return Restaurant.objects.filter(is_active=True).first()


def staff_logout(request):
    """Déconnexion du staff"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('staff:login')


@login_required
def dashboard(request):
    """Tableau de bord du restaurant"""
    # Récupérer le restaurant associé à l'utilisateur
    restaurant = get_restaurant_for_user(request.user)

    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:login')

    # Récupérer les tables du restaurant
    tables = Table.objects.filter(restaurant=restaurant, is_active=True).annotate(
        active_orders_count=Count('orders', filter=Q(orders__status__in=['pending', 'confirmed', 'preparing', 'ready']))
    ).order_by('name')

    # Récupérer les commandes en cours
    active_orders = Order.objects.filter(
        table__restaurant=restaurant,
        table__is_active=True,
        status__in=['pending', 'confirmed', 'preparing', 'ready']
    ).select_related('table').order_by('-created_at')

    # Calculer les revenus
    today = timezone.now().date()
    today_orders = Order.objects.filter(
        table__restaurant=restaurant,
        created_at__date=today,
        status__in=['confirmed', 'preparing', 'ready', 'served']
    )
    daily_revenue = today_orders.aggregate(total=Sum('total_price'))['total'] or 0

    # Revenus de la semaine
    week_ago = today - timedelta(days=7)
    week_orders = Order.objects.filter(
        table__restaurant=restaurant,
        created_at__date__gte=week_ago,
        status__in=['confirmed', 'preparing', 'ready', 'served']
    )
    weekly_revenue = week_orders.aggregate(total=Sum('total_price'))['total'] or 0

    # Revenus du mois
    month_ago = today - timedelta(days=30)
    month_orders = Order.objects.filter(
        table__restaurant=restaurant,
        created_at__date__gte=month_ago,
        status__in=['confirmed', 'preparing', 'ready', 'served']
    )
    monthly_revenue = month_orders.aggregate(total=Sum('total_price'))['total'] or 0

    # Total des commandes servies
    total_served = Order.objects.filter(
        table__restaurant=restaurant,
        status='served'
    ).count()

    # Récupérer les annonces actives
    from .models import Announcement
    active_announcements = Announcement.objects.filter(
        is_active=True
    ).exclude(
        start_date__gt=timezone.now()
    ).exclude(
        end_date__lt=timezone.now()
    ).order_by('-priority', '-created_at')
    
    # Compter les nouvelles annonces (créées dans les 7 derniers jours)
    recent_announcements = active_announcements.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()

    # Compter les demandes d'addition en attente
    pending_bills = Order.objects.filter(
        table__restaurant=restaurant,
        bill_requested=True
    ).count()

    # Statistiques
    stats = {
        'total_tables': tables.count(),
        'occupied_tables': tables.filter(
            Q(active_orders_count__gt=0) | Q(is_occupied=True)
        ).count(),
        'active_orders': active_orders.count(),
        'pending_orders': active_orders.filter(status='pending').count(),
        'daily_revenue': daily_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'total_served': total_served,
        'active_announcements': active_announcements.count(),
        'recent_announcements': recent_announcements,
    }

    context = {
        'restaurant': restaurant,
        'tables': tables,
        'active_orders': active_orders,
        'stats': stats,
        'active_announcements': active_announcements,
        'recent_announcements': recent_announcements,
        'pending_bills': pending_bills,
    }
    return render(request, 'staff/dashboard.html', context)


@login_required
def check_new_orders(request):
    """API pour vérifier les nouvelles commandes et demandes d'addition (polling temps réel)"""
    restaurant = get_restaurant_for_user(request.user)
    
    if not restaurant:
        return JsonResponse({'success': False, 'error': 'No restaurant'})
    
    # Récupérer l'ID de la dernière commande vue (passé en paramètre)
    last_order_id = request.GET.get('last_order_id', 0)
    last_bill_check = request.GET.get('last_bill_check', '')
    
    response_data = {
        'success': True,
        'has_new_orders': False,
        'has_bill_requests': False,
        'new_orders_count': 0,
        'orders': [],
        'bill_requests': [],
    }
    
    # Vérifier les nouvelles commandes
    new_orders = Order.objects.filter(
        table__restaurant=restaurant,
        status__in=['pending', 'confirmed', 'preparing', 'ready']
    ).exclude(
        id__lte=last_order_id
    ).select_related('table').prefetch_related('items__menu_item').order_by('-created_at')
    
    if new_orders.exists():
        orders_data = []
        for order in new_orders:
            items_list = []
            for item in order.items.all():
                items_list.append({
                    'name': item.menu_item.name if item.menu_item else 'Item supprimé',
                    'quantity': item.quantity,
                })
            
            orders_data.append({
                'id': order.id,
                'uuid': str(order.uuid)[:8],
                'table_name': order.table.name,
                'table_color': order.table.color,
                'status': order.status,
                'status_display': order.get_status_display(),
                'total': str(order.total_price),
                'items_count': order.items.count(),
                'items_list': items_list,
                'created_at': order.created_at.strftime('%d/%m %H:%M'),
            })
        
        response_data['has_new_orders'] = True
        response_data['new_orders_count'] = new_orders.count()
        response_data['orders'] = orders_data
    
    # Vérifier les nouvelles demandes d'addition
    bill_requests = Order.objects.filter(
        table__restaurant=restaurant,
        bill_requested=True,
        bill_requested_at__isnull=False
    ).select_related('table')
    
    if bill_requests.exists():
        bill_data = []
        for order in bill_requests:
            bill_data.append({
                'id': order.id,
                'table_name': order.table.name,
                'requested_at': order.bill_requested_at.strftime('%d/%m %H:%M'),
            })
        
        response_data['has_bill_requests'] = True
        response_data['bill_requests'] = bill_data
    
    return JsonResponse(response_data)


@login_required
@require_POST
def mark_bill_handled(request, order_uuid):
    """Marquer une demande d'addition comme traitée"""
    from .models import Order
    order = get_object_or_404(Order, uuid=order_uuid)
    order.bill_requested = False
    order.bill_requested_at = None
    order.save()
    return JsonResponse({'success': True})


@login_required
def bills_list(request):
    """Liste des demandes d'addition en attente"""
    restaurant = get_restaurant_for_user(request.user)

    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:login')

    # Récupérer toutes les commandes avec demande d'addition
    bill_requests = Order.objects.filter(
        table__restaurant=restaurant,
        bill_requested=True
    ).select_related('table').order_by('-bill_requested_at')

    # Compter les demandes d'addition en attente pour le badge
    pending_bills = bill_requests.count()
    
    # Compter les tables occupées
    occupied_tables = restaurant.tables.filter(is_occupied=True).count()

    context = {
        'restaurant': restaurant,
        'bill_requests': bill_requests,
        'pending_bills': pending_bills,
        'occupied_tables': occupied_tables,
    }

    return render(request, 'staff/bills_list.html', context)


@login_required
def orders_list(request):
    """Liste de toutes les commandes"""
    restaurant = get_restaurant_for_user(request.user)
    
    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:login')
    
    # Filtres
    status_filter = request.GET.get('status', 'all')
    table_filter = request.GET.get('table', 'all')
    
    orders = Order.objects.filter(table__restaurant=restaurant).select_related('table').order_by('-created_at')
    
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    if table_filter != 'all':
        orders = orders.filter(table_id=table_filter)
    
    tables = Table.objects.filter(restaurant=restaurant, is_active=True)
    
    context = {
        'restaurant': restaurant,
        'orders': orders,
        'tables': tables,
        'status_filter': status_filter,
        'table_filter': table_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'staff/orders_list.html', context)


@login_required
def order_detail(request, order_uuid):
    """Détail d'une commande"""
    restaurant = get_restaurant_for_user(request.user)
    
    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:login')
    
    order = get_object_or_404(
        Order.objects.select_related('table').prefetch_related('items__menu_item'),
        uuid=order_uuid,
        table__restaurant=restaurant
    )
    
    context = {
        'restaurant': restaurant,
        'order': order,
    }
    return render(request, 'staff/order_detail.html', context)


@login_required
@require_POST
def update_order_status(request, order_uuid):
    """Mettre à jour le statut d'une commande"""
    restaurant = get_restaurant_for_user(request.user)
    
    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:login')
    
    order = get_object_or_404(
        Order,
        uuid=order_uuid,
        table__restaurant=restaurant
    )
    
    new_status = request.POST.get('status')
    if new_status and new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save()
        
        # Si la commande est servie ou annulée, vérifier si la table peut être libérée
        if new_status in ['served', 'cancelled']:
            has_active_orders = Order.objects.filter(
                table=order.table,
                status__in=['pending', 'confirmed', 'preparing', 'ready']
            ).exists()
            
            if not has_active_orders:
                order.table.is_occupied = False
                order.table.save()
                messages.success(request, f'Statut mis à jour : {order.get_status_display()}. Table libérée.')
            else:
                messages.success(request, f'Statut mis à jour : {order.get_status_display()}')
        else:
            messages.success(request, f'Statut mis à jour : {order.get_status_display()}')
    else:
        messages.error(request, 'Statut invalide.')
    
    return redirect('staff:order_detail', order_uuid=order_uuid)


@login_required
def tables_list(request):
    """Liste des tables avec statut"""
    restaurant = get_restaurant_for_user(request.user)

    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:login')

    tables = Table.objects.filter(
        restaurant=restaurant,
        is_active=True
    ).annotate(
        active_orders_count=Count('orders', filter=Q(orders__status__in=['pending', 'confirmed', 'preparing', 'ready']))
    ).order_by('name')

    # Calculer les statistiques basées sur les commandes actives
    tables_count = tables.count()
    # Une table est occupée si elle a des commandes actives
    occupied_count = 0
    for table in tables:
        if table.active_orders_count > 0 or table.is_occupied:
            occupied_count += 1
    free_count = tables_count - occupied_count

    context = {
        'restaurant': restaurant,
        'tables': tables,
        'tables_count': tables_count,
        'occupied_count': occupied_count,
        'free_count': free_count,
    }
    return render(request, 'staff/tables_list.html', context)


@login_required
@require_POST
def toggle_table_occupied(request, table_uuid):
    """Basculer l'état occupé/libre d'une table"""
    restaurant = get_restaurant_for_user(request.user)
    
    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:login')
    
    table = get_object_or_404(Table, uuid=table_uuid, restaurant=restaurant)
    
    # Vérifier si la table a des commandes actives
    has_active_orders = Order.objects.filter(
        table=table,
        status__in=['pending', 'confirmed', 'preparing', 'ready']
    ).exists()
    
    # Si la table a des commandes actives, on ne peut pas la libérer manuellement
    if has_active_orders and not table.is_occupied:
        messages.warning(request, f'Impossible de libérer la table {table.name} : des commandes sont en cours.')
        return redirect('staff:tables_list')
    
    table.is_occupied = not table.is_occupied
    table.save()
    
    if table.is_occupied:
        messages.success(request, f'Table {table.name} marquée comme occupée.')
    else:
        messages.success(request, f'Table {table.name} libérée.')
    
    return redirect('staff:tables_list')


@login_required
@require_POST
def clear_table(request, table_uuid):
    """Vider une table (marquer comme libre et archiver les commandes)"""
    restaurant = get_restaurant_for_user(request.user)
    
    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:login')
    
    table = get_object_or_404(Table, uuid=table_uuid, restaurant=restaurant)
    
    # Marquer les commandes en cours comme servies
    Order.objects.filter(
        table=table,
        status__in=['pending', 'confirmed', 'preparing', 'ready']
    ).update(status='served')
    
    # Libérer la table
    table.is_occupied = False
    table.save()
    
    messages.success(request, f'Table {table.name} libérée et commandes marquées comme servies.')
    return redirect('staff:tables_list')


def get_restaurant_for_user(user):
    """Récupère le restaurant associé à un utilisateur"""
    # Méthode 1: Via un champ ForeignKey sur User (à implémenter si besoin)
    # if hasattr(user, 'restaurant'):
    #     return user.restaurant

    # Méthode 2: Récupérer le premier restaurant actif
    # Pour une vraie implémentation, il faudrait lier user à restaurant
    return Restaurant.objects.filter(is_active=True).first()


@login_required
def profile(request):
    """Page de profil de l'établissement - modifier les informations"""
    restaurant = get_restaurant_for_user(request.user)

    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:dashboard')

    if request.method == 'POST':
        form = RestaurantProfileForm(request.POST, request.FILES, instance=restaurant)
        # Le nom est exclu du form, on le réapplique
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès.')
            return redirect('staff:profile')
    else:
        form = RestaurantProfileForm(instance=restaurant)

    context = {
        'restaurant': restaurant,
        'form': form,
    }
    return render(request, 'staff/profile.html', context)


@login_required
def finance(request):
    """Page de gestion financière - revenus et rapports"""
    restaurant = get_restaurant_for_user(request.user)

    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:dashboard')

    # Filtres de date
    date_filter = request.GET.get('date', 'today')
    start_date = timezone.now().date()
    end_date = start_date

    if date_filter == 'today':
        start_date = timezone.now().date()
        end_date = start_date
    elif date_filter == 'week':
        start_date = timezone.now().date() - timedelta(days=7)
        end_date = timezone.now().date()
    elif date_filter == 'month':
        start_date = timezone.now().date() - timedelta(days=30)
        end_date = timezone.now().date()
    elif date_filter == 'year':
        start_date = timezone.now().date() - timedelta(days=365)
        end_date = timezone.now().date()
    elif date_filter == 'custom':
        custom_start = request.GET.get('start_date')
        custom_end = request.GET.get('end_date')
        if custom_start and custom_end:
            start_date = timezone.datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(custom_end, '%Y-%m-%d').date()

    # Récupérer les commandes servies pour la période
    orders = Order.objects.filter(
        table__restaurant=restaurant,
        created_at__date__range=[start_date, end_date],
        status__in=['confirmed', 'preparing', 'ready', 'served']
    ).select_related('table').order_by('-created_at')

    # Calculer les statistiques
    total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0
    total_orders = orders.count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    # Revenus par jour (pour le graphique) - calcul manuel pour éviter SQL ambigu
    from collections import defaultdict
    daily_revenues_dict = defaultdict(lambda: {'revenue': 0, 'count': 0})
    for order in orders:
        date_str = order.created_at.date().isoformat()
        daily_revenues_dict[date_str]['revenue'] += float(order.total_price or 0)
        daily_revenues_dict[date_str]['count'] += 1
    
    daily_revenues = [
        {'date': date_str, 'revenue': data['revenue'], 'count': data['count']}
        for date_str, data in sorted(daily_revenues_dict.items())
    ]

    # Top produits
    top_items = OrderItem.objects.filter(
        order__table__restaurant=restaurant,
        order__created_at__date__range=[start_date, end_date],
        order__status__in=['confirmed', 'preparing', 'ready', 'served']
    ).values('menu_item__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('unit_price') * Sum('quantity')
    ).order_by('-total_quantity')[:10]

    context = {
        'restaurant': restaurant,
        'orders': orders,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'daily_revenues': daily_revenues,
        'top_items': top_items,
        'date_filter': date_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'staff/finance.html', context)


@login_required
def export_finance_pdf(request):
    """Export des rapports financiers en PDF"""
    # Implementation simplifiée - génère un CSV comme alternative
    from django.http import HttpResponse
    import csv

    restaurant = get_restaurant_for_user(request.user)
    if not restaurant:
        return redirect('staff:dashboard')

    date_filter = request.GET.get('date', 'today')
    start_date = timezone.now().date()

    if date_filter == 'week':
        start_date = timezone.now().date() - timedelta(days=7)
    elif date_filter == 'month':
        start_date = timezone.now().date() - timedelta(days=30)
    elif date_filter == 'year':
        start_date = timezone.now().date() - timedelta(days=365)

    orders = Order.objects.filter(
        table__restaurant=restaurant,
        created_at__date__gte=start_date,
        status__in=['confirmed', 'preparing', 'ready', 'served']
    ).select_related('table')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="rapport_finance_{start_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Rapport Financier - Restaurant', restaurant.name])
    writer.writerow(['Période', f'Du {start_date} au {timezone.now().date()}'])
    writer.writerow([])
    writer.writerow(['Date', 'Commande', 'Table', 'Statut', 'Total'])

    for order in orders:
        writer.writerow([
            order.created_at.strftime('%d/%m/%Y %H:%M'),
            f'#{str(order.uuid)[:8]}',
            order.table.name,
            order.get_status_display(),
            f'{order.total_price:.2f}€'
        ])

    return response


@login_required
def export_finance_excel(request):
    """Export des rapports financiers en Excel (format CSV amélioré)"""
    from django.http import HttpResponse
    import csv

    restaurant = get_restaurant_for_user(request.user)
    if not restaurant:
        return redirect('staff:dashboard')

    date_filter = request.GET.get('date', 'today')
    start_date = timezone.now().date()

    if date_filter == 'week':
        start_date = timezone.now().date() - timedelta(days=7)
    elif date_filter == 'month':
        start_date = timezone.now().date() - timedelta(days=30)
    elif date_filter == 'year':
        start_date = timezone.now().date() - timedelta(days=365)

    orders = Order.objects.filter(
        table__restaurant=restaurant,
        created_at__date__gte=start_date,
        status__in=['confirmed', 'preparing', 'ready', 'served']
    ).select_related('table')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="finance_export_{start_date}.csv"'
    response.write('\ufeff')  # BOM pour Excel UTF-8

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['RAPPORT FINANCIER', restaurant.name])
    writer.writerow(['Période', f'Du {start_date} au {timezone.now().date()}'])
    writer.writerow([])
    writer.writerow(['Date', 'Commande', 'Table', 'Statut', 'Articles', 'Total'])

    for order in orders:
        writer.writerow([
            order.created_at.strftime('%d/%m/%Y %H:%M'),
            f'#{str(order.uuid)[:8]}',
            order.table.name,
            order.get_status_display(),
            order.items.count(),
            f'{order.total_price:.2f}€'
        ])

    writer.writerow([])
    writer.writerow(['TOTAL', f'{orders.count()} commandes', '', '', '', f'{sum(o.total_price for o in orders):.2f}€'])

    return response


@login_required
def export_finance_word(request):
    """Export des rapports financiers en Word (format TXT structuré)"""
    from django.http import HttpResponse

    restaurant = get_restaurant_for_user(request.user)
    if not restaurant:
        return redirect('staff:dashboard')

    date_filter = request.GET.get('date', 'today')
    start_date = timezone.now().date()

    if date_filter == 'week':
        start_date = timezone.now().date() - timedelta(days=7)
    elif date_filter == 'month':
        start_date = timezone.now().date() - timedelta(days=30)
    elif date_filter == 'year':
        start_date = timezone.now().date() - timedelta(days=365)

    orders = Order.objects.filter(
        table__restaurant=restaurant,
        created_at__date__gte=start_date,
        status__in=['confirmed', 'preparing', 'ready', 'served']
    ).select_related('table')

    total = sum(o.total_price for o in orders)

    response = HttpResponse(content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="rapport_finance_{start_date}.txt"'

    content = f"""
================================================================================
                         RAPPORT FINANCIER
================================================================================

Restaurant : {restaurant.name}
Période    : Du {start_date} au {timezone.now().date()}

--------------------------------------------------------------------------------
                         RÉSUMÉ
--------------------------------------------------------------------------------

Nombre total de commandes : {orders.count()}
Chiffre d'affaires total  : {total:.2f} €
Panier moyen              : {total / orders.count() if orders.count() > 0 else 0:.2f} €

--------------------------------------------------------------------------------
                         DÉTAIL DES COMMANDES
--------------------------------------------------------------------------------

"""
    for order in orders:
        content += f"""
Commande #{str(order.uuid)[:8]}
  Date   : {order.created_at.strftime('%d/%m/%Y à %H:%M')}
  Table  : {order.table.name}
  Statut : {order.get_status_display()}
  Total  : {order.total_price:.2f} €
--------------------------------------------------------------------------------
"""

    content += f"""
================================================================================
                         FIN DU RAPPORT
================================================================================
"""

    response.write(content.encode('utf-8'))
    return response


@login_required
def add_menu_item(request):
    """Ajouter un élément au menu"""
    restaurant = get_restaurant_for_user(request.user)
    
    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:login')
    
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            menu_item = form.save(commit=False)
            menu_item.save()
            messages.success(request, f'"{menu_item.name}" a été ajouté au menu.')
            return redirect('staff:menu_items')
        else:
            messages.error(request, 'Erreur dans le formulaire.')
    else:
        form = MenuItemForm()
    
    context = {
        'restaurant': restaurant,
        'form': form,
    }
    return render(request, 'staff/add_menu_item.html', context)


@login_required
def menu_items(request):
    """Liste des éléments du menu"""
    restaurant = get_restaurant_for_user(request.user)

    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:login')

    # Recherche
    search_query = request.GET.get('search', '')

    # Devise sélectionnée (défaut: XAF)
    selected_currency = request.GET.get('currency', 'XAF')
    request.session['staff_currency'] = selected_currency

    # Taux de conversion
    from decimal import Decimal
    exchange_rates = {
        'XAF': Decimal('655.957'),
        'XOF': Decimal('655.957'),
        'EUR': Decimal('1.0'),
        'USD': Decimal('1.08'),
        'GBP': Decimal('0.85'),
        'CHF': Decimal('0.93'),
        'CAD': Decimal('1.47'),
    }
    exchange_rate = exchange_rates.get(selected_currency, Decimal('655.957'))

    if search_query:
        # Filtrer les categories qui ont des items correspondants
        categories = Category.objects.filter(
            restaurant=restaurant,
            items__name__icontains=search_query
        ).prefetch_related('items').order_by('order').distinct()
    else:
        categories = Category.objects.filter(
            restaurant=restaurant
        ).prefetch_related('items').order_by('order')

    context = {
        'restaurant': restaurant,
        'categories': categories,
        'search_query': search_query,
        'selected_currency': selected_currency,
        'exchange_rate': exchange_rate,
    }
    return render(request, 'staff/menu_items.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_menu_item_availability(request, item_id):
    """Activer/désactiver un élément du menu"""
    try:
        item = MenuItem.objects.get(id=item_id)
        data = json.loads(request.body)
        item.is_available = data.get('is_available', True)
        item.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def delete_menu_item(request, item_id):
    """Supprimer un élément du menu"""
    try:
        item = MenuItem.objects.get(id=item_id)
        item.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def bulk_delete_menu_items(request):
    """Supprimer plusieurs éléments du menu"""
    try:
        data = json.loads(request.body)
        item_ids = data.get('item_ids', [])
        MenuItem.objects.filter(id__in=item_ids).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def bulk_toggle_menu_items(request):
    """Activer/désactiver plusieurs éléments du menu"""
    try:
        data = json.loads(request.body)
        item_ids = data.get('item_ids', [])
        is_available = data.get('is_available', True)
        MenuItem.objects.filter(id__in=item_ids).update(is_available=is_available)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def edit_menu_item(request):
    """Modifier un élément du menu"""
    try:
        item_id = request.POST.get('item_id')
        item = MenuItem.objects.get(id=item_id)

        item.name = request.POST.get('name', item.name)
        item.description = request.POST.get('description', item.description)
        item.price = Decimal(request.POST.get('price', item.price))

        category_id = request.POST.get('category')
        if category_id:
            item.category_id = category_id
        
        # Update availability
        is_available = request.POST.get('is_available') == 'on'
        item.is_available = is_available

        item.save()

        messages.success(request, f'"{item.name}" a été modifié avec succès.')
        return redirect('staff:menu_items')
    except Exception as e:
        messages.error(request, f'Erreur: {str(e)}')
        return redirect('staff:menu_items')


@login_required
@require_POST
def add_category(request):
    """Ajouter une catégorie au menu"""
    restaurant = get_restaurant_for_user(request.user)
    
    if not restaurant:
        messages.error(request, "Aucun restaurant associé à votre compte.")
        return redirect('staff:login')
    
    name = request.POST.get('name', '')
    description = request.POST.get('description', '')
    order = request.POST.get('order', 0)
    
    if name:
        Category.objects.create(
            restaurant=restaurant,
            name=name,
            description=description,
            order=order
        )
        messages.success(request, f'Catégorie "{name}" ajoutée avec succès.')
    else:
        messages.error(request, 'Le nom de la catégorie est requis.')
    
    return redirect('staff:menu_items')
