from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from menu.models import Announcement


class Command(BaseCommand):
    help = 'Crée une nouvelle annonce/notification pour les utilisateurs'

    def add_arguments(self, parser):
        parser.add_argument('title', type=str, help="Titre de l'annonce")
        parser.add_argument('message', type=str, help="Message de l'annonce")
        parser.add_argument('--image', type=str, default='', help="Chemin de l'image (optionnel)")
        parser.add_argument('--priority', type=int, default=0, help="Priorité (défaut: 0)")
        parser.add_argument('--days', type=int, default=0, help="Nombre de jours d'affichage (0 = illimité)")

    def handle(self, *args, **options):
        title = options['title']
        message = options['message']
        image = options['image'] if options['image'] else None
        priority = options['priority']
        days = options['days']
        
        # Calculer la date de fin si days > 0
        end_date = None
        if days > 0:
            end_date = timezone.now() + timedelta(days=days)
        
        # Créer l'annonce
        announcement = Announcement.objects.create(
            title=title,
            message=message,
            image=image,
            priority=priority,
            end_date=end_date,
            is_active=True
        )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Annonce "{title}" créée avec succès !'))
        self.stdout.write(self.style.SUCCESS(f'   ID: {announcement.id}'))
        self.stdout.write(self.style.SUCCESS(f'   Priorité: {priority}'))
        if end_date:
            self.stdout.write(self.style.SUCCESS(f'   Fin: {end_date.strftime("%d/%m/%Y à %H:%M")}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'   Fin: Illimitée'))
        
        self.stdout.write(self.style.WARNING('\n⚠️  Les utilisateurs verront cette annonce au prochain chargement'))
        self.stdout.write(self.style.WARNING('   (sauf s\'ils ont déjà fermé une annonce précédente)'))
