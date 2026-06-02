from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from menu.models import Restaurant


class Command(BaseCommand):
    help = 'Crée un groupe de staff restaurant et un utilisateur de démonstration'

    def handle(self, *args, **kwargs):
        # Créer ou récupérer le groupe "Restaurant Staff"
        staff_group, created = Group.objects.get_or_create(name='Restaurant Staff')
        
        if created:
            self.stdout.write(self.style.SUCCESS('Groupe "Restaurant Staff" créé avec succès !'))
        else:
            self.stdout.write(self.style.SUCCESS('Groupe "Restaurant Staff" déjà existant.'))

        # Créer ou récupérer le groupe "Restaurant Manager"
        manager_group, created = Group.objects.get_or_create(name='Restaurant Manager')
        
        if created:
            self.stdout.write(self.style.SUCCESS('Groupe "Restaurant Manager" créé avec succès !'))
        else:
            self.stdout.write(self.style.SUCCESS('Groupe "Restaurant Manager" déjà existant.'))

        # Créer un utilisateur de démonstration s'il n'existe pas
        username = 'staff'
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                password='staff123',
                email='staff@restaurant.com',
                first_name='Staff',
                last_name='User',
                is_staff=True,
                is_superuser=False
            )
            user.groups.add(staff_group)
            self.stdout.write(self.style.SUCCESS(f'\nUtilisateur de démo créé :'))
            self.stdout.write(self.style.SUCCESS(f'  Username: {username}'))
            self.stdout.write(self.style.SUCCESS(f'  Password: staff123'))
            self.stdout.write(self.style.SUCCESS(f'  Groupe: Restaurant Staff'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nUtilisateur "{username}" déjà existant.'))

        # Afficher les informations
        self.stdout.write(self.style.SUCCESS('\n=== Résumé ==='))
        self.stdout.write(self.style.SUCCESS(f'Groupes créés: Restaurant Staff, Restaurant Manager'))
        self.stdout.write(self.style.SUCCESS(f'Utilisateurs dans "Restaurant Staff": {staff_group.user_set.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Utilisateurs dans "Restaurant Manager": {manager_group.user_set.count()}'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Accès à l\'interface ==='))
        self.stdout.write(self.style.SUCCESS('URL de connexion: /staff/login/'))
        self.stdout.write(self.style.SUCCESS('Identifiants: staff / staff123'))
        
        self.stdout.write(self.style.SUCCESS('\nPour ajouter des utilisateurs au groupe:'))
        self.stdout.write(self.style.SUCCESS('1. Allez dans /admin/auth/user/'))
        self.stdout.write(self.style.SUCCESS('2. Sélectionnez un utilisateur'))
        self.stdout.write(self.style.SUCCESS('3. Ajoutez-le au groupe "Restaurant Staff" ou "Restaurant Manager"'))
