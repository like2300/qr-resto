from django.core.management.base import BaseCommand
from menu.models import MenuItem
from decimal import Decimal


class Command(BaseCommand):
    help = 'Convertit les prix des éléments du menu d\'EUR vers FCFA'

    def handle(self, *args, **kwargs):
        exchange_rate = Decimal('655.957')
        
        items = MenuItem.objects.all()
        converted_count = 0
        
        self.stdout.write(f'Conversion de {items.count()} éléments du menu...')
        self.stdout.write(f'Taux de conversion: 1 EUR = {exchange_rate} FCFA\n')
        
        for item in items:
            old_price = item.price
            # Convertir EUR -> FCFA (arrondi à l'entier le plus proche)
            new_price = int(float(old_price) * float(exchange_rate))
            item.price = Decimal(str(new_price))
            item.save()
            converted_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ {item.name}: {old_price}€ → {new_price} FCFA'
                )
            )
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{converted_count} élément(s) converti(s) avec succès !'
        ))
        self.stdout.write(self.style.WARNING(
            '\n⚠️ Les prix sont maintenant en FCFA. Assurez-vous que votre site affiche la bonne devise.'
        ))
