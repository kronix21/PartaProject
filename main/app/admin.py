from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import (
    EquipmentType, Cabinet, Employee, Equipment, 
    Movement, Repair, WriteOffAct, Profile,
)

# --- FR-14: Действие для печати инвентаризационной ведомости ---
@admin.action(description='Сформировать и распечатать инвентаризационную ведомость')
def print_inventory_sheet(modeladmin, request, queryset):
    cabinets = {}
    for eq in queryset.select_related('cabinet', 'type', 'responsible'):
        cab_name = eq.cabinet.number if eq.cabinet else "Не распределено"
        if cab_name not in cabinets:
            cabinets[cab_name] = []
        cabinets[cab_name].append(eq)
    
    html = f"<html><head><title>Инвентаризационная ведомость</title>"
    html += "<style>body{{font-family: Arial;}} table{{width: 100%; border-collapse: collapse;}} th, td{{border: 1px solid #000; padding: 8px; text-align: left;}}</style>"
    html += "</head><body><h2>Инвентаризационная ведомость</h2>"
    
    for cab, items in cabinets.items():
        html += f"<h3>Кабинет: {cab}</h3>"
        html += "<table><tr><th>Инв. номер</th><th>Наименование</th><th>Модель</th><th>Состояние</th><th>Ответственный</th></tr>"
        for item in items:
            resp = item.responsible.full_name if item.responsible else "Не назначен"
            html += f"<tr><td>{item.inventory_number}</td><td>{item.name}</td><td>{item.model}</td><td>{item.get_status_display()}</td><td>{resp}</td></tr>"
        html += "</table><br>"
    
    html += "</body></html>"
    return HttpResponse(html)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'phone')

@admin.register(EquipmentType) 
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'inventory_number', 
        'name', 
        'model', 
        'get_status_display', 
        'cabinet', 
        'responsible', 
        'show_photo'
    )
    
    list_filter = ('status', 'type', 'cabinet')
    
    search_fields = ('inventory_number', 'name', 'serial_number')
    
    readonly_fields = ('show_photo_large',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('inventory_number', 'name', 'model', 'serial_number', 'type')
        }),
        ('Дата', {
            'fields': ('purchase_date',)
        }),
        ('Местоположение и ответственные', {
            'fields': ('cabinet', 'responsible', 'status')
        }),
        ('Медиа', {
            'fields': ('photo', 'show_photo_large')
        }),
    )
    def show_photo(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />', obj.photo.url)
        return "Нет фото"
    show_photo.short_description = 'Фото' # Название колонки

    def show_photo_large(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 10px;" />', obj.photo.url)
        return "Фото не загружено"
    show_photo_large.short_description = 'Текущее фото'

@admin.register(Cabinet)
class CabinetAdmin(admin.ModelAdmin):
    list_display = ('number', 'floor', 'purpose')
    search_fields = ('number',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'department', 'phone')
    search_fields = ('full_name', 'department')

@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ('date', 'equipment', 'from_cabinet', 'to_cabinet', 'to_responsible')
    list_filter = ('date', 'to_cabinet')

@admin.register(Repair)
class RepairAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'request_date', 'status', 'technician')
    list_filter = ('status', 'request_date')

@admin.register(WriteOffAct)
class WriteOffActAdmin(admin.ModelAdmin):
    list_display = ('act_number', 'date', 'equipment', 'reason')
    readonly_fields = ('act_number', 'date', 'reason', 'basis', 'equipment')
