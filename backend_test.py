import requests
import sys
import json
from datetime import datetime, timedelta

class InvoiceAppTester:
    def __init__(self, base_url="https://invoice-hub-70.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_clients = []
        self.created_invoices = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.text else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_signup(self):
        """Test user signup"""
        timestamp = datetime.now().strftime('%H%M%S')
        signup_data = {
            "name": f"Test User {timestamp}",
            "email": f"test{timestamp}@example.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Signup",
            "POST",
            "auth/signup",
            200,
            data=signup_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            print(f"   User created: {response['user']['name']} ({response['user']['email']})")
            return True
        return False

    def test_login(self):
        """Test user login with created credentials"""
        if not hasattr(self, 'signup_email'):
            print("❌ Cannot test login - no signup email available")
            return False
            
        login_data = {
            "email": self.signup_email,
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST", 
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            return True
        return False

    def test_create_client(self, client_data):
        """Create a client"""
        success, response = self.run_test(
            f"Create Client - {client_data['name']}",
            "POST",
            "clients",
            200,
            data=client_data
        )
        
        if success and 'id' in response:
            self.created_clients.append(response)
            return response['id']
        return None

    def test_get_clients(self):
        """Get all clients"""
        success, response = self.run_test(
            "Get All Clients",
            "GET",
            "clients",
            200
        )
        
        if success:
            print(f"   Found {len(response)} clients")
            return True
        return False

    def test_get_client(self, client_id):
        """Get specific client"""
        success, response = self.run_test(
            "Get Single Client",
            "GET",
            f"clients/{client_id}",
            200
        )
        return success

    def test_update_client(self, client_id):
        """Update client"""
        update_data = {
            "name": "Updated Client Name",
            "email": "updated@example.com",
            "phone": "+1-555-0199",
            "company": "Updated Company Inc",
            "address": "456 Updated St, New City, NY 10002"
        }
        
        success, response = self.run_test(
            "Update Client",
            "PUT",
            f"clients/{client_id}",
            200,
            data=update_data
        )
        return success

    def test_create_invoice(self, client_id, invoice_data):
        """Create an invoice"""
        success, response = self.run_test(
            f"Create Invoice for Client {client_id}",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if success and 'id' in response:
            self.created_invoices.append(response)
            print(f"   Invoice created: {response['invoice_number']} - Total: ${response['total']}")
            return response['id']
        return None

    def test_get_invoices(self):
        """Get all invoices"""
        success, response = self.run_test(
            "Get All Invoices",
            "GET",
            "invoices",
            200
        )
        
        if success:
            print(f"   Found {len(response)} invoices")
            return True
        return False

    def test_get_invoice(self, invoice_id):
        """Get specific invoice"""
        success, response = self.run_test(
            "Get Single Invoice",
            "GET",
            f"invoices/{invoice_id}",
            200
        )
        return success

    def test_update_invoice(self, invoice_id, client_id):
        """Update invoice"""
        update_data = {
            "client_id": client_id,
            "date": "2025-01-15",
            "due_date": "2025-02-15",
            "items": [
                {
                    "description": "Updated Service",
                    "quantity": 2,
                    "rate": 150.0,
                    "amount": 300.0
                }
            ],
            "tax": 30.0,
            "discount": 10.0,
            "status": "sent",
            "notes": "Updated invoice notes"
        }
        
        success, response = self.run_test(
            "Update Invoice",
            "PUT",
            f"invoices/{invoice_id}",
            200,
            data=update_data
        )
        return success

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        
        if success:
            print(f"   Total Revenue: ${response.get('total_revenue', 0)}")
            print(f"   Total Invoices: {response.get('total_invoices', 0)}")
            return True
        return False

    def test_dashboard_chart_data(self):
        """Test dashboard chart data"""
        success, response = self.run_test(
            "Dashboard Chart Data",
            "GET",
            "dashboard/chart-data",
            200
        )
        
        if success:
            revenue_data = response.get('revenue_trend', [])
            status_dist = response.get('status_distribution', {})
            print(f"   Revenue trend data points: {len(revenue_data)}")
            print(f"   Status distribution: {status_dist}")
            return True
        return False

    def test_delete_invoice(self, invoice_id):
        """Delete invoice"""
        success, response = self.run_test(
            "Delete Invoice",
            "DELETE",
            f"invoices/{invoice_id}",
            200
        )
        return success

    def test_delete_client(self, client_id):
        """Delete client"""
        success, response = self.run_test(
            "Delete Client",
            "DELETE",
            f"clients/{client_id}",
            200
        )
        return success

def main():
    print("🚀 Starting Invoice App Backend API Testing...")
    tester = InvoiceAppTester()
    
    # Test Authentication
    print("\n" + "="*50)
    print("TESTING AUTHENTICATION")
    print("="*50)
    
    if not tester.test_signup():
        print("❌ Signup failed, stopping tests")
        return 1

    # Test Clients CRUD
    print("\n" + "="*50)
    print("TESTING CLIENTS MANAGEMENT")
    print("="*50)
    
    # Create test clients
    test_clients = [
        {
            "name": "Acme Corporation",
            "email": "contact@acme.com",
            "phone": "+1-555-0123",
            "company": "Acme Corp",
            "address": "123 Business St, City, NY 10001"
        },
        {
            "name": "Tech Solutions Ltd",
            "email": "info@techsolutions.com", 
            "phone": "+1-555-0456",
            "company": "Tech Solutions Ltd",
            "address": "456 Tech Ave, Silicon Valley, CA 94000"
        },
        {
            "name": "Global Services Inc",
            "email": "hello@globalservices.com",
            "phone": "+1-555-0789",
            "company": "Global Services Inc", 
            "address": "789 Global Blvd, International City, TX 75000"
        }
    ]
    
    client_ids = []
    for client_data in test_clients:
        client_id = tester.test_create_client(client_data)
        if client_id:
            client_ids.append(client_id)
    
    if not client_ids:
        print("❌ No clients created, stopping tests")
        return 1
    
    # Test client operations
    tester.test_get_clients()
    tester.test_get_client(client_ids[0])
    tester.test_update_client(client_ids[0])

    # Test Invoices CRUD
    print("\n" + "="*50)
    print("TESTING INVOICES MANAGEMENT")
    print("="*50)
    
    # Create test invoices with different statuses
    test_invoices = [
        {
            "client_id": client_ids[0],
            "date": "2025-01-10",
            "due_date": "2025-02-10",
            "items": [
                {
                    "description": "Web Development Services",
                    "quantity": 40,
                    "rate": 100.0,
                    "amount": 4000.0
                },
                {
                    "description": "SEO Optimization",
                    "quantity": 10,
                    "rate": 150.0,
                    "amount": 1500.0
                }
            ],
            "tax": 550.0,
            "discount": 100.0,
            "status": "paid",
            "notes": "Thank you for your business!"
        },
        {
            "client_id": client_ids[1] if len(client_ids) > 1 else client_ids[0],
            "date": "2025-01-12",
            "due_date": "2025-02-12",
            "items": [
                {
                    "description": "Mobile App Development",
                    "quantity": 60,
                    "rate": 120.0,
                    "amount": 7200.0
                }
            ],
            "tax": 720.0,
            "discount": 200.0,
            "status": "sent",
            "notes": "Payment due within 30 days"
        },
        {
            "client_id": client_ids[2] if len(client_ids) > 2 else client_ids[0],
            "date": "2025-01-05",
            "due_date": "2025-01-20",
            "items": [
                {
                    "description": "Consulting Services",
                    "quantity": 20,
                    "rate": 200.0,
                    "amount": 4000.0
                }
            ],
            "tax": 400.0,
            "discount": 0.0,
            "status": "overdue",
            "notes": "Urgent payment required"
        },
        {
            "client_id": client_ids[0],
            "date": "2025-01-15",
            "due_date": "2025-02-15",
            "items": [
                {
                    "description": "Design Services",
                    "quantity": 15,
                    "rate": 80.0,
                    "amount": 1200.0
                }
            ],
            "tax": 120.0,
            "discount": 50.0,
            "status": "draft",
            "notes": "Draft invoice for review"
        }
    ]
    
    invoice_ids = []
    for invoice_data in test_invoices:
        invoice_id = tester.test_create_invoice(invoice_data["client_id"], invoice_data)
        if invoice_id:
            invoice_ids.append(invoice_id)
    
    if not invoice_ids:
        print("❌ No invoices created, stopping tests")
        return 1
    
    # Test invoice operations
    tester.test_get_invoices()
    tester.test_get_invoice(invoice_ids[0])
    tester.test_update_invoice(invoice_ids[0], client_ids[0])

    # Test Dashboard
    print("\n" + "="*50)
    print("TESTING DASHBOARD")
    print("="*50)
    
    tester.test_dashboard_stats()
    tester.test_dashboard_chart_data()

    # Test Delete Operations
    print("\n" + "="*50)
    print("TESTING DELETE OPERATIONS")
    print("="*50)
    
    # Delete one invoice and one client for testing
    if invoice_ids:
        tester.test_delete_invoice(invoice_ids[-1])
    
    if len(client_ids) > 1:
        tester.test_delete_client(client_ids[-1])

    # Print final results
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"✅ Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.created_clients:
        print(f"👥 Clients created: {len(tester.created_clients)}")
    if tester.created_invoices:
        print(f"📄 Invoices created: {len(tester.created_invoices)}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())