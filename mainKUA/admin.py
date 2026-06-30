from django.contrib import admin
from .models import DataSet, PracType, DocTemplate

class DataSetAdmin(admin.ModelAdmin):
    list_display = ['id', 'familia', 'name', 'otchestvo', 'group', 'kurs', 'user']
    list_filter = ['group', 'kurs', 'prac_type']
    search_fields = ['familia', 'name', 'otchestvo', 'group']
    raw_id_fields = ['user']
    fieldsets = (
        ('Личная информация', {
            'fields': ('familia', 'name', 'otchestvo', 'user')
        }),
        ('Информация о практике', {
            'fields': ('prac_type', 'module', 'specialization', 'kurs', 'group')
        }),
        ('Период практики', {
            'fields': ('date_begin', 'date_finish', 'year')
        }),
        ('Руководители', {
            'fields': ('head1', 'head2', 'ruc_pract')
        }),
        ('МДК', {
            'fields': ('mdk1', 'mdk2', 'mdk3', 'mdk4')
        }),
        ('Объем практики', {
            'fields': ('hours',)
        }),
    )

class PracTypeAdmin(admin.ModelAdmin):
    list_display = ['id_practype', 'type_name']
    search_fields = ['type_name']

class DocTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'template_type', 'description', 'is_active')
        }),
        ('Файл шаблона', {
            'fields': ('file',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(DataSet, DataSetAdmin)
admin.site.register(PracType, PracTypeAdmin)
admin.site.register(DocTemplate, DocTemplateAdmin)