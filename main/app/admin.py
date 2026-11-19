from django.contrib import admin
from django.http import HttpResponse
from .models import (
    EquipmentType, Cabinet, Employee, Equipment, 
    Movement, Repair, WriteOffAct, Delivery, DeliveryItem
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

@admin.register(EquipmentType)  # <-- ДОБАВЛЕНО
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('inventory_number', 'name', 'model', 'type', 'cabinet', 'responsible', 'status')
    list_filter = ('status', 'type', 'cabinet', 'responsible')
    search_fields = ('inventory_number', 'name', 'serial_number', 'model')
    actions = [print_inventory_sheet]
    readonly_fields = ('id',)
    
    fieldsets = (
        ('Основная информация', {'fields': ('inventory_number', 'name', 'model', 'serial_number', 'type')}),
        ('Финансы и состояние', {'fields': ('purchase_date', 'cost', 'status')}),
        ('Размещение и ответственность', {'fields': ('cabinet', 'responsible')}),
    )

@admin.register(Cabinet)
class CabinetAdmin(admin.ModelAdmin):
    list_display = ('number', 'building', 'floor', 'purpose')
    search_fields = ('number', 'building')

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

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'supplier_name')

@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):
    list_display = ('delivery', 'equipment', 'quantity', 'price_at_delivery')