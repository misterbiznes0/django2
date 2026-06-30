from django.db import models
from django.contrib.auth.models import User

class PracType(models.Model):
    id_practype = models.AutoField(primary_key=True) 
    type_name = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = 'prac_type'
    
    def __str__(self):
        return self.type_name


class Group(models.Model):
    id_group = models.AutoField(primary_key=True)
    group_name = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = 'groups'
    
    def __str__(self):
        return self.group_name


class Module(models.Model):
    id_module = models.AutoField(primary_key=True)
    module_name = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = 'modules'
    
    def __str__(self):
        return self.module_name


class Spec(models.Model):
    id_spec = models.AutoField(primary_key=True)
    spec_name = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = 'specs'
    
    def __str__(self):
        return self.spec_name


class DataSet(models.Model):
    id = models.AutoField(primary_key=True)
    familia = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    otchestvo = models.TextField(blank=True, null=True)
    
    prac_type = models.ForeignKey(
        PracType, 
        on_delete=models.SET_NULL, 
        db_column='prac_type_id', 
        null=True, 
        blank=True
    )
    module = models.ForeignKey(
        Module, 
        on_delete=models.SET_NULL, 
        db_column='module_id', 
        null=True, 
        blank=True
    )
    specialization = models.ForeignKey(
        Spec, 
        on_delete=models.SET_NULL, 
        db_column='spec_id', 
        null=True, 
        blank=True
    )
    group = models.ForeignKey(
        Group, 
        on_delete=models.SET_NULL, 
        db_column='group_id', 
        null=True, 
        blank=True
    )
    
    kurs = models.IntegerField(blank=True, null=True)
    date_begin = models.TextField(blank=True, null=True)
    date_finish = models.TextField(blank=True, null=True)
    head1 = models.TextField(blank=True, null=True)
    head2 = models.TextField(blank=True, null=True)
    ruc_pract = models.TextField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        db_column='user_id', 
        null=True, 
        blank=True
    )
    hours = models.IntegerField(blank=True, null=True)
    mdk1 = models.TextField(blank=True, null=True)
    mdk2 = models.TextField(blank=True, null=True)
    mdk3 = models.TextField(blank=True, null=True)
    mdk4 = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'data_set'
    
    def __str__(self):
        group_name = self.group.group_name if self.group else ''
        return f"{self.familia} {self.name} {self.otchestvo} - {group_name}"


class DocTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('title', 'Титульный лист'),
        ('diary', 'Дневник отчета'),
        ('task', 'Задание на практику'),
    ]
    
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    file = models.FileField(upload_to='templates/')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'doc_template'
    
    def __str__(self):
        return self.name