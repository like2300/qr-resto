from django.core.management.base import BaseCommand
from menu.models import Restaurant, Category, MenuItem
from decimal import Decimal


class Command(BaseCommand):
    help = 'Crée des éléments de menu factices pour toutes les catégories'

    def handle(self, *args, **kwargs):
        # Récupérer le restaurant par défaut
        restaurant = Restaurant.objects.first()
        if not restaurant:
            self.stdout.write(self.style.ERROR('Aucun restaurant trouvé. Créez d\'abord un restaurant par défaut.'))
            return

        # Données factices pour les pizzas
        pizza_items = [
            {'name': 'Pizza Margherita', 'description': 'Tomate San Marzano, mozzarella di bufala, basilic frais, huile d\'olive', 'price': Decimal('12.00')},
            {'name': 'Pizza Pepperoni', 'description': 'Tomate, mozzarella, pepperoni italien, origan', 'price': Decimal('14.00')},
            {'name': 'Pizza 4 Fromages', 'description': 'Mozzarella, gorgonzola, chèvre, parmesan', 'price': Decimal('15.00')},
            {'name': 'Pizza Végétarienne', 'description': 'Tomate, mozzarella, poivrons, champignons, oignons, olives noires', 'price': Decimal('13.00')},
            {'name': 'Pizza Prosciutto', 'description': 'Tomate, mozzarella, jambon cru italien, roquette, parmesan', 'price': Decimal('16.00')},
        ]

        # Données factices pour la poule/volaille
        poule_items = [
            {'name': 'Poulet Rôti', 'description': 'Poulet fermier rôti aux herbes, pommes de terre grenailles', 'price': Decimal('18.00')},
            {'name': 'Suprême de Poulet', 'description': 'Suprême de poulet, sauce aux champignons, riz pilaf', 'price': Decimal('19.00')},
            {'name': 'Poulet Yassa', 'description': 'Poulet mariné au citron, oignons caramélisés, riz blanc', 'price': Decimal('17.00')},
            {'name': 'Ailes de Poulet', 'description': 'Ailes de poulet marinées, sauce barbecue, frites', 'price': Decimal('14.00')},
            {'name': 'Canard Confit', 'description': 'Cuisses de canard confites, haricots tarbais', 'price': Decimal('22.00')},
        ]

        # Données factices pour les jus
        jus_items = [
            {'name': 'Jus d\'Orange Pressé', 'description': 'Oranges fraîches pressées minute', 'price': Decimal('4.00')},
            {'name': 'Jus de Mangue', 'description': 'Jus de mangue naturel, sans sucre ajouté', 'price': Decimal('4.50')},
            {'name': 'Smoothie Vert', 'description': 'Épinards, pomme, concombre, citron vert', 'price': Decimal('5.00')},
            {'name': 'Jus de Bissap', 'description': 'Infusion de fleurs d\'hibiscus, menthe fraîche', 'price': Decimal('3.50')},
            {'name': 'Cocktail Tropical', 'description': 'Mélange ananas, mangue, fruit de la passion', 'price': Decimal('5.50')},
        ]

        # Récupérer les catégories
        categories_data = {
            'pizza': pizza_items,
            'poule': poule_items,
            'jus': jus_items,
        }

        total_created = 0

        for category_slug, items_data in categories_data.items():
            category = Category.objects.filter(
                restaurant=restaurant,
                name__iexact=category_slug
            ).first()

            if not category:
                self.stdout.write(self.style.WARNING(f'Catégorie "{category_slug}" non trouvée, skipping...'))
                continue

            # Créer les items pour cette catégorie
            for item_data in items_data:
                item, created = MenuItem.objects.get_or_create(
                    category=category,
                    name=item_data['name'],
                    defaults={
                        'description': item_data['description'],
                        'price': item_data['price'],
                        'is_available': True,
                    }
                )

                if created:
                    total_created += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ Créé: {item.name} ({category.name})'))
                else:
                    self.stdout.write(f'- Déjà existant: {item.name}')

        self.stdout.write(self.style.SUCCESS(f'\n=== Résumé ==='))
        self.stdout.write(f'{total_created} nouvel(s) élément(s) de menu créé(s) avec succès !')
        self.stdout.write(f'Restaurant: {restaurant.name}')
        self.stdout.write(f'Catégories mises à jour: {len(categories_data)}')
