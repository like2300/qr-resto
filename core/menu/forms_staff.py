from django import forms
from .models import Category, MenuItem


class MenuItemForm(forms.ModelForm):
    """Formulaire pour ajouter un élément au menu"""

    class Meta:
        model = MenuItem
        fields = ['category', 'name', 'description', 'price', 'image', 'is_available']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Nom du plat'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Description du plat (ingrédients, allergènes...)',
                'rows': 4
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '1',
                'min': '0'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-500 border-gray-300 rounded focus:ring-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Changer le label et l'aide pour indiquer que le prix est en FCFA
        self.fields['price'].label = 'Prix (FCFA)'
        self.fields['price'].help_text = 'Prix en Francs CFA (ex: 5000 pour 5000 FCFA)'
        self.fields['price'].widget.attrs['placeholder'] = 'Prix en FCFA'
