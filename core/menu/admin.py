from django.contrib import admin
from django.urls import path
from django.utils.html import format_html
from unfold.admin import ModelAdmin, StackedInline
from .models import Restaurant, Table, Category, MenuItem, Comment, AdminTheme, Order, OrderItem, Announcement


@admin.register(Restaurant)
class RestaurantAdmin(ModelAdmin):
    list_display = ['name', 'city', 'phone', 'currency', 'vat_enabled', 'is_active', 'created_at']
    list_filter = ['is_active', 'country', 'currency', 'vat_enabled']
    search_fields = ['name', 'city', 'email']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'slug', 'description', 'is_active')
        }),
        ('Coordonnées', {
            'fields': ('email', 'phone', 'website')
        }),
        ('Adresse', {
            'fields': ('address', 'city', 'postal_code', 'country')
        }),
        ('Logo et bannière', {
            'fields': ('logo', 'banner')
        }),
        ('Couleurs par défaut', {
            'fields': ('primary_color',)
        }),
        ('Devise et TVA', {
            'fields': ('currency', 'custom_exchange_rate', 'vat_enabled', 'vat_rate')
        }),
        ('Paiement MomPay', {
            'fields': ('mompay_enabled', 'mompay_merchant_code')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Announcement)
class AnnouncementAdmin(ModelAdmin):
    list_display = ['title', 'priority', 'is_active', 'start_date', 'end_date', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Contenu', {
            'fields': ('title', 'message', 'image')
        }),
        ('Affichage', {
            'fields': ('is_active', 'priority', 'start_date', 'end_date')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Table)
class TableAdmin(ModelAdmin):
    list_display = ['name', 'restaurant_link', 'color_preview', 'qr_code_display', 'uuid', 'capacity', 'is_active', 'created_at']
    list_filter = ['is_active', 'capacity', 'restaurant']
    search_fields = ['name', 'uuid']
    readonly_fields = ['uuid', 'color_preview', 'qr_code_display', 'created_at', 'updated_at']
    change_form_template = 'admin/table_change_form.html'
    fieldsets = (
        (None, {
            'fields': ('restaurant', 'name', 'uuid', 'color', 'color_preview', 'capacity', 'is_active', 'qr_code_display')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def restaurant_link(self, obj):
        if obj.restaurant is None:
            return format_html('<span style="color: #999;">-</span>')
        return format_html('<a href="?restaurant__id={}">{}</a>', obj.restaurant.id, obj.restaurant.name)
    restaurant_link.short_description = "Restaurant"

    def color_preview(self, obj):
        """Aperçu de la couleur de la table"""
        if obj.pk:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 10px;">'
                '<div style="width: 30px; height: 30px; background-color: {}; '
                'border-radius: 5px; border: 1px solid #ddd;"></div>'
                '<span>{}</span>'
                '</div>',
                obj.color,
                obj.color
            )
        return None
    color_preview.short_description = "Aperçu couleur"
    
    def qr_code_display(self, obj):
        """Affiche le QR code de la table"""
        if not obj.pk:
            return "Enregistrez la table d'abord"
        
        qr_url = obj.qr_code_url
        menu_url = obj.get_menu_url()
        
        return format_html(
            '<div style="display: flex; flex-direction: column; align-items: center; gap: 10px;">'
            '<img src="{}" alt="QR Code" style="width: 200px; height: 200px; border: 2px solid #ddd; border-radius: 8px;">'
            '<a href="{}" target="_blank" class="btn btn-sm" style="background: #3B82F6; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none;">'
            '<i class="ri-external-link-line mr-1"></i>Ouvrir le menu</a>'
            '<a href="{}" download="qr_table_{}.png" class="btn btn-sm" style="background: #10B981; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none;">'
            '<i class="ri-download-line mr-1"></i>Télécharger le QR code</a>'
            '<p style="color: #666; font-size: 12px; word-break: break-all; text-align: center;">{}</p>'
            '</div>',
            qr_url,
            menu_url,
            qr_url,
            obj.name,
            menu_url
        )
    qr_code_display.short_description = "QR Code"
    
    def get_urls(self):
        urls = super().get_urls()
        return urls


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'restaurant_link', 'order', 'created_at']
    list_editable = ['order']
    ordering = ['order']
    search_fields = ['name']
    list_filter = ['restaurant']

    def restaurant_link(self, obj):
        if obj.restaurant is None:
            return format_html('<span style="color: #999;">-</span>')
        return format_html('<a href="?restaurant__id={}">{}</a>', obj.restaurant.id, obj.restaurant.name)
    restaurant_link.short_description = "Restaurant"


@admin.register(MenuItem)
class MenuItemAdmin(ModelAdmin):
    list_display = ['name', 'category', 'restaurant_link', 'price', 'is_available', 'created_at']
    list_filter = ['category__restaurant', 'category', 'is_available']
    search_fields = ['name', 'description']
    list_editable = ['price', 'is_available']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'description', 'price', 'is_available', 'image')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def restaurant_link(self, obj):
        if obj.category and obj.category.restaurant:
            return format_html('<a href="?category__restaurant__id={}">{}</a>', obj.category.restaurant.id, obj.category.restaurant.name)
        return format_html('<span style="color: #999;">-</span>')
    restaurant_link.short_description = "Restaurant"


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ['table', 'menu_item', 'rating_badge', 'content_preview', 'created_at', 'is_resolved']
    list_filter = ['is_resolved', 'rating', 'created_at', 'table']
    search_fields = ['table__name', 'content']
    readonly_fields = ['created_at']
    list_editable = ['is_resolved']
    
    def rating_badge(self, obj):
        """Affiche la note avec des étoiles"""
        stars = "⭐" * obj.rating
        return format_html('<span style="font-size: 1.2em;">{}</span>', stars)
    rating_badge.short_description = "Note"
    
    def content_preview(self, obj):
        """Aperçu du commentaire"""
        content = obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        return format_html('<span style="color: #666;">{}</span>', content)
    content_preview.short_description = "Commentaire"


class OrderItemInline(StackedInline):
    model = OrderItem
    extra = 0
    fields = ('menu_item', 'quantity', 'unit_price', 'notes')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            formset.extra = 0
        return formset


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ['uuid_short', 'table', 'status_badge', 'total_price', 'items_count', 'created_at']
    list_filter = ['status', 'table', 'created_at']
    search_fields = ['uuid', 'table__name', 'notes']
    readonly_fields = ['uuid', 'total_price', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Informations', {
            'fields': ('uuid', 'table', 'status', 'total_price')
        }),
        ('Notes', {
            'fields': ('notes',),
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'served_at'),
            'classes': ('collapse',)
        }),
    )
    
    def uuid_short(self, obj):
        return str(obj.uuid)[:8]
    uuid_short.short_description = "UUID"
    
    def status_badge(self, obj):
        colors = {
            'pending': '#F59E0B',
            'confirmed': '#3B82F6',
            'preparing': '#8B5CF6',
            'ready': '#10B981',
            'served': '#6B7280',
            'cancelled': '#EF4444',
        }
        labels = {
            'pending': 'En attente',
            'confirmed': 'Confirmée',
            'preparing': 'En préparation',
            'ready': 'Prête',
            'served': 'Servie',
            'cancelled': 'Annulée',
        }
        color = colors.get(obj.status, '#6B7280')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; '
            'border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">{}</span>',
            color, label
        )
    status_badge.short_description = "Statut"
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Articles"


@admin.register(AdminTheme)
class AdminThemeAdmin(ModelAdmin):
    list_display = ['name', 'theme_mode', 'primary_color_preview', 'is_active', 'updated_at']
    list_filter = ['theme_mode', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'preview_panel']
    change_form_template = 'admin/admintheme_change_form.html'
    
    fieldsets = (
        ('Général', {
            'fields': ('name', 'theme_mode', 'is_active')
        }),
        ('Couleurs principales', {
            'fields': (
                ('primary_color', 'primary_hover', 'primary_light'),
            )
        }),
        ('Sidebar', {
            'fields': (
                ('sidebar_bg', 'sidebar_bg_gradient', 'sidebar_text'),
            )
        }),
        ('Arrière-plans', {
            'fields': (
                ('bg_color', 'card_bg'),
            )
        }),
        ('Textes', {
            'fields': (
                ('text_primary', 'text_secondary'),
            )
        }),
        ("Couleurs d'état", {
            'fields': (
                ('success_color', 'warning_color', 'danger_color', 'info_color'),
            )
        }),
        ('Bordures', {
            'fields': (
                ('border_color', 'border_radius'),
            )
        }),
        ('Aperçu', {
            'fields': ('preview_panel',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def primary_color_preview(self, obj):
        """Aperçu de la couleur principale"""
        if obj.pk:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 10px;">'
                '<div style="width: 30px; height: 30px; background-color: {}; '
                'border-radius: 5px; border: 1px solid #ddd;"></div>'
                '</div>',
                obj.primary_color
            )
        return None
    primary_color_preview.short_description = "Aperçu"
    
    def preview_panel(self, obj):
        """Panneau d'aperçu des couleurs"""
        if not obj.pk:
            return "Sauvegardez d'abord le thème pour voir l'aperçu"
        
        return format_html(
            '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; padding: 20px; background: #f9fafb; border-radius: 8px;">'
            '<div style="text-align: center;"><div style="width: 50px; height: 50px; background-color: {}; border-radius: {}px; margin: 0 auto 5px;"></div><small>Principale</small></div>'
            '<div style="text-align: center;"><div style="width: 50px; height: 50px; background-color: {}; border-radius: {}px; margin: 0 auto 5px;"></div><small>Succès</small></div>'
            '<div style="text-align: center;"><div style="width: 50px; height: 50px; background-color: {}; border-radius: {}px; margin: 0 auto 5px;"></div><small>Avertissement</small></div>'
            '<div style="text-align: center;"><div style="width: 50px; height: 50px; background-color: {}; border-radius: {}px; margin: 0 auto 5px;"></div><small>Danger</small></div>'
            '<div style="text-align: center;"><div style="width: 50px; height: 50px; background-color: {}; border-radius: {}px; margin: 0 auto 5px;"></div><small>Sidebar</small></div>'
            '<div style="text-align: center;"><div style="width: 50px; height: 50px; background-color: {}; border-radius: {}px; margin: 0 auto 5px;"></div><small>Fond</small></div>'
            '<div style="text-align: center;"><div style="width: 50px; height: 50px; background-color: {}; border-radius: {}px; margin: 0 auto 5px;"></div><small>Cartes</small></div>'
            '<div style="text-align: center;"><div style="width: 50px; height: 50px; background-color: {}; border-radius: {}px; margin: 0 auto 5px; border: 1px solid #ddd;"></div><small>Bordure</small></div>'
            '</div>',
            obj.primary_color, obj.border_radius,
            obj.success_color, obj.border_radius,
            obj.warning_color, obj.border_radius,
            obj.danger_color, obj.border_radius,
            obj.sidebar_bg, obj.border_radius,
            obj.bg_color, obj.border_radius,
            obj.card_bg, obj.border_radius,
            obj.border_color, obj.border_radius,
        )
    preview_panel.short_description = "Aperçu des couleurs"
