from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import DataSet, PracType, DocTemplate, Group, Module, Spec
from docxtpl import DocxTemplate
import os
import tempfile
import time
import re
from datetime import datetime


# ==================== ФУНКЦИИ СКЛОНЕНИЯ ФИО ====================

def decline_fio_genitive(familia, name, otchestvo):
    """Склонение ФИО в родительный падеж (кого?) - Кульковой Ульяны Андреевны"""
    
    def decline_familia(f):
        if not f:
            return ''
        if f.endswith('а'):
            return f[:-1] + 'ой'
        if f.endswith('я'):
            return f[:-1] + 'ой'
        if f.endswith('ва'):
            return f[:-2] + 'вой'
        if f.endswith('на'):
            return f[:-2] + 'ной'
        if f.endswith('ий'):
            return f[:-2] + 'его'
        if f.endswith('ый'):
            return f[:-2] + 'ого'
        if f.endswith('ой'):
            return f[:-2] + 'ого'
        if f.endswith('ь'):
            return f[:-1] + 'я'
        if f[-1] in 'бвгджзйклмнпрстфхцчшщ':
            return f + 'а'
        return f
    
    def decline_name(n):
        if not n:
            return ''
        if n.endswith('а'):
            return n[:-1] + 'ы'
        if n.endswith('я'):
            return n[:-1] + 'и'
        if n.endswith('й'):
            return n[:-1] + 'я'
        if n.endswith('ь'):
            return n[:-1] + 'я'
        if n[-1] in 'бвгджзйклмнпрстфхцчшщ':
            return n + 'а'
        return n
    
    def decline_otchestvo(o):
        if not o:
            return ''
        if o.endswith('на'):
            return o[:-2] + 'ны'
        if o.endswith('вна'):
            return o[:-3] + 'вны'
        if o.endswith('чна'):
            return o[:-3] + 'чны'
        if o.endswith('ч'):
            return o + 'а'
        if o.endswith('й'):
            return o[:-1] + 'я'
        if o.endswith('а'):
            return o[:-1] + 'ы'
        return o + 'а'
    
    fam = decline_familia(familia)
    nam = decline_name(name)
    otch = decline_otchestvo(otchestvo)
    
    result_parts = []
    if fam:
        result_parts.append(fam)
    if nam:
        result_parts.append(nam)
    if otch:
        result_parts.append(otch)
    
    return ' '.join(result_parts)


def decline_fio_dative(familia, name, otchestvo):
    """Склонение ФИО в дательный падеж (кому?) - Кульковой Ульяне Андреевне"""
    
    def decline_familia_dative(f):
        if not f:
            return ''
        if f.endswith('а'):
            return f[:-1] + 'ой'
        if f.endswith('я'):
            return f[:-1] + 'ой'
        if f.endswith('ва'):
            return f[:-2] + 'вой'
        if f.endswith('на'):
            return f[:-2] + 'ной'
        if f.endswith('ий'):
            return f[:-2] + 'ему'
        if f.endswith('ый'):
            return f[:-2] + 'ому'
        if f.endswith('ой'):
            return f[:-2] + 'ому'
        if f.endswith('ь'):
            return f[:-1] + 'ю'
        if f[-1] in 'бвгджзйклмнпрстфхцчшщ':
            return f + 'у'
        return f
    
    def decline_name_dative(n):
        if not n:
            return ''
        if n.endswith('а'):
            return n[:-1] + 'е'
        if n.endswith('я'):
            return n[:-1] + 'е'
        if n.endswith('й'):
            return n[:-1] + 'ю'
        if n.endswith('ь'):
            return n[:-1] + 'ю'
        if n[-1] in 'бвгджзйклмнпрстфхцчшщ':
            return n + 'у'
        return n
    
    def decline_otchestvo_dative(o):
        if not o:
            return ''
        if o.endswith('на'):
            return o[:-2] + 'не'
        if o.endswith('вна'):
            return o[:-3] + 'вне'
        if o.endswith('чна'):
            return o[:-3] + 'чне'
        if o.endswith('ч'):
            return o + 'у'
        if o.endswith('й'):
            return o[:-1] + 'ю'
        if o.endswith('а'):
            return o[:-1] + 'е'
        return o + 'у'
    
    fam = decline_familia_dative(familia)
    nam = decline_name_dative(name)
    otch = decline_otchestvo_dative(otchestvo)
    
    result_parts = []
    if fam:
        result_parts.append(fam)
    if nam:
        result_parts.append(nam)
    if otch:
        result_parts.append(otch)
    
    return ' '.join(result_parts)


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def format_date_for_title(date_str):
    """Форматирует дату для титульного листа: '2' декабря 2025"""
    if not date_str:
        return ''
    
    try:
        parts = date_str.split('.')
        if len(parts) != 3:
            return date_str
        
        day = str(int(parts[0]))
        month_num = parts[1]
        year = parts[2]
        
        months = {
            '01': 'января', '02': 'февраля', '03': 'марта', '04': 'апреля',
            '05': 'мая', '06': 'июня', '07': 'июля', '08': 'августа',
            '09': 'сентября', '10': 'октября', '11': 'ноября', '12': 'декабря'
        }
        
        month_name = months.get(month_num, month_num)
        
        return f'"{day}" {month_name} {year}'
    
    except Exception:
        return date_str


def extract_module_code(module_full_name):
    """Извлекает код модуля (ПМ.08, ПМд.13 и т.д.) из полного названия"""
    if not module_full_name:
        return ''
    
    # Ищем паттерн ПМ.xx или ПМд.xx или ПМ. xx (с пробелом)
    match = re.match(r'(ПМ[д]?\.?\s*\d+)', module_full_name, re.IGNORECASE)
    if match:
        # Убираем пробелы
        return match.group(1).replace(' ', '')
    
    # Если не нашли, берем первые 8 символов
    return module_full_name[:8] if len(module_full_name) > 8 else module_full_name


def underline_if_empty(value, length=8):
    """Заменяет пустое значение на подчеркивания"""
    if value is None:
        return '_' * length
    value_str = str(value).strip()
    if not value_str:
        return '_' * length
    return value_str


# ==================== АУТЕНТИФИКАЦИЯ ====================

def register(request):
    if request.method == "GET":
        return render(request, "register.html", {"form": UserCreationForm()})
    else:
        if request.POST['password1'] == request.POST['password2']:
            user = User.objects.create_user(
                request.POST['username'],
                password=request.POST['password1']
            )
            user.save()
            DataSet.objects.create(user=user)
            login(request, user)
            return redirect('/profile/')
        else:
            messages.error(request, 'Пароли не совпадают')
            return render(request, "register.html", {"form": UserCreationForm()})


def loginf(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Вы вошли как {username}')
                return redirect('/profile/')
            else:
                messages.error(request, 'Неправильное имя пользователя или пароль')
        else:
            messages.error(request, 'Неправильное имя пользователя или пароль')

    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logoutf(request):
    logout(request)
    return redirect('/login/')


# ==================== ПРОФИЛЬ (ОСНОВНАЯ СТРАНИЦА) ====================

@login_required
def profile(request):
    user_report = DataSet.objects.filter(user=request.user).first()
    
    if not user_report:
        user_report = DataSet.objects.create(user=request.user)

    if request.method == 'POST':
        if 'generate_title' in request.POST:
            return generate_title_document(request, user_report)
        if 'generate_diary' in request.POST:
            return generate_diary_document(request, user_report)
        if 'generate_task' in request.POST:
            return generate_task_document(request, user_report)

        # === Текстовые поля ===
        user_report.familia = request.POST.get('familia', '').strip() or None
        user_report.name = request.POST.get('name', '').strip() or None
        user_report.otchestvo = request.POST.get('otchestvo', '').strip() or None
        
        # === Тип практики (внешний ключ) ===
        tip_value = request.POST.get('tip', '')
        if tip_value:
            try:
                user_report.prac_type = PracType.objects.get(type_name=tip_value)
            except PracType.DoesNotExist:
                user_report.prac_type = None
        else:
            user_report.prac_type = None
        
        # === Модуль (внешний ключ, создаем если нет) ===
        module_value = request.POST.get('module', '').strip()
        if module_value:
            module_obj, created = Module.objects.get_or_create(module_name=module_value)
            user_report.module = module_obj
        else:
            user_report.module = None
        
        # === Специальность (внешний ключ, создаем если нет) ===
        spec_value = request.POST.get('specialization', '').strip()
        if spec_value:
            spec_obj, created = Spec.objects.get_or_create(spec_name=spec_value)
            user_report.specialization = spec_obj
        else:
            user_report.specialization = None
        
        # === Группа (внешний ключ, создаем если нет) ===
        group_value = request.POST.get('group', '').strip()
        if group_value:
            group_obj, created = Group.objects.get_or_create(group_name=group_value)
            user_report.group = group_obj
        else:
            user_report.group = None
        
        # === Курс ===
        kurs_value = request.POST.get('kurs', '')
        user_report.kurs = int(kurs_value) if kurs_value and kurs_value.isdigit() else None
        
        # === Даты (формат: DD.MM.YYYY) ===
        begin_date = request.POST.get('begin_date', '')
        if begin_date:
            date_parts = begin_date.split('-')
            if len(date_parts) == 3:
                user_report.date_begin = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
            else:
                user_report.date_begin = None
        else:
            user_report.date_begin = None
        
        finish_date = request.POST.get('finish_date', '')
        if finish_date:
            date_parts = finish_date.split('-')
            if len(date_parts) == 3:
                user_report.date_finish = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
            else:
                user_report.date_finish = None
        else:
            user_report.date_finish = None
        
        # === Руководители ===
        user_report.head1 = request.POST.get('head1', '').strip() or None
        user_report.head2 = request.POST.get('head2', '').strip() or None
        user_report.ruc_pract = request.POST.get('ruc_pract', '').strip() or None
        
        # === Год ===
        year_value = request.POST.get('year', '')
        user_report.year = int(year_value) if year_value and year_value.isdigit() else None
        
        # === Часы ===
        hours_value = request.POST.get('hours', '')
        user_report.hours = int(hours_value) if hours_value and hours_value.isdigit() else None
        
        # === МДК ===
        user_report.mdk1 = request.POST.get('mdk1', '').strip() or None
        user_report.mdk2 = request.POST.get('mdk2', '').strip() or None
        user_report.mdk3 = request.POST.get('mdk3', '').strip() or None
        user_report.mdk4 = request.POST.get('mdk4', '').strip() or None

        user_report.save()
        messages.success(request, 'Данные сохранены!')
        return redirect('/profile/')

    # === Форматирование дат для input type="date" ===
    begin_date_for_input = ''
    finish_date_for_input = ''

    if user_report.date_begin:
        try:
            parts = user_report.date_begin.split('.')
            if len(parts) == 3:
                begin_date_for_input = f"{parts[2]}-{parts[1]}-{parts[0]}"
        except:
            pass

    if user_report.date_finish:
        try:
            parts = user_report.date_finish.split('.')
            if len(parts) == 3:
                finish_date_for_input = f"{parts[2]}-{parts[1]}-{parts[0]}"
        except:
            pass

    # === Данные для выпадающих списков ===
    prac_types = PracType.objects.all()
    groups = Group.objects.all()
    modules = Module.objects.all()
    specializations = Spec.objects.all()

    # === Проверка наличия шаблонов ===
    has_title_template = DocTemplate.objects.filter(template_type='title', is_active=True).exists()
    has_diary_template = DocTemplate.objects.filter(template_type='diary', is_active=True).exists()
    has_task_template = DocTemplate.objects.filter(template_type='task', is_active=True).exists()

    return render(request, "profile.html", {
        "user_report": user_report,
        "prac_types": prac_types,
        "groups": groups,
        "modules": modules,
        "specializations": specializations,
        "begin_date_for_input": begin_date_for_input,
        "finish_date_for_input": finish_date_for_input,
        "has_title_template": has_title_template,
        "has_diary_template": has_diary_template,
        "has_task_template": has_task_template,
    })


# ==================== ГЕНЕРАЦИЯ ТИТУЛЬНОГО ЛИСТА ====================

def generate_title_document(request, user_report):
    temp_file_path = None
    try:
        template = DocTemplate.objects.get(template_type='title', is_active=True)

        # Тип практики
        if user_report.prac_type and user_report.prac_type.type_name == 'Учебная':
            practice_type = "УЧЕБНОЙ"
        else:
            practice_type = "ПРОИЗВОДСТВЕННОЙ"

        # Склонение ФИО
        fio_genitive = decline_fio_genitive(
            user_report.familia or '',
            user_report.name or '',
            user_report.otchestvo or ''
        )

        # Форматирование дат
        date_begin_formatted = format_date_for_title(user_report.date_begin or '')
        date_finish_formatted = format_date_for_title(user_report.date_finish or '')

        # Получение значений из связанных таблиц
        module_name = user_report.module.module_name if user_report.module else ''
        spec_name = user_report.specialization.spec_name if user_report.specialization else ''
        group_name = user_report.group.group_name if user_report.group else ''

        context = {
            'tip': practice_type,
            'fio': fio_genitive,
            'module': underline_if_empty(module_name, 8),
            'specialization': underline_if_empty(spec_name, 8),
            'kurs': user_report.kurs or '',
            'group': underline_if_empty(group_name, 8),
            'date_begin': date_begin_formatted,
            'date_finish': date_finish_formatted,
            'head1': underline_if_empty(user_report.head1, 8),
            'head2': underline_if_empty(user_report.head2, 8),
            'ruc_pract': underline_if_empty(user_report.ruc_pract, 8),
            'year': user_report.year or datetime.now().year,
        }

        doc = DocxTemplate(template.file.path)
        doc.render(context)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_file_path = temp_file.name
        temp_file.close()

        doc.save(temp_file_path)
        time.sleep(0.1)

        with open(temp_file_path, 'rb') as f:
            file_content = f.read()

        try:
            os.remove(temp_file_path)
        except:
            pass

        filename = f"{user_report.familia}_{user_report.name}_Титульный_лист_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

        response = HttpResponse(file_content, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        messages.success(request, 'Титульный лист успешно сгенерирован!')
        return response

    except DocTemplate.DoesNotExist:
        messages.error(request, 'Шаблон титульного листа не найден')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

    return redirect('/profile/')


# ==================== ГЕНЕРАЦИЯ ДНЕВНИКА ====================

def generate_diary_document(request, user_report):
    temp_file_path = None
    try:
        template = DocTemplate.objects.get(template_type='diary', is_active=True)

        # Тип практики (ВСЕ БУКВЫ ЗАГЛАВНЫЕ)
        if user_report.prac_type and user_report.prac_type.type_name == 'Учебная':
            practice_type = "УЧЕБНОЙ"
        else:
            practice_type = "ПРОИЗВОДСТВЕННОЙ"

        # Склонение ФИО
        fio_genitive = decline_fio_genitive(
            user_report.familia or '',
            user_report.name or '',
            user_report.otchestvo or ''
        )

        # Получение значений из связанных таблиц
        module_name = user_report.module.module_name if user_report.module else ''
        module_short = extract_module_code(module_name)
        
        spec_name = user_report.specialization.spec_name if user_report.specialization else ''
        group_name = user_report.group.group_name if user_report.group else ''

        context = {
            'tip': practice_type,
            'familia': user_report.familia or '',
            'name': user_report.name or '',
            'otchestvo': user_report.otchestvo or '',
            'fio': fio_genitive,
            'kurs': user_report.kurs or '',
            'group': group_name,
            'specialization': spec_name,
            'module': module_short,
            'module_full': module_name,
            'head1': user_report.head1 or '',
            'head2': user_report.head2 or '',
            'ruc_pract': user_report.ruc_pract or '',
            'mdk1': user_report.mdk1 or '',
            'mdk2': user_report.mdk2 or '',
            'mdk3': user_report.mdk3 or '',
            'mdk4': user_report.mdk4 or '',
            'hours': user_report.hours or '',
            'year': user_report.year or datetime.now().year,
        }

        doc = DocxTemplate(template.file.path)
        doc.render(context)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_file_path = temp_file.name
        temp_file.close()

        doc.save(temp_file_path)
        time.sleep(0.1)

        with open(temp_file_path, 'rb') as f:
            file_content = f.read()

        try:
            os.remove(temp_file_path)
        except:
            pass

        filename = f"{user_report.familia}_{user_report.name}_Дневник_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

        response = HttpResponse(file_content, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        messages.success(request, 'Дневник успешно сгенерирован!')
        return response

    except DocTemplate.DoesNotExist:
        messages.error(request, 'Шаблон дневника не найден')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

    return redirect('/profile/')


# ==================== ГЕНЕРАЦИЯ ЗАДАНИЯ ====================

def generate_task_document(request, user_report):
    temp_file_path = None
    try:
        template = DocTemplate.objects.get(template_type='task', is_active=True)

        # Тип практики
        if user_report.prac_type and user_report.prac_type.type_name == 'Учебная':
            practice_type_first = "учебную"
            practice_type_second = "учебной"
        else:
            practice_type_first = "производственную"
            practice_type_second = "производственной"

        # Склонение ФИО в дательный падеж
        fio_dative = decline_fio_dative(
            user_report.familia or '',
            user_report.name or '',
            user_report.otchestvo or ''
        )

        # Получение значений из связанных таблиц
        module_name = user_report.module.module_name if user_report.module else ''
        spec_name = user_report.specialization.spec_name if user_report.specialization else ''
        group_name = user_report.group.group_name if user_report.group else ''

        context = {
            'tip': practice_type_first,
            'tip2': practice_type_second,
            'fio_dative': fio_dative,
            'familia': user_report.familia or '',
            'name': user_report.name or '',
            'otchestvo': user_report.otchestvo or '',
            'group': group_name,
            'kurs': user_report.kurs or '',
            'specialization': spec_name,
            'module': module_name,
            'mdk1': user_report.mdk1 or '',
            'mdk2': user_report.mdk2 or '',
            'mdk3': user_report.mdk3 or '',
            'mdk4': user_report.mdk4 or '',
            'hours': user_report.hours or '',
            'date_begin': user_report.date_begin or '',
            'date_finish': user_report.date_finish or '',
            'head1': user_report.head1 or '',
            'year': user_report.year or datetime.now().year,
        }

        doc = DocxTemplate(template.file.path)
        doc.render(context)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_file_path = temp_file.name
        temp_file.close()

        doc.save(temp_file_path)
        time.sleep(0.1)

        with open(temp_file_path, 'rb') as f:
            file_content = f.read()

        try:
            os.remove(temp_file_path)
        except:
            pass

        filename = f"{user_report.familia}_{user_report.name}_Задание_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

        response = HttpResponse(file_content, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        messages.success(request, 'Задание успешно сгенерировано!')
        return response

    except DocTemplate.DoesNotExist:
        messages.error(request, 'Шаблон задания не найден')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

    return redirect('/profile/')