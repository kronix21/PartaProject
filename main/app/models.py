from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('admin', 'Администратор'),
        ('technician', 'Техник'),
        ('accountant', 'Бухгалтер'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Аватар")
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name="Роль"
    )

    def __str__(self):
        return f"Профиль {self.user.username}"

class EquipmentType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название типа")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Тип оборудования"
        verbose_name_plural = "Типы оборудования"
        ordering = ['name']

    def __str__(self):
        return self.name


class Cabinet(models.Model):
    number = models.CharField(max_length=20, unique=True, verbose_name="Номер кабинета")
    floor = models.IntegerField(verbose_name="Этаж")
    purpose = models.CharField(max_length=100, blank=True, null=True, verbose_name="Назначение")

    class Meta:
        verbose_name = "Кабинет"
        verbose_name_plural = "Кабинеты"
        ordering = ['number']

    def __str__(self):
        return f"каб. {self.number}"


class Employee(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="ФИО")
    position = models.CharField(max_length=100, verbose_name="Должность")
    department = models.CharField(max_length=100, verbose_name="Подразделение")
    phone = models.CharField(max_length=20, verbose_name="Телефон")

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Equipment(models.Model):
    STATUS_CHOICES = [
        ('working', 'В работе'),
        ('repair', 'В ремонте'),
        ('written_off', 'Списано'),
    ]

    inventory_number = models.CharField(max_length=50, unique=True, verbose_name="Инвентарный номер")
    name = models.CharField(max_length=150, verbose_name="Наименование")
    model = models.CharField(max_length=100, verbose_name="Модель")
    serial_number = models.CharField(max_length=100, unique=True, verbose_name="Серийный номер")
    purchase_date = models.DateField(verbose_name="Дата поступления")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Состояние")
    
    photo = models.ImageField(
        upload_to='equipment_photos/', 
        null=True, 
        blank=True, 
        verbose_name="Фотография"
    )

    type = models.ForeignKey(EquipmentType, on_delete=models.PROTECT, related_name='equipments', verbose_name="Тип оборудования")
    cabinet = models.ForeignKey(Cabinet, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipments', verbose_name="Кабинет")
    responsible = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='responsible_for', verbose_name="Ответственный")

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
        ordering = ['inventory_number']
        constraints = [
            models.UniqueConstraint(fields=['serial_number'], name='unique_serial_number'),
            models.CheckConstraint(
                condition=models.Q(status__in=['new', 'working', 'repair', 'written_off']),
                name='valid_equipment_status'
            )
        ]

    def __str__(self):
        return f"{self.inventory_number} - {self.name}"

    def clean(self):
        super().clean()
        # NFR-05 и FR-10: Проверка на списание уже на уровне модели
        if self.status == 'written_off' and self.cabinet:
            raise ValidationError(_("Списанное оборудование не может быть закреплено за кабинетом."))


class Movement(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='movements', verbose_name="Оборудование")
    date = models.DateField(verbose_name="Дата перемещения")
    from_cabinet = models.ForeignKey(Cabinet, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_from', verbose_name="Кабинет отправления")
    to_cabinet = models.ForeignKey(Cabinet, on_delete=models.PROTECT, related_name='movements_to', verbose_name="Кабинет назначения")
    from_responsible = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_from', verbose_name="Прежний ответственный")
    to_responsible = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='movements_to', verbose_name="Новый ответственный")
    reason = models.CharField(max_length=200, verbose_name="Причина перемещения")

    class Meta:
        verbose_name = "Перемещение"
        verbose_name_plural = "Перемещения"
        ordering = ['-date']

    def __str__(self):
        return f"Перемещение {self.equipment.inventory_number} ({self.date})"

    def clean(self):
        super().clean()
        # FR-10: Запрет перемещения списанного оборудования
        if self.equipment.status == 'written_off':
            raise ValidationError(_("Невозможно переместить списанное оборудование."))


class Repair(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'В процессе'),
        ('completed', 'Завершен'),
    ]
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='repairs', verbose_name="Оборудование")
    request_date = models.DateField(verbose_name="Дата обращения")
    description = models.TextField(verbose_name="Описание неисправности")
    technician = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='repairs_done', verbose_name="Исполнитель (техник)")
    result = models.TextField(blank=True, null=True, verbose_name="Результат ремонта")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', verbose_name="Статус ремонта")

    class Meta:
        verbose_name = "Ремонт"
        verbose_name_plural = "Ремонты"
        ordering = ['-request_date']

    def __str__(self):
        return f"Ремонт {self.equipment.inventory_number} ({self.get_status_display()})"


class WriteOffAct(models.Model):
    act_number = models.CharField(max_length=50, unique=True, verbose_name="Номер акта")
    date = models.DateField(verbose_name="Дата списания")
    reason = models.CharField(max_length=200, verbose_name="Причина списания")
    basis = models.CharField(max_length=200, verbose_name="Основание (приказ)")
    equipment = models.OneToOneField(Equipment, on_delete=models.PROTECT, related_name='write_off_act', verbose_name="Списываемое оборудование")

    class Meta:
        verbose_name = "Акт списания"
        verbose_name_plural = "Акты списания"
        ordering = ['-date']

    def __str__(self):
        return f"Акт списания №{self.act_number} от {self.date}"

    def save(self, *args, **kwargs):
        if self.equipment.status != 'written_off':
            self.equipment.status = 'written_off'
            self.equipment.cabinet = None
            self.equipment.responsible = None
            self.equipment.save()
        super().save(*args, **kwargs)

