from django import forms
from .models import Order, OrderItem, Restaurant


class OrderForm(forms.ModelForm):
    """Formulaire pour créer une commande"""

    class Meta:
        model = Order
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'placeholder': 'Notes pour votre commande (optionnel)',
                'rows': 2,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            })
        }


class OrderItemForm(forms.ModelForm):
    """Formulaire pour ajouter un élément à une commande"""

    class Meta:
        model = OrderItem
        fields = ['quantity', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'min': 1,
                'max': 99,
                'value': 1,
                'class': 'w-16 text-center border border-gray-300 rounded-lg'
            }),
            'notes': forms.TextInput(attrs={
                'placeholder': 'Notes (cuisson, allergènes...)',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm'
            })
        }


class RestaurantProfileForm(forms.ModelForm):
    """Formulaire pour modifier le profil du restaurant (nom bloqué)"""

    class Meta:
        model = Restaurant
        fields = [
            'description', 'email', 'phone', 'website',
            'address', 'city', 'postal_code', 'country',
            'logo', 'banner', 'primary_color',
            'mompay_enabled', 'mompay_merchant_code',
            'vat_enabled', 'vat_rate',
            'bill_notification_repeats', 'voice_notifications_enabled'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'primary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'w-full h-12 border border-gray-300 rounded-lg cursor-pointer'
            }),
            'mompay_enabled': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-500 border-gray-300 rounded focus:ring-blue-500'
            }),
            'mompay_merchant_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: M123456'
            }),
            'vat_enabled': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-500 border-gray-300 rounded focus:ring-blue-500'
            }),
            'vat_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'bill_notification_repeats': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'max': '5'
            }),
            'voice_notifications_enabled': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-500 border-gray-300 rounded focus:ring-blue-500'
            }),
        }
