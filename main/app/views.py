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

def index(request):
    profile = None
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)

    context = {
        'profile': profile,
    }
    return TemplateResponse(request, 'index.html', context)

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
    item = get_object_or_404(Equipment, pk=pk)
    
    date_str = request.POST.get('date')
    to_cabinet_id = request.POST.get('to_cabinet')
    to_responsible_id = request.POST.get('to_responsible') or item.responsible_id
    reason = request.POST.get('reason')
    
    Movement.objects.create(
        equipment=item,
        date=date_str,
        from_cabinet=item.cabinet,
        to_cabinet_id=to_cabinet_id,
        from_responsible=item.responsible,
        to_responsible_id=to_responsible_id,
        reason=reason
    )
    
    item.cabinet_id = to_cabinet_id
    if to_responsible_id:
        item.responsible_id = to_responsible_id
    item.save()
    
    return redirect('equipment', pk=item.pk)
    
def write_off_equipment(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    WriteOffAct.objects.create(
        act_number=request.POST.get('act_number'),
        date=request.POST.get('date') or timezone.now().date(),
        reason=request.POST.get('reason'),
        basis=request.POST.get('basis'),
        equipment=item
    )
    return redirect('equipment', pk=item.pk)
    
def create_repair(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    
    if item.status == 'written_off':
        return redirect('equipment', pk=item.pk)

    technician_id = request.POST.get('technician')
    
    Repair.objects.create(
        equipment=item,
        request_date=request.POST.get('date') or timezone.now().date(),
        description=request.POST.get('description'),
        technician_id=technician_id,
        status='in_progress'
    )
    
    item.status = 'repair'
    item.save()
    
    return redirect('equipment', pk=item.pk)
    
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

def add(request):
    photo = request.FILES.get('photo') 
    inventory_number = request.POST.get('inventory_number')
    name = request.POST.get('name')
    serial_number = request.POST.get('serial_number')
    cabinet_id = request.POST.get('cabinet')
    type_id = request.POST.get('type')
    model = request.POST.get('model')
    purchase_date = request.POST.get('purchase_date')
    status = request.POST.get('status')
    responsible_id = request.POST.get('responsible')

    equipment = Equipment()

    equipment.inventory_number=inventory_number
    equipment.name=name
    equipment.serial_number=serial_number
    equipment.model=model
    equipment.purchase_date=purchase_date
    equipment.status=status
    equipment.photo = photo
    equipment.cabinet_id = cabinet_id
    equipment.type_id = type_id
    equipment.responsible_id = responsible_id
        
    equipment.save()
    
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

def save_edit(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    
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
    
    item.save()
    return redirect('equipment', pk=item.pk)

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

def close_repair(request):
    repair_id = request.POST.get('repair_id')
    technician_id = request.POST.get('technician')
    result_text = request.POST.get('result')
    new_status = request.POST.get('status')
    
    repair = get_object_or_404(Repair, id=repair_id)
    
    repair.technician_id = technician_id
    repair.result = result_text
    repair.status = new_status
    repair.save()
    
    if new_status == 'completed':
        repair.equipment.status = 'working'
        repair.equipment.save()
        
    return redirect('repairs')

def signin_staff(request):
    return TemplateResponse(request, 'signin_staff.html')

def signin(request):
    return TemplateResponse(request, 'signin.html')

def auth(request):
    phone = request.POST.get('phone')
    password = request.POST.get('password')
    
    user = authenticate(request, username=phone, password=password)
    
    if user is not None:
        login(request, user)
        return redirect('profile')
    else:
        messages.error(request, "Неверный телефон или пароль")
        return redirect('signin')

def signup_staff(request):
    return TemplateResponse(request, 'signup_staff.html')

def signup(request):
    return TemplateResponse(request, 'signup.html')

def add_user(request):
    phone = request.POST.get('phone')
    email = request.POST.get('email')
    password = request.POST.get('password')

    if User.objects.filter(username=phone).exists():
        messages.error(request, "Пользователь с таким телефоном уже существует")
        return render(request, 'signup.html')

    user = User.objects.create_user(
        username=phone,
        email=email,
        password=password,
    )
    
    Profile.objects.create(user=user, phone=phone)
    login(request, user)

    return redirect('profile')

def signout(request):
    logout(request)
    return redirect('index')

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