"""
Admin User Behavior

Simulates administrator operations:
- Schedule generation
- User management
- System configuration
- Compliance monitoring
- Resilience analysis
"""

from locust import HttpUser, task, between
import random


class AdminUser(HttpUser):
    """
    Administrator user with heavy operations.

    Weight: 10% of total users
    """

    wait_time = between(2, 8)  # Longer think time for complex operations

    def __init__(self, environment):
        super().__init__(environment)
        self.token = None

    def on_start(self):
        """Login as admin"""
        self.login()

    def on_stop(self):
        """Logout"""
        if self.token:
            self.logout()

    def login(self):
        """Authenticate admin user"""
        with self.client.post(
            '/api/v1/auth/login',
            json={
                'username': 'admin@test.com',
                'password': 'TestPassword123!'
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                response.success()
            else:
                response.failure(f'Admin login failed: {response.status_code}')

    def logout(self):
        """Logout admin"""
        if self.token:
            headers = {'Authorization': f'Bearer {self.token}'}
            self.client.post('/api/v1/auth/logout', headers=headers)

    def get_headers(self):
        """Get auth headers"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    @task(10)
    def view_dashboard(self):
        """View admin dashboard data"""
        if not self.token:
            return

        # Multiple dashboard endpoints
        endpoints = [
            '/api/v1/assignments?limit=50',
            '/api/v1/persons',
            '/api/v1/resilience/metrics',
            '/api/v1/compliance/violations'
        ]

        for endpoint in endpoints:
            self.client.get(endpoint, headers=self.get_headers())

    @task(5)
    def manage_users(self):
        """User management operations"""
        if not self.token:
            return

        # List users with filters
        roles = ['RESIDENT', 'FACULTY', 'ADMIN', 'COORDINATOR']
        role = random.choice(roles)

        self.client.get(
            f'/api/v1/persons?role={role}&limit=20',
            headers=self.get_headers(),
            name='/api/v1/persons (filtered by role)'
        )

    @task(3)
    def create_person(self):
        """Create new person (less frequent)"""
        if not self.token:
            return

        person_data = {
            'first_name': f'Test{random.randint(1000, 9999)}',
            'last_name': 'User',
            'email': f'test{random.randint(1000, 9999)}@loadtest.com',
            'role': random.choice(['RESIDENT', 'FACULTY']),
            'is_active': True
        }

        if person_data['role'] == 'RESIDENT':
            person_data['pgy_year'] = random.randint(1, 4)

        with self.client.post(
            '/api/v1/persons',
            json=person_data,
            headers=self.get_headers(),
            catch_response=True,
            name='/api/v1/persons (create)'
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 409:
                # Conflict (duplicate) is expected in load test
                response.success()
            else:
                response.failure(f'Create person failed: {response.status_code}')

    @task(4)
    def manage_rotations(self):
        """Rotation management"""
        if not self.token:
            return

        self.client.get(
            '/api/v1/rotations?limit=50',
            headers=self.get_headers(),
            name='/api/v1/rotations (list all)'
        )

    @task(2)
    def create_rotation(self):
        """Create new rotation"""
        if not self.token:
            return

        rotation_types = ['CLINIC', 'INPATIENT', 'PROCEDURES', 'CALL', 'ADMIN']
        rotation_data = {
            'name': f'Test Rotation {random.randint(1000, 9999)}',
            'rotation_type': random.choice(rotation_types),
            'is_active': True,
            'requires_supervision': random.choice([True, False]),
            'max_consecutive_days': random.choice([7, 14, 21]),
            'color': '#' + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
        }

        with self.client.post(
            '/api/v1/rotations',
            json=rotation_data,
            headers=self.get_headers(),
            catch_response=True,
            name='/api/v1/rotations (create)'
        ) as response:
            if response.status_code in [201, 409]:
                response.success()
            else:
                response.failure(f'Create rotation failed: {response.status_code}')

    @task(6)
    def monitor_compliance(self):
        """Monitor ACGME compliance"""
        if not self.token:
            return

        endpoints = [
            '/api/v1/compliance/validate',
            '/api/v1/compliance/work-hours',
            '/api/v1/compliance/violations'
        ]

        endpoint = random.choice(endpoints)
        self.client.get(endpoint, headers=self.get_headers())

    @task(5)
    def resilience_monitoring(self):
        """Monitor resilience metrics"""
        if not self.token:
            return

        endpoints = [
            '/api/v1/resilience/health',
            '/api/v1/resilience/metrics',
            '/api/v1/resilience/utilization'
        ]

        endpoint = random.choice(endpoints)
        self.client.get(endpoint, headers=self.get_headers())

    @task(1)
    def generate_schedule(self):
        """Generate schedule (expensive operation, low frequency)"""
        if not self.token:
            return

        from datetime import datetime, timedelta

        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=30)

        schedule_request = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'algorithm': 'GREEDY',
            'optimization_goals': ['MINIMIZE_VIOLATIONS', 'BALANCE_WORKLOAD'],
            'max_runtime_seconds': 30,
            'include_weekends': True,
            'include_holidays': True
        }

        with self.client.post(
            '/api/v1/schedules/generate',
            json=schedule_request,
            headers=self.get_headers(),
            catch_response=True,
            name='/api/v1/schedules/generate',
            timeout=60  # Longer timeout for expensive operation
        ) as response:
            if response.status_code in [201, 202]:
                response.success()
            else:
                response.failure(f'Schedule generation failed: {response.status_code}')

    @task(3)
    def bulk_operations(self):
        """Bulk assignment operations"""
        if not self.token:
            return

        # Get bulk assignments
        self.client.get(
            '/api/v1/assignments?limit=100',
            headers=self.get_headers(),
            name='/api/v1/assignments (bulk list)'
        )

    @task(2)
    def export_data(self):
        """Export operations (reports, schedules)"""
        if not self.token:
            return

        # List schedules for export
        self.client.get(
            '/api/v1/schedules',
            headers=self.get_headers(),
            name='/api/v1/schedules (list)'
        )
