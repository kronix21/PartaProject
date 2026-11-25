from django.template.response import TemplateResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Equipment, Repair, Employee, Cabinet, EquipmentType, Movement, WriteOffAct, Profile
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .decorators import role_required
from django.core.exceptions import ValidationError

import logging

logger = logging.getLogger('app')

def index(request):
    profile = None
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)

    context = {
        'profile': profile,
    }
    return TemplateResponse(request, 'index.html', context)

@role_required(['user', 'technician', 'accountant'])
@login_required(login_url='signin')
def profile(request):
    profile_obj, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        profile_obj.phone = request.POST.get('phone', '')
        
        if request.FILES.get('avatar'):
            profile_obj.avatar = request.FILES.get('avatar')
        
        profile_obj.save()
        return redirect('profile')
    
    context = {
        'profile': profile_obj,
    }
    return TemplateResponse(request, 'profile.html', context)

@role_required(['user', 'technician', 'accountant'])
def equipment(request, pk):
    profile = None
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)

    cabinets = Cabinet.objects.all()
    item = get_object_or_404(Equipment, pk=pk) 
    movements = item.movements.all().order_by('-date')
    employees = Employee.objects.all()
    context = {
        'item': item,
        'movements': movements,
        'cabinets': cabinets,
        'employees': employees,
        'profile': profile,
    }
    return TemplateResponse(request, 'equipment.html', context)

def move_equipment(request, pk):
    if request.method != 'POST':
        return redirect('equipment', pk=pk)

    item = get_object_or_404(Equipment, pk=pk)

    if item.status == 'written_off':
        messages.error(request, "Перемещение списанного оборудования запрещено.")
        logger.warning(f"Попытка перемещения списанного | id={item.pk} | user={request.user.username}")
        return redirect('equipment', pk=item.pk)

    date_str = request.POST.get('date')
    to_cabinet_id = request.POST.get('to_cabinet')
    to_responsible_id = request.POST.get('to_responsible') or item.responsible_id
    reason = (request.POST.get('reason') or '').strip()

    errors = []
    if not date_str:
        errors.append("Укажите дату перемещения.")
    if not to_cabinet_id:
        errors.append("Выберите кабинет назначения.")
    if not reason:
        errors.append("Укажите причину перемещения.")

    if errors:
        for err in errors:
            messages.error(request, err)
        logger.warning(f"Ошибка перемещения (валидация) | id={item.pk} | {errors}")
        return redirect('equipment', pk=item.pk)

    try:
        Movement.objects.create(
            equipment=item,
            date=date_str,
            from_cabinet=item.cabinet,
            to_cabinet_id=to_cabinet_id,
            from_responsible=item.responsible,
            to_responsible_id=to_responsible_id,
            reason=reason,
        )
        item.cabinet_id = to_cabinet_id
        if to_responsible_id:
            item.responsible_id = to_responsible_id
        item.full_clean()
        item.save()
        logger.info(f"Перемещение | id={item.pk} | to_cabinet={to_cabinet_id} | user={request.user.username}")
    except ValidationError as e:
        for msg in e.messages:
            messages.error(request, msg)
        logger.warning(f"Ошибка валидации при перемещении | id={item.pk} | {e.messages}")
        return redirect('equipment', pk=item.pk)
    except Exception as e:
        logger.error(f"Ошибка при перемещении | id={item.pk} | {e}", exc_info=True)
        messages.error(request, f"Не удалось выполнить перемещение: {e}")
        return redirect('equipment', pk=item.pk)

    messages.success(request, "Оборудование успешно перемещено.")
    return redirect('equipment', pk=item.pk)
    
@role_required(['accountant'])
def write_off_equipment(request, pk):
    item = get_object_or_404(Equipment, pk=pk)

    if item.status == 'written_off':
        messages.error(request, "Оборудование уже списано.")
        logger.warning(f"Повторное списание | id={item.pk}")
        return redirect('equipment', pk=item.pk)

    try:
        WriteOffAct.objects.create(
            act_number=request.POST.get('act_number'),
            date=request.POST.get('date') or timezone.now().date(),
            reason=request.POST.get('reason'),
            basis=request.POST.get('basis'),
            equipment=item
        )
        logger.info(f"Списание оборудования | id={item.pk} | inv={item.inventory_number} | user={request.user.username}")
        messages.success(request, "Оборудование списано.")
    except Exception as e:
        logger.error(f"Ошибка при списании | id={item.pk} | {e}", exc_info=True)
        messages.error(request, "Не удалось списать оборудование.")

    return redirect('equipment', pk=item.pk)
    
@role_required(['technician'])
def create_repair(request, pk):
    item = get_object_or_404(Equipment, pk=pk)

    if item.status == 'written_off':
        messages.error(request, "Создание ремонта для списанного оборудования запрещено.")
        logger.warning(f"Попытка ремонта списанного | id={item.pk}")
        return redirect('equipment', pk=item.pk)

    technician_id = request.POST.get('technician')
    description = (request.POST.get('description') or '').strip()

    if not technician_id or not description:
        messages.error(request, "Укажите техника и описание неисправности.")
        logger.warning(f"Ошибка создания ремонта (валидация) | id={item.pk}")
        return redirect('equipment', pk=item.pk)

    try:
        Repair.objects.create(
            equipment=item,
            request_date=request.POST.get('date') or timezone.now().date(),
            description=description,
            technician_id=technician_id,
            status='in_progress'
        )
        item.status = 'repair'
        item.save()
        logger.info(f"Создан ремонт | equipment={item.pk} | technician={technician_id} | user={request.user.username}")
        messages.success(request, "Заявка на ремонт создана.")
    except Exception as e:
        logger.error(f"Ошибка при создании ремонта | id={item.pk} | {e}", exc_info=True)
        messages.error(request, "Не удалось создать заявку на ремонт.")

    return redirect('equipment', pk=item.pk)

@role_required(['user', 'accountant'])
def add_equipment(request):
    profile = None
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)

    cabinets = Cabinet.objects.all()
    types = EquipmentType.objects.all()
    employees = Employee.objects.all()

    context = {
        'cabinets': cabinets,
        'types': types,
        'employees': employees,
        'profile': profile,
    }
    return TemplateResponse(request, 'add_equipment.html', context)

@role_required(['user', 'accountant'])
def add(request):
    if request.method != 'POST':
        return redirect('add_equipment')

    photo = request.FILES.get('photo')
    inventory_number = (request.POST.get('inventory_number') or '').strip()
    name = (request.POST.get('name') or '').strip()
    serial_number = (request.POST.get('serial_number') or '').strip()
    cabinet_id = request.POST.get('cabinet')
    type_id = request.POST.get('type')
    model = (request.POST.get('model') or '').strip()
    purchase_date = request.POST.get('purchase_date')
    status = request.POST.get('status')
    responsible_id = request.POST.get('responsible')

    errors = []

    required = {
        'inventory_number': inventory_number,
        'name': name,
        'serial_number': serial_number,
        'model': model,
        'purchase_date': purchase_date,
        'status': status,
        'type': type_id,
    }
    if any(not v for v in required.values()):
        errors.append("Заполните все обязательные поля.")

    if inventory_number and Equipment.objects.filter(inventory_number=inventory_number).exists():
        errors.append("Оборудование с таким инвентарным номером уже существует.")

    if serial_number and Equipment.objects.filter(serial_number=serial_number).exists():
        errors.append("Оборудование с таким серийным номером уже существует.")

    valid_statuses = ['working', 'repair', 'written_off']
    if status and status not in valid_statuses:
        errors.append("Недопустимый статус оборудования.")

    if errors:
        for err in errors:
            messages.error(request, err)
        logger.warning(f"Ошибка добавления оборудования | user={request.user.username} | errors={errors}")
        return redirect('add_equipment')

    try:
        equipment = Equipment(
            inventory_number=inventory_number,
            name=name,
            serial_number=serial_number,
            model=model,
            purchase_date=purchase_date,
            status=status,
            cabinet_id=cabinet_id or None,
            type_id=type_id,
            responsible_id=responsible_id or None,
        )
        if photo:
            equipment.photo = photo

        equipment.full_clean()
        equipment.save()
        logger.info(f"Добавлено оборудование | id={equipment.pk} | inv={inventory_number} | user={request.user.username}")
    except ValidationError as e:
        for msg in e.messages:
            messages.error(request, msg)
        logger.warning(f"Ошибка валидации при добавлении | inv={inventory_number} | {e.messages}")
        return redirect('add_equipment')
    except Exception as e:
        logger.error(f"Ошибка при добавлении оборудования | inv={inventory_number} | {e}", exc_info=True)
        messages.error(request, "Не удалось сохранить оборудование.")
        return redirect('add_equipment')

    return redirect('catalog')

def catalog(request):
    profile = None
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)

    query = request.GET.get('search', '')
    status = request.GET.get('status', '')

    equipment_list = Equipment.objects.all()

    if query:
        equipment_list = equipment_list.filter(
            Q(name__icontains=query) | Q(inventory_number__icontains=query)
        )

    if status:
        equipment_list = equipment_list.filter(status=status)

    paginator = Paginator(equipment_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'profile': profile,
    }
    return TemplateResponse(request, 'catalog.html', context)

@role_required(['accountant'])
def edit(request, pk):
    profile = None
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)

    item = get_object_or_404(Equipment, pk=pk)
    
    context = {
        'item': item,
        'cabinets': Cabinet.objects.all(),
        'types': EquipmentType.objects.all(),
        'employees': Employee.objects.all(),
        'profile': profile,
    }
    return TemplateResponse(request, 'edit.html', context)

@role_required(['accountant'])
def save_edit(request, pk):
    item = get_object_or_404(Equipment, pk=pk)

    try:
        item.inventory_number = request.POST.get('inventory_number')
        item.name = request.POST.get('name')
        item.serial_number = request.POST.get('serial_number')
        item.model = request.POST.get('model')
        item.purchase_date = request.POST.get('purchase_date')
        item.status = request.POST.get('status')
        item.cabinet_id = request.POST.get('cabinet')
        item.type_id = request.POST.get('type')
        item.responsible_id = request.POST.get('responsible')
        if request.FILES.get('photo'):
            item.photo = request.FILES.get('photo')

        item.full_clean()
        item.save()
        logger.info(f"Отредактировано оборудование | id={item.pk} | inv={item.inventory_number} | user={request.user.username}")
    except ValidationError as e:
        for msg in e.messages:
            messages.error(request, msg)
        logger.warning(f"Ошибка валидации при редактировании | id={item.pk} | {e.messages}")
        return redirect('edit', pk=item.pk)
    except Exception as e:
        logger.error(f"Ошибка при редактировании | id={item.pk} | {e}", exc_info=True)
        messages.error(request, "Не удалось сохранить изменения.")
        return redirect('edit', pk=item.pk)

    return redirect('equipment', pk=item.pk)

@role_required(['technician'])
def repairs(request):
    profile = None
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)

    repairs_list = Repair.objects.filter(status='in_progress').select_related('equipment', 'technician')
    paginator = Paginator(repairs_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    employees = Employee.objects.all()

    context = {
        'page_obj': page_obj,
        'employees': employees,
        'profile': profile,
    }
    return TemplateResponse(request, 'repairs.html', context)

@role_required(['technician'])
def close_repair(request):
    repair_id = request.POST.get('repair_id')
    technician_id = request.POST.get('technician')
    result_text = (request.POST.get('result') or '').strip()
    new_status = request.POST.get('status')

    repair = get_object_or_404(Repair, id=repair_id)

    if not result_text:
        messages.error(request, "Укажите результат ремонта.")
        logger.warning(f"Ошибка снятия с ремонта (нет результата) | repair={repair_id}")
        return redirect('repairs')

    try:
        repair.technician_id = technician_id
        repair.result = result_text
        repair.status = new_status
        repair.save()

        if new_status == 'completed':
            repair.equipment.status = 'working'
            repair.equipment.save()

        logger.info(f"Ремонт закрыт | repair={repair_id} | status={new_status} | user={request.user.username}")
        messages.success(request, "Ремонт закрыт.")
    except Exception as e:
        logger.error(f"Ошибка при закрытии ремонта | repair={repair_id} | {e}", exc_info=True)
        messages.error(request, "Не удалось закрыть ремонт.")

    return redirect('repairs')

def signin_staff(request):
    return TemplateResponse(request, 'signin_staff.html')

def signin(request):
    return TemplateResponse(request, 'signin.html')

def auth(request):
    if request.method != 'POST':
        return redirect('signin')

    phone = request.POST.get('phone', '').strip()
    password = request.POST.get('password', '')

    errors = []

    if not phone:
        errors.append("Введите номер телефона.")
    else:
        phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        phone_pattern = re.compile(r'^(\+7|8|7)\d{10}$')
        if not phone_pattern.match(phone_clean):
            errors.append("Неверный формат телефона. Пример: +79001234567.")

    if not password:
        errors.append("Введите пароль.")

    if errors:
        for err in errors:
            messages.error(request, err)
        logger.warning(f"Неудачная попытка входа (валидация) | phone={phone} | IP={request.META.get('REMOTE_ADDR')}")
        return redirect('signin')

    user = authenticate(request, username=phone, password=password)

    if user is not None:
        login(request, user)
        logger.info(f"Вход в систему | user={user.username} | role={user.profile.role} | IP={request.META.get('REMOTE_ADDR')}")
        return redirect('profile')
    else:
        messages.error(request, "Неверный телефон или пароль.")
        logger.warning(f"Неудачная попытка входа (неверный пароль) | phone={phone} | IP={request.META.get('REMOTE_ADDR')}")
        return redirect('signin')

def signup_staff(request):
    return TemplateResponse(request, 'signup_staff.html')

def signup(request):
    return TemplateResponse(request, 'signup.html')

def add_user(request):
    if request.method != 'POST':
        return redirect('signup')

    phone = request.POST.get('phone', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    password_confirm = request.POST.get('password_confirm', '')

    errors = []

    phone_pattern = re.compile(r'^(\+7|8|7)?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$')
    if not phone:
        errors.append("Введите номер телефона.")
    elif not phone_pattern.match(phone):
        errors.append("Неверный формат номера телефона. Пример: +79001234567 или 89001234567.")

    if not email:
        errors.append("Введите email.")
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors.append("Неверный формат email.")

    if not password:
        errors.append("Введите пароль.")
    elif len(password) < 8:
        errors.append("Пароль должен содержать минимум 8 символов.")
    elif not re.search(r'\d', password):
        errors.append("Пароль должен содержать хотя бы одну цифру.")

    if User.objects.filter(username=phone).exists():
        errors.append("Пользователь с таким номером телефона уже существует.")

    if errors:
        for err in errors:
            messages.error(request, err)
        logger.warning(f"Ошибка регистрации | phone={phone} | errors={errors}")
        return render(request, 'signup.html')

    try:
        user = User.objects.create_user(username=phone, email=email, password=password)
        Profile.objects.create(user=user, phone=phone, role='user')
        login(request, user)
        logger.info(f"Зарегистрирован новый пользователь | user={user.username} | email={email}")
        return redirect('profile')
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя | phone={phone} | {e}", exc_info=True)
        messages.error(request, "Не удалось создать аккаунт. Попробуйте позже.")
        return render(request, 'signup.html')

def signout(request):
    if request.user.is_authenticated:
        logger.info(f"Выход из системы | user={request.user.username}")
    logout(request)
    return redirect('index')

@role_required(['accountant'])
def statement(request):
    profile = None
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        
    cabinets = Cabinet.objects.all().order_by('number')
    selected_cabinet_id = request.GET.get('cabinet')
    
    if selected_cabinet_id:
        try:
            selected_cabinet = Cabinet.objects.get(id=selected_cabinet_id)
            equipments = Equipment.objects.filter(cabinet=selected_cabinet)
        except Cabinet.DoesNotExist:
            selected_cabinet = None
            equipments = Equipment.objects.none()
    else:
        if cabinets.exists():
            selected_cabinet = cabinets.first()
            equipments = Equipment.objects.filter(cabinet=selected_cabinet)
        else:
            selected_cabinet = None
            equipments = Equipment.objects.none()

    context = {
        'cabinets': cabinets,
        'equipments': equipments,
        'selected_cabinet': selected_cabinet,
        'profile': profile,
    }
    return TemplateResponse(request, 'statement.html', context)

def test_500(request):
    logger.error("Тестовая ошибка 500 | user=%s | path=%s", request.user, request.path)
    raise Exception("Тестовая ошибка")