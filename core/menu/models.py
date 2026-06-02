import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Restaurant(models.Model):
    """Restaurant avec ses informations"""
    name = models.CharField(max_length=200, verbose_name="Nom du restaurant")
    slug = models.SlugField(unique=True, verbose_name="Identifiant URL")
    description = models.TextField(blank=True, verbose_name="Description")

    # Informations de contact
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    website = models.URLField(blank=True, verbose_name="Site web")

    # Adresse
    address = models.CharField(max_length=255, blank=True, verbose_name="Adresse")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    postal_code = models.CharField(max_length=10, blank=True, verbose_name="Code postal")
    country = models.CharField(max_length=100, default="France", verbose_name="Pays")

    # Logo et images
    logo = models.ImageField(upload_to='restaurants/', blank=True, null=True, verbose_name="Logo")
    banner = models.ImageField(upload_to='restaurants/', blank=True, null=True, verbose_name="Bannière")

    # Couleurs par défaut
    primary_color = models.CharField(
        max_length=7,
        default="#3B82F6",
        verbose_name="Couleur principale",
        help_text="Couleur par défaut pour les tables"
    )

    # Paramètres de devise
    CURRENCY_CHOICES = [
        ('XAF', 'FCFA - Franc CFA'),
        ('EUR', '€ - Euro'),
        ('USD', '$ - Dollar US'),
        ('XOF', 'CFA - Franc Ouest Africain'),
        ('GBP', '£ - Livre Sterling'),
        ('CHF', 'CHF - Franc Suisse'),
        ('CAD', 'C$ - Dollar Canadien'),
    ]
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='XAF',  # XAF par défaut
        verbose_name="Devise par défaut"
    )
    
    # Taux de conversion personnalisé (base EUR)
    custom_exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1.0,
        verbose_name="Taux de conversion personnalisé",
        help_text="Taux par rapport à l'EUR (1 EUR = X devise)"
    )
    
    # TVA
    vat_enabled = models.BooleanField(
        default=True,
        verbose_name="Afficher la TVA"
    )
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.0,
        verbose_name="Taux de TVA (%)",
        help_text="Taux de TVA en pourcentage"
    )
    
    # Paiement MomPay
    mompay_merchant_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Code marchand MomPay",
        help_text="Code marchand pour le paiement MomPay (laisser vide pour désactiver)"
    )
    mompay_enabled = models.BooleanField(
        default=False,
        verbose_name="Activer MomPay"
    )

    # Notifications vocales
    bill_notification_repeats = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Répétitions notification vocale",
        help_text="Nombre de fois que la notification vocale est répétée (1-5)"
    )
    voice_notifications_enabled = models.BooleanField(
        default=True,
        verbose_name="Activer notifications vocales"
    )

    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Restaurant"
        verbose_name_plural = "Restaurants"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def currency_symbol(self):
        """Retourne le symbole de la devise"""
        symbols = {
            'EUR': '€',
            'USD': '$',
            'XAF': 'FCFA',
            'XOF': 'CFA',
            'GBP': '£',
            'CHF': 'CHF',
            'CAD': 'C$',
        }
        return symbols.get(self.currency, self.currency)


class Announcement(models.Model):
    """Annonce/Notification pour les utilisateurs"""
    title = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    image = models.ImageField(upload_to='announcements/', blank=True, null=True, verbose_name="Image")
    
    # Affichage
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    priority = models.PositiveSmallIntegerField(default=0, verbose_name="Priorité")
    
    # Dates
    start_date = models.DateTimeField(blank=True, null=True, verbose_name="Date de début")
    end_date = models.DateTimeField(blank=True, null=True, verbose_name="Date de fin")
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Annonce"
        verbose_name_plural = "Annonces"
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return self.title

    def is_currently_active(self):
        """Vérifie si l'annonce est active selon les dates"""
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return self.is_active


class Table(models.Model):
    """Table du restaurant avec un UUID unique et couleur personnalisable"""
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='tables',
        on_delete=models.CASCADE,
        verbose_name="Restaurant",
        null=True,
        blank=True
    )
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, verbose_name="Nom de la table")
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        verbose_name="Couleur",
        help_text="Couleur de la table (format hexadécimal, ex: #FF5733)"
    )
    capacity = models.PositiveSmallIntegerField(
        default=4,
        verbose_name="Capacité",
        help_text="Nombre de places"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    is_occupied = models.BooleanField(default=False, verbose_name="Occupée")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Table"
        verbose_name_plural = "Tables"
        ordering = ['name']
        indexes = [models.Index(fields=['restaurant', 'is_active'])]

    def __str__(self):
        if self.restaurant:
            return f"{self.restaurant.name} - {self.name}"
        return self.name

    @property
    def qr_code_url(self):
        """Génère l'URL du QR code via API externe"""
        menu_url = self.get_menu_url()
        return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={menu_url}"

    def get_menu_url(self):
        """Retourne l'URL complète du menu pour cette table"""
        domain = 'qr-resto.alwaysdata.net'
        return f"http://{domain}/m/{self.uuid}/"


class Category(models.Model):
    """Catégorie de plats (entrée, plat principal, dessert, etc.)"""
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='categories',
        on_delete=models.CASCADE,
        verbose_name="Restaurant",
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['order', 'name']
        indexes = [models.Index(fields=['restaurant', 'order'])]

    def __str__(self):
        if self.restaurant:
            return f"{self.restaurant.name} - {self.name}"
        return self.name


class MenuItem(models.Model):
    """Élément du menu avec prix en FCFA"""
    category = models.ForeignKey(
        Category,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name="Catégorie"
    )
    name = models.CharField(max_length=200, verbose_name="Nom du plat")
    description = models.TextField(blank=True, verbose_name="Description")
    price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="Prix (FCFA)"
    )
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    image = models.ImageField(
        upload_to='menu_items/',
        blank=True,
        null=True,
        verbose_name="Image"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Élément du menu"
        verbose_name_plural = "Éléments du menu"
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} - {self.price}€"


class Comment(models.Model):
    """Commentaire laissé par une table"""
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='comments',
        on_delete=models.CASCADE,
        verbose_name="Restaurant",
        null=True,
        blank=True
    )
    table = models.ForeignKey(
        Table,
        related_name='comments',
        on_delete=models.CASCADE,
        verbose_name="Table"
    )
    menu_item = models.ForeignKey(
        MenuItem,
        related_name='comments',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Élément du menu"
    )
    content = models.TextField(verbose_name="Commentaire")
    rating = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="Note",
        help_text="Note de 1 à 5"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False, verbose_name="Résolu")

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['-created_at']
        indexes = [models.Index(fields=['restaurant', '-created_at'])]

    def __str__(self):
        return f"Commentaire de {self.table.name} - {self.created_at.strftime('%Y-%m-%d')}"


class Order(models.Model):
    """Commande d'une table"""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('preparing', 'En préparation'),
        ('ready', 'Prête'),
        ('served', 'Servie'),
        ('cancelled', 'Annulée'),
    ]
    
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    table = models.ForeignKey(
        Table,
        related_name='orders',
        on_delete=models.CASCADE,
        verbose_name="Table"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Prix total (€)"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    served_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de service"
    )
    bill_requested = models.BooleanField(
        default=False,
        verbose_name="Addition demandée"
    )
    bill_requested_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date demande addition"
    )

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande {self.table.name} - {self.created_at.strftime('%d/%m %H:%M')}"
    
    def calculate_total(self):
        """Recalcule le prix total de la commande"""
        self.total_price = sum(item.subtotal for item in self.items.all())
        self.save()


class OrderItem(models.Model):
    """Élément d'une commande"""
    
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name="Commande"
    )
    menu_item = models.ForeignKey(
        MenuItem,
        related_name='order_items',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Élément du menu"
    )
    quantity = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Quantité"
    )
    unit_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Prix unitaire (€)"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes (cuisson, allergènes...)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Élément de commande"
        verbose_name_plural = "Éléments de commande"

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name if self.menu_item else 'Item supprimé'}"
    
    @property
    def subtotal(self):
        """Sous-total pour cet élément"""
        return self.quantity * self.unit_price


class AdminTheme(models.Model):
    """Configuration des couleurs de l'admin panel"""
    
    THEME_CHOICES = [
        ('light', 'Clair'),
        ('dark', 'Sombre'),
        ('auto', 'Automatique'),
    ]
    
    name = models.CharField(
        max_length=50,
        default="Thème Principal",
        verbose_name="Nom du thème"
    )
    theme_mode = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light',
        verbose_name="Mode du thème"
    )
    
    # Couleurs principales
    primary_color = models.CharField(
        max_length=7,
        default="#3B82F6",
        verbose_name="Couleur principale",
        help_text="Couleur primaire (boutons, liens)"
    )
    primary_hover = models.CharField(
        max_length=7,
        default="#2563EB",
        verbose_name="Couleur principale (survol)"
    )
    primary_light = models.CharField(
        max_length=7,
        default="#DBEAFE",
        verbose_name="Couleur principale (clair)"
    )
    
    # Couleurs sidebar
    sidebar_bg = models.CharField(
        max_length=7,
        default="#1E293B",
        verbose_name="Sidebar (fond)",
        help_text="Arrière-plan de la barre latérale"
    )
    sidebar_bg_gradient = models.CharField(
        max_length=7,
        default="#0F172A",
        verbose_name="Sidebar (dégradé)",
        help_text="Couleur de fin du dégradé"
    )
    sidebar_text = models.CharField(
        max_length=7,
        default="#F8FAFC",
        verbose_name="Sidebar (texte)"
    )
    
    # Couleurs de fond
    bg_color = models.CharField(
        max_length=7,
        default="#F9FAFB",
        verbose_name="Arrière-plan général"
    )
    card_bg = models.CharField(
        max_length=7,
        default="#FFFFFF",
        verbose_name="Cartes (fond)"
    )
    
    # Couleurs de texte
    text_primary = models.CharField(
        max_length=7,
        default="#1F2937",
        verbose_name="Texte principal"
    )
    text_secondary = models.CharField(
        max_length=7,
        default="#6B7280",
        verbose_name="Texte secondaire"
    )
    
    # Couleurs d'état
    success_color = models.CharField(
        max_length=7,
        default="#10B981",
        verbose_name="Succès (vert)"
    )
    warning_color = models.CharField(
        max_length=7,
        default="#F59E0B",
        verbose_name="Avertissement (orange)"
    )
    danger_color = models.CharField(
        max_length=7,
        default="#EF4444",
        verbose_name="Danger/Erreur (rouge)"
    )
    info_color = models.CharField(
        max_length=7,
        default="#3B82F6",
        verbose_name="Information (bleu)"
    )
    
    # Bordures
    border_color = models.CharField(
        max_length=7,
        default="#E5E7EB",
        verbose_name="Couleur des bordures"
    )
    
    # Rayons des bords
    border_radius = models.PositiveSmallIntegerField(
        default=8,
        verbose_name="Arrondi des bords (px)",
        help_text="Rayon des bords en pixels"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Thème Admin"
        verbose_name_plural = "Thèmes Admin"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # S'assurer qu'un seul thème est actif à la fois
        if self.is_active:
            AdminTheme.objects.filter(is_active=True).update(is_active=False)
            self.is_active = True
        super().save(*args, **kwargs)
