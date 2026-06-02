from menu.models import AdminTheme, Order, Comment


def admin_theme(request):
    """Context processor pour charger le thème admin actif"""
    try:
        theme = AdminTheme.objects.filter(is_active=True).first()
        if theme:
            return {
                'admin_theme': theme,
            }
    except Exception:
        pass
    return {}


def pending_bills_count(request):
    """Context processor pour ajouter le nombre de demandes d'addition en attente"""
    if request.user.is_authenticated:
        from menu.models import Restaurant
        restaurant = Restaurant.objects.filter(is_active=True).first()
        if restaurant:
            pending_bills = Order.objects.filter(
                table__restaurant=restaurant,
                bill_requested=True
            ).count()
            return {'pending_bills': pending_bills}
    return {'pending_bills': 0}


def pending_comments_count(request):
    """Context processor pour ajouter le nombre de commentaires en attente"""
    if request.user.is_authenticated:
        from menu.models import Restaurant
        restaurant = Restaurant.objects.filter(is_active=True).first()
        if restaurant:
            pending_comments = Comment.objects.filter(
                restaurant=restaurant,
                is_resolved=False
            ).count()
            return {'pending_comments': pending_comments}
    return {'pending_comments': 0}
