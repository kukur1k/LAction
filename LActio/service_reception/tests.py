from django.test import TestCase



from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from .models import RepairRequest, WorkType


class CRUDTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            is_approved=True
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='test123')
        
        self.work_type = WorkType.objects.create(name='Диагностика')
        
        self.request = RepairRequest.objects.create(
            client_name='Иванов Иван Иванович',
            client_phone='79527891826',
            car_brand='Toyota',
            car_model='Camry',
            license_plate='A123AA',
            issue_description='Не заводится',
            status='draft',
            receptionist=self.user,
        )
        self.request.work_types.add(self.work_type)



    
    def test_create_request(self):
        
        response = self.client.post('/requests/create/', {
            'client_name': 'Петров Петр Петрович',
            'client_phone': '+79527891826',
            'car_brand': 'BMW',
            'car_model': 'X5',
            'license_plate': 'B456BB152',
            'vin': 'VIN9876543210',
            'mileage': 30000,
            'issue_description': 'Стук в подвеске',
            'work_types': [self.work_type.id],
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.assertEqual(RepairRequest.objects.count(), 2)
    
        new_request = RepairRequest.objects.last()
        self.assertEqual(new_request.client_name, 'Петров Петр Петрович')
        self.assertEqual(new_request.car_brand, 'BMW')
        self.assertEqual(new_request.car_model, 'X5')
        self.assertEqual(new_request.work_types.count(), 1)
    

    
    def test_read_request_list(self):
        
        response = self.client.get('/requests/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Иванов Иван Иванович')
        self.assertContains(response, 'Toyota')
        self.assertContains(response, 'Camry')
    
    def test_read_request_detail(self):
        
        response = self.client.get(f'/requests/{self.request.pk}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Иванов Иван Иванович')
        self.assertContains(response, 'Toyota')
        self.assertContains(response, 'Camry')
        self.assertContains(response, 'Не заводится')
    


    def test_update_request(self):
        
        response = self.client.post(f'/requests/{self.request.pk}/edit/', {
            'client_name': 'Иванов Иван *',
            'client_phone': '+7 900 123-45-67',
            'car_brand': 'Toyota',
            'car_model': 'Camry',
            'license_plate': 'A123AA',
            'issue_description': 'Не заводится *',
            'work_types': [self.work_type.id],
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.request.refresh_from_db()
        
        self.assertEqual(self.request.client_name, 'Иванов Иван *')
        self.assertEqual(self.request.issue_description, 'Не заводится *')
    

    
    def test_delete_request(self):
        
        self.assertEqual(RepairRequest.objects.count(), 1)
        
        response = self.client.post(f'/requests/{self.request.pk}/delete/')
        
        self.assertEqual(response.status_code, 302)
        
        self.assertEqual(RepairRequest.objects.count(), 0)
    
    
    def test_start_inspection(self):
        # Начать осмотр (статус draft -> active)
        
        self.client.get(f'/start-inspection/{self.request.pk}/')
        self.request.refresh_from_db()
        
        self.assertEqual(self.request.status, 'active')
        self.assertIsNotNone(self.request.started_at)
    
    def test_complete_request(self):
        
        self.client.get(f'/start-inspection/{self.request.pk}/')
        
        self.client.get(f'/complete-request/{self.request.pk}/')
        self.request.refresh_from_db()
        
        self.assertEqual(self.request.status, 'completed')
        self.assertIsNotNone(self.request.completed_at)
        self.assertIsNotNone(self.request.time_spent)


    
    def test_search_request_by_name(self):
        # Поиск заявки по имени клиента
        
        response = self.client.get('/requests/?search=Иванов')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Иванов Иван Иванович')
    
    def test_search_request_by_car(self):
        # Поиск заявки по марке
        
        response = self.client.get('/requests/?search=Toyota')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Toyota')
