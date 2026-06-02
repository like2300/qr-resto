from django.test import TestCase, Client
from django.urls import reverse
from .models import Restaurant, Table, Order
from django.utils import timezone

class BillRequestTestCase(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", slug="test-rest")
        self.table = Table.objects.create(restaurant=self.restaurant, name="Table 1", is_occupied=True)
        self.order = Order.objects.create(table=self.table, status='pending')
        self.client = Client()

    def test_request_bill_clears_table(self):
        # Verify initial state
        self.assertTrue(self.table.is_occupied)
        
        # Request the bill
        url = reverse('menu:request_bill', args=[self.table.uuid, self.order.uuid])
        response = self.client.post(url)
        
        # Check if redirect happened
        self.assertEqual(response.status_code, 302)
        
        # Verify state after request
        self.table.refresh_from_db()
        self.order.refresh_from_db()
        
        self.assertFalse(self.table.is_occupied)
        self.assertTrue(self.order.bill_requested)
        self.assertEqual(self.order.status, 'served')
