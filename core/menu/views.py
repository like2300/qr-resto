from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Restaurant, Table, Category, MenuItem, Order, OrderItem
from .forms import OrderForm
import decimal


def menu(request, table_uuid):
    """Affiche le menu du restaurant pour une table donnée"""
    table = get_object_or_404(Table, uuid=table_uuid, is_active=True)
    restaurant = table.restaurant

    # Récupérer la devise depuis l'URL, puis la session, puis défaut XAF
    selected_currency = request.GET.get('currency', request.session.get('selected_currency', 'XAF'))
    request.session['selected_currency'] = selected_currency

    # Récupérer le taux de conversion via API (base FCFA vers devise sélectionnée)
    exchange_rate = get_exchange_rate_for_xaf(selected_currency)

    # Symbole de la devise
    symbols = {
        'EUR': '€',
        'USD': '$',
        'XAF': 'FCFA',
        'XOF': 'CFA',
        'GBP': '£',
        'CHF': 'CHF',
        'CAD': 'C$',
    }
    currency_symbol = symbols.get(selected_currency, selected_currency)

    # Filtrer les catégories du restaurant
    categories = Category.objects.filter(
        restaurant=restaurant,
        items__is_available=True
    ).prefetch_related('items').distinct().order_by('order')
    
    # Récupérer l'annonce active
    from .models import Announcement
    announcement = Announcement.objects.filter(
        is_active=True
    ).exclude(
        start_date__gt=timezone.now()
    ).exclude(
        end_date__lt=timezone.now()
    ).order_by('-priority', '-created_at').first()

    context = {
        'table': table,
        'restaurant': restaurant,
        'categories': categories,
        'selected_currency': selected_currency,
        'exchange_rate': exchange_rate,
        'currency_symbol': currency_symbol,
        'announcement': announcement,
    }
    return render(request, 'menu/menu.html', context)


def get_exchange_rate_for_xaf(currency):
    """Récupère le taux de conversion FCFA vers devise sélectionnée
    
    Les prix sont en FCFA dans la base.
    XAF/XOF sont fixes (1.0).
    Pour les autres, on utilise l'API (base EUR) puis on convertit.
    """
    import urllib.request
    import json
    from decimal import Decimal

    # XAF/XOF - taux fixe
    if currency == 'XAF' or currency == 'XOF':
        return Decimal('1.0')

    # Utiliser l'API exchangerate-api.com (base EUR)
    try:
        url = f'https://api.exchangerate-api.com/v4/latest/EUR'
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            eur_rate = Decimal(str(data['rates'].get(currency, 1.0)))
            
            # 1 EUR = 655.957 FCFA
            # Donc 1 FCFA = 1/655.957 EUR
            # Et 1 FCFA = (1/655.957) * eur_rate dans la devise cible
            xaf_to_eur = Decimal('1') / Decimal('655.957')
            xaf_to_currency = xaf_to_eur * eur_rate
            
            return xaf_to_currency
    except Exception:
        # Fallback sur les taux fixes
        fixed_rates = {
            'EUR': Decimal('0.001525'),  # 1/655.957
            'USD': Decimal('0.001650'),  # 1/607.37
            'XAF': Decimal('1.0'),
            'XOF': Decimal('1.0'),
            'GBP': Decimal('0.001296'),  # 1/771.71
            'CHF': Decimal('0.001418'),  # 1/705.33
            'CAD': Decimal('0.002241'),  # 1/446.23
        }
        return fixed_rates.get(currency, Decimal('1.0'))


def get_exchange_rate(currency):
    """Récupère le taux de conversion depuis une API gratuite (base EUR)
    
    Les prix dans la base sont en EUR, on convertit vers la devise sélectionnée.
    XAF/XOF sont les devises par défaut d'affichage.
    """
    import urllib.request
    import json
    
    # Taux fixes pour les devises africaines (pegged to EUR)
    if currency == 'XAF' or currency == 'XOF':
        return decimal.Decimal('655.957')
    
    # Utiliser l'API gratuite exchangerate-api.com
    try:
        url = f'https://api.exchangerate-api.com/v4/latest/EUR'
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            rate = data['rates'].get(currency, 1.0)
            return decimal.Decimal(str(rate))
    except Exception:
        # Fallback sur les taux fixes en cas d'erreur
        fixed_rates = {
            'EUR': decimal.Decimal('1.0'),
            'USD': decimal.Decimal('1.08'),
            'XAF': decimal.Decimal('655.957'),
            'XOF': decimal.Decimal('655.957'),
            'GBP': decimal.Decimal('0.85'),
            'CHF': decimal.Decimal('0.93'),
            'CAD': decimal.Decimal('1.47'),
        }
        return fixed_rates.get(currency, decimal.Decimal('1.0'))


def update_currency(request):
    """Met à jour la devise sélectionnée via AJAX"""
    if request.method == 'POST':
        currency = request.POST.get('currency', 'XAF')
        request.session['selected_currency'] = currency
        exchange_rate = get_exchange_rate(currency)
        
        # Symbole de la devise
        symbols = {
            'EUR': '€',
            'USD': '$',
            'XAF': 'FCFA',
            'XOF': 'CFA',
            'GBP': '£',
            'CHF': 'CHF',
            'CAD': 'C$',
        }
        currency_symbol = symbols.get(currency, currency)
        
        return JsonResponse({
            'success': True,
            'currency': currency,
            'exchange_rate': str(exchange_rate),
            'currency_symbol': currency_symbol,
        })
    return JsonResponse({'success': False})


@require_POST
@transaction.atomic
def create_order(request, table_uuid):
    """Crée une nouvelle commande"""
    table = get_object_or_404(Table, uuid=table_uuid, is_active=True)

    # Récupérer les items du POST
    items_data = request.POST.get('items', '')
    notes = request.POST.get('notes', '')

    if not items_data:
        messages.error(request, 'Votre commande est vide')
        return redirect('menu:menu', table_uuid=table.uuid)

    # Créer la commande
    order = Order.objects.create(
        table=table,
        notes=notes
    )

    # Ajouter les items
    total = 0
    items_count = 0
    for item_str in items_data.split('|'):
        if not item_str:
            continue
        parts = item_str.split(':')
        if len(parts) != 3:
            continue

        menu_item_id, quantity, price = parts
        try:
            menu_item = MenuItem.objects.get(id=int(menu_item_id), is_available=True)
            quantity = int(quantity)
            price = float(price)
            
            # Skip if price is 0 or invalid
            if price <= 0:
                continue

            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=quantity,
                unit_price=price
            )
            total += quantity * price
            items_count += 1
        except (MenuItem.DoesNotExist, ValueError) as e:
            continue
    
    # If no items were added, show error
    if items_count == 0:
        messages.error(request, 'Aucun article valide dans votre commande')
        return redirect('menu:menu', table_uuid=table.uuid)

    # Mettre à jour le total
    order.total_price = total
    order.save()

    # Marquer la table comme occupée
    table.is_occupied = True
    table.save()

    messages.success(request, f'Commande #{str(order.uuid)[:8]} créée avec succès !')
    return redirect('menu:order_detail', table_uuid=table.uuid, order_uuid=order.uuid)


def order_detail(request, table_uuid, order_uuid):
    """Détail d'une commande"""
    table = get_object_or_404(Table, uuid=table_uuid, is_active=True)
    order = get_object_or_404(Order.objects.prefetch_related('items__menu_item'), uuid=order_uuid, table=table)
    restaurant = table.restaurant

    # Calculer le total de la commande à partir des items
    total_from_items = sum(item.subtotal for item in order.items.all())
    
    # Si le total stocké est 0 ou différent, utiliser le calculé
    if order.total_price == 0 or order.total_price != total_from_items:
        order.total_price = total_from_items

    # Récupérer la devise depuis l'URL, puis la session, puis défaut XAF
    selected_currency = request.GET.get('currency', request.session.get('selected_currency', 'XAF'))
    request.session['selected_currency'] = selected_currency
    
    # Récupérer le taux de conversion via API
    exchange_rate = get_exchange_rate_for_xaf(selected_currency)

    # Symbole de la devise
    symbols = {
        'EUR': '€',
        'USD': '$',
        'XAF': 'FCFA',
        'XOF': 'CFA',
        'GBP': '£',
        'CHF': 'CHF',
        'CAD': 'C$',
    }
    currency_symbol = symbols.get(selected_currency, selected_currency)

    # Vérifier si MomPay est activé
    mompay_enabled = restaurant.mompay_enabled and bool(restaurant.mompay_merchant_code)

    # Calculer le total converti
    total_converted = float(order.total_price) * float(exchange_rate)

    context = {
        'table': table,
        'restaurant': restaurant,
        'order': order,
        'selected_currency': selected_currency,
        'exchange_rate': exchange_rate,
        'currency_symbol': currency_symbol,
        'mompay_enabled': mompay_enabled,
        'total_converted': total_converted,
    }
    return render(request, 'menu/order_detail.html', context)


@require_POST
@transaction.atomic
def request_bill(request, table_uuid, order_uuid):
    """Demander l'addition"""
    table = get_object_or_404(Table, uuid=table_uuid, is_active=True)
    order = get_object_or_404(Order, uuid=order_uuid, table=table)
    
    # Marquer la demande d'addition
    order.bill_requested = True
    order.bill_requested_at = timezone.now()
    order.save()
    
    # Libérer la table automatiquement quand l'addition est demandée
    # Marquer toutes les commandes en cours de cette table comme servies
    Order.objects.filter(
        table=table,
        status__in=['pending', 'confirmed', 'preparing', 'ready']
    ).update(status='served')

    # Libérer la table
    table.is_occupied = False
    table.save()
    
    messages.success(request, 'Votre demande d\'addition a été envoyée au personnel. La table est maintenant libérée.')
    return redirect('menu:order_detail', table_uuid=table_uuid, order_uuid=order_uuid)


def order_status(request, table_uuid, order_uuid):
    """Vérifie le statut d'une commande (API)"""
    table = get_object_or_404(Table, uuid=table_uuid, is_active=True)
    order = get_object_or_404(Order, uuid=order_uuid, table=table)

    data = {
        'status': order.status,
        'status_display': order.get_status_display(),
        'total_price': str(order.total_price),
        'items_count': order.items.count(),
    }
    return JsonResponse(data)


def order_invoice_pdf(request, table_uuid, order_uuid):
    """Affiche la facture d'une commande (pour impression PDF)"""
    table = get_object_or_404(Table, uuid=table_uuid, is_active=True)
    order = get_object_or_404(Order, uuid=order_uuid, table=table)
    restaurant = table.restaurant

    # Les prix sont déjà en FCFA dans la base de données
    selected_currency = 'XAF'
    exchange_rate = 1.0
    currency_symbol = 'FCFA'

    # Vérifier si MomPay est activé
    mompay_enabled = restaurant.mompay_enabled and bool(restaurant.mompay_merchant_code)

    # Libérer la table quand le client ouvre la facture
    # Marquer toutes les commandes en cours comme servies
    Order.objects.filter(
        table=table,
        status__in=['pending', 'confirmed', 'preparing', 'ready']
    ).update(status='served')

    # Libérer la table
    table.is_occupied = False
    table.save()

    context = {
        'table': table,
        'restaurant': restaurant,
        'order': order,
        'selected_currency': selected_currency,
        'exchange_rate': exchange_rate,
        'currency_symbol': currency_symbol,
        'mompay_enabled': mompay_enabled,
        'mompay_merchant_code': restaurant.mompay_merchant_code if mompay_enabled else '',
    }
    return render(request, 'menu/invoice.html', context)


@require_POST
@transaction.atomic
def cancel_order(request, table_uuid, order_uuid):
    """Annule une commande"""
    table = get_object_or_404(Table, uuid=table_uuid, is_active=True)
    order = get_object_or_404(Order, uuid=order_uuid, table=table)

    # On ne peut annuler que si la commande est en attente ou confirmée
    if order.status in ['pending', 'confirmed']:
        order.status = 'cancelled'
        order.save()
        
        # Vérifier si la table a d'autres commandes actives
        has_active_orders = Order.objects.filter(
            table=table,
            status__in=['pending', 'confirmed', 'preparing', 'ready']
        ).exists()
        
        # Si aucune autre commande active, libérer la table
        if not has_active_orders:
            table.is_occupied = False
            table.save()
        
        messages.success(request, f'Commande #{str(order.uuid)[:8]} annulée avec succès !')
    else:
        messages.error(request, 'Cette commande ne peut plus être annulée.')

    return redirect('menu:order_detail', table_uuid=table_uuid, order_uuid=order_uuid)


@require_POST
@transaction.atomic
def free_table(request, table_uuid):
    """Libère la table et marque les commandes comme servies"""
    table = get_object_or_404(Table, uuid=table_uuid, is_active=True)

    # Marquer toutes les commandes en cours comme servies
    Order.objects.filter(
        table=table,
        status__in=['pending', 'confirmed', 'preparing', 'ready']
    ).update(status='served')

    # Libérer la table
    table.is_occupied = False
    table.save()

    messages.success(request, f'Table {table.name} libérée avec succès !')
    return redirect('menu:menu', table_uuid=table_uuid)


@require_POST
def notify_bill_request(request):
    """Notification quand un client demande l'addition"""
    try:
        import json
        data = json.loads(request.body)
        table_number = data.get('table_number')
        order_uuid = data.get('order_uuid')
        
        # Ici, on pourrait envoyer une notification push au staff
        # Pour l'instant, on retourne juste un succès
        return JsonResponse({
            'success': True,
            'message': f'Demande d\'addition pour la table {table_number}',
            'table_number': table_number,
            'order_uuid': order_uuid
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
