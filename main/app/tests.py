from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Equipment, Cabinet, EquipmentType, Employee, Profile, Movement

class NegativeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cabinet = Cabinet.objects.create(number="101", floor=1)
        self.type = EquipmentType.objects.create(name="Стул")
        self.employee = Employee.objects.create(
            full_name="Иванов И.И.", position="Техник", department="IT", phone="123"
        )
        self.equipment = Equipment.objects.create(
            inventory_number="INV001", name="Стул", model="Серый",
            serial_number="SN001", purchase_date="2024-01-01", status="working",
            type=self.type, cabinet=self.cabinet, responsible=self.employee
        )
        self.user_user = User.objects.create_user(username="user1", password="pass12345")
        Profile.objects.create(user=self.user_user, role="user")
        self.user_accountant = User.objects.create_user(username="acc1", password="pass12345")
        Profile.objects.create(user=self.user_accountant, role="accountant")

    # 1. Обращение к несуществующей записи → 404
    def test_nonexistent_equipment_returns_404(self):
        # ЛОГИНИМСЯ, иначе @role_required редиректит на signin (302)
        self.client.login(username="user1", password="pass12345")
        response = self.client.get(reverse('equipment', args=[9999]))
        self.assertEqual(response.status_code, 404)

    # 2. Доступ без прав → 403
    def test_forbidden_for_wrong_role(self):
        self.client.login(username="user1", password="pass12345")  # роль user
        response = self.client.get(reverse('statement'))            # только accountant
        self.assertEqual(response.status_code, 403)

    # 3. Неверная форма → запись не создаётся
    def test_invalid_form_does_not_create_equipment(self):
        self.client.login(username="acc1", password="pass12345")
        initial_count = Equipment.objects.count()
        response = self.client.post(reverse('add'), {
            'inventory_number': '', 'name': '', 'serial_number': '',
            'model': '', 'purchase_date': '', 'status': '',
            'cabinet': '', 'type': '', 'responsible': '',
        }, follow=True)
        self.assertEqual(Equipment.objects.count(), initial_count)
        self.assertContains(response, "Заполните все обязательные поля")

    # 4. Ошибка в середине → данные не меняются
    def test_move_without_reason_does_not_change_data(self):
        self.client.login(username="acc1", password="pass12345")
        old_cabinet_id = self.equipment.cabinet_id
        initial_movements = Movement.objects.count()
        response = self.client.post(reverse('move_equipment', args=[self.equipment.pk]), {
            'date': '2024-01-01',
            'to_cabinet': self.cabinet.id,
            'reason': '',
        }, follow=True)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.cabinet_id, old_cabinet_id)
        self.assertEqual(Movement.objects.count(), initial_movements)
        self.assertContains(response, "Укажите причину перемещения")

    # 5. Пустая выборка не падает
    def test_statement_with_empty_cabinet_does_not_crash(self):
        empty_cabinet = Cabinet.objects.create(number="999", floor=9)
        self.client.login(username="acc1", password="pass12345")
        response = self.client.get(reverse('statement') + f'?cabinet={empty_cabinet.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "В этом кабинете нет оборудования")