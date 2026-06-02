from django.core.management.base import BaseCommand
from menu.models import AdminTheme


class Command(BaseCommand):
    help = "Crée le thème admin par défaut"

    def handle(self, *args, **kwargs):
        self.stdout.write("Création du thème admin par défaut...")

        theme, created = AdminTheme.objects.get_or_create(
            name="Thème Principal",
            defaults={
                "theme_mode": "light",
                "primary_color": "#3B82F6",
                "primary_hover": "#2563EB",
                "primary_light": "#DBEAFE",
                "sidebar_bg": "#1E293B",
                "sidebar_bg_gradient": "#0F172A",
                "sidebar_text": "#F8FAFC",
                "bg_color": "#F9FAFB",
                "card_bg": "#FFFFFF",
                "text_primary": "#1F2937",
                "text_secondary": "#6B7280",
                "success_color": "#10B981",
                "warning_color": "#F59E0B",
                "danger_color": "#EF4444",
                "info_color": "#3B82F6",
                "border_color": "#E5E7EB",
                "border_radius": 8,
                "is_active": True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS("✓ Thème admin créé avec succès !")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠ Le thème existe déjà.")
            )
