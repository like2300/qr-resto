from django.core.management.base import BaseCommand
from menu.models import Restaurant, Table, Category


class Command(BaseCommand):
    help = 'Crée un restaurant par défaut et associe toutes les tables et catégories existantes'

    def handle(self, *args, **kwargs):
        # Créer ou récupérer le restaurant par défaut
        restaurant, created = Restaurant.objects.get_or_create(
            slug='default',
            defaults={
                'name': 'Mon Restaurant',
                'description': 'Bienvenue dans notre restaurant',
                'email': 'contact@restaurant.com',
                'phone': '+33 1 23 45 67 89',
                'address': '123 Rue de la Paix',
                'city': 'Paris',
                'postal_code': '75001',
                'country': 'France',
                'primary_color': '#3B82F6',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Restaurant "{restaurant.name}" créé avec succès !'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Restaurant "{restaurant.name}" déjà existant.'))

        # Associer toutes les tables existantes à ce restaurant
        tables_without_restaurant = Table.objects.filter(restaurant__isnull=True)
        table_count = tables_without_restaurant.count()

        if table_count > 0:
            tables_without_restaurant.update(restaurant=restaurant)
            self.stdout.write(self.style.SUCCESS(f'{table_count} table(s) associée(s) au restaurant.'))
        else:
            self.stdout.write('Toutes les tables sont déjà associées à un restaurant.')

        # Associer toutes les catégories existantes à ce restaurant
        categories_without_restaurant = Category.objects.filter(restaurant__isnull=True)
        category_count = categories_without_restaurant.count()

        if category_count > 0:
            categories_without_restaurant.update(restaurant=restaurant)
            self.stdout.write(self.style.SUCCESS(f'{category_count} catégorie(s) associée(s) au restaurant.'))
        else:
            self.stdout.write('Toutes les catégories sont déjà associées à un restaurant.')

        # Afficher les informations
        self.stdout.write(self.style.SUCCESS('\n=== Résumé ==='))
        self.stdout.write(f'Restaurant: {restaurant.name}')
        self.stdout.write(f'Slug: {restaurant.slug}')
        self.stdout.write(f'Tables associées: {restaurant.tables.count()}')
        self.stdout.write(f'Catégories associées: {restaurant.categories.count()}')
        self.stdout.write(f'\nPour modifier les informations du restaurant, allez dans l\'admin Django.')
