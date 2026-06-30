from django import forms
from .models import DataSet

class DataSetForm(forms.ModelForm):
    class Meta:
        model = DataSet
        fields = '__all__'  # Использует все поля модели
        
        # Или перечислите конкретные поля, если нужно:
        # fields = [
        #     'tip', 'fio', 'module', 'specialization', 'kurs', 'group',
        #     'day_begin', 'month_begin', 'year_begin', 'day_finish', 
        #     'month_finish', 'year_finish', 'head1', 'head2', 'ruc_pract',
        #     'year', 'name_org', 'address_org', 'phone_org', 'email_org',
        #     'sphere', 'year_foundation', 'form_ownership', 'history_org',
        #     'godovoy_otchet', 'name_docher', 'address_docher', 'phone_docher',
        #     'email_docher', 'uslugi_org', 'achievments_org', 'name_podrazdel',
        #     'head_podrazdel', 'fio_head_practice', 'kurator_phone', 'kurator_email',
        #     'struk_and_func', 'goal_pract', 'prof_kompetentsii', 'obsh_kompetentsii'
        # ]
        
        # Добавляем виджеты для лучшего отображения (опционально)
        widgets = {
            'tip': forms.Select(choices=[('', 'Выберите тип'), ('Практика', 'Практика'), ('Диплом', 'Диплом')]),
            'kurs': forms.NumberInput(attrs={'class': 'form-control'}),
            'group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: ИС-24'}),
        }