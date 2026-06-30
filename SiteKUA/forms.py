from django import forms
from .models import data_set

class DataSetForm(forms.ModelForm):
    class Meta:
        model = data_set
        fields = '__all__'  # или перечислите нужные поля
        widgets = {
            'tip': forms.Select(choices=[('Учебной', 'Учебной'), ('Практической', 'Практической')]),
            'day_begin': forms.NumberInput(attrs={'type': 'number'}),
            'day_finish': forms.NumberInput(attrs={'type': 'number'}),
            'year_begin': forms.NumberInput(attrs={'type': 'number'}),
            'year_finish': forms.NumberInput(attrs={'type': 'number'}),
            'kurs': forms.NumberInput(attrs={'type': 'number'}),
        }