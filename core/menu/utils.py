import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.contrib import messages


def generate_qr_code(table, request=None):
    """Génère un QR code pour une table"""
    from django.conf import settings
    
    # Construire l'URL complète
    domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
    menu_url = f"http://{domain}/m/{table.uuid}/"
    
    # Créer le QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(menu_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Sauvegarder dans un buffer
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer, menu_url


def generate_qr_code_for_table(table):
    """Génère et attache un QR code à une table"""
    buffer, _ = generate_qr_code(table)
    
    # Sauvegarder le fichier
    filename = f'qr_tables/table_{table.uuid}.png'
    table.qr_code.save(filename, ContentFile(buffer.getvalue()), save=True)
    
    return table.qr_code.url
