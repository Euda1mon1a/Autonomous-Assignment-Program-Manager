"""
Locust Load Test for Residency Scheduler

Main entry point for Locust load testing.

Run:
    locust -f locustfile.py --host=http://localhost:8000
    locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 10m
"""

import os
from locust import HttpUser, task, between, events
from locust.env import Environment

from users.admin_user import AdminUser
from users.faculty_user import FacultyUser
from users.resident_user import ResidentUser


class MixedWorkloadUser(HttpUser):
    """
    Mixed workload simulating realistic traffic distribution.

    User distribution:
    - 10% Admins (heavy operations)
    - 30% Faculty (moderate operations)
    - 60% Residents (light read operations)
    """

    # Wait between 1-5 seconds between tasks
    wait_time = between(1, 5)

    # Weight distribution
    # Note: Locust uses these proportions when spawning users
    admin_weight = 10
    faculty_weight = 30
    resident_weight = 60

    def __init__(self, environment):
        super().__init__(environment)
        self.token = None
        self.user_role = self._determine_role()

    def _determine_role(self):
        """Determine user role based on weights"""
        import random
        rand = random.randint(1, 100)

        if rand <= self.admin_weight:
            return 'admin'
        elif rand <= self.admin_weight + self.faculty_weight:
            return 'faculty'
        else:
            return 'resident'

    def on_start(self):
        """Called when a user starts - login"""
        self.login()

    def on_stop(self):
        """Called when a user stops - logout"""
        if self.token:
            self.logout()

    def login(self):
        """Authenticate user"""
        credentials = {
            'admin': {'username': 'admin@test.com', 'password': 'TestPassword123!'},
            'faculty': {'username': 'faculty@test.com', 'password': 'TestPassword123!'},
            'resident': {'username': 'resident@test.com', 'password': 'TestPassword123!'}
        }

        creds = credentials.get(self.user_role, credentials['resident'])

        with self.client.post(
            '/api/v1/auth/login',
            json=creds,
            catch_response=True,
            name='/api/v1/auth/login'
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                response.success()
            else:
                response.failure(f'Login failed: {response.status_code}')

    def logout(self):
        """Logout user"""
        if self.token:
            headers = {'Authorization': f'Bearer {self.token}'}
            self.client.post('/api/v1/auth/logout', headers=headers)

    def get_auth_headers(self):
        """Get authorization headers"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    @task(10)
    def view_schedule(self):
        """View assignments (most common operation)"""
        if not self.token:
            return

        self.client.get(
            '/api/v1/assignments?limit=20',
            headers=self.get_auth_headers(),
            name='/api/v1/assignments (list)'
        )

    @task(5)
    def view_personnel(self):
        """View personnel list"""
        if not self.token:
            return

        self.client.get(
            '/api/v1/persons?limit=20',
            headers=self.get_auth_headers(),
            name='/api/v1/persons (list)'
        )

    @task(4)
    def view_rotations(self):
        """View rotations"""
        if not self.token:
            return

        self.client.get(
            '/api/v1/rotations?limit=20',
            headers=self.get_auth_headers(),
            name='/api/v1/rotations (list)'
        )

    @task(3)
    def view_blocks(self):
        """View calendar blocks"""
        if not self.token:
            return

        self.client.get(
            '/api/v1/blocks?limit=30',
            headers=self.get_auth_headers(),
            name='/api/v1/blocks (list)'
        )

    @task(3)
    def check_compliance(self):
        """Check compliance status"""
        if not self.token:
            return

        self.client.get(
            '/api/v1/compliance/work-hours',
            headers=self.get_auth_headers(),
            name='/api/v1/compliance/work-hours'
        )

    @task(2)
    def view_swaps(self):
        """View swap requests"""
        if not self.token:
            return

        self.client.get(
            '/api/v1/swaps?limit=20',
            headers=self.get_auth_headers(),
            name='/api/v1/swaps (list)'
        )

    @task(1)
    def view_resilience_metrics(self):
        """View resilience metrics (admin/coordinator only)"""
        if not self.token or self.user_role == 'resident':
            return

        self.client.get(
            '/api/v1/resilience/metrics',
            headers=self.get_auth_headers(),
            name='/api/v1/resilience/metrics'
        )

    @task(2)
    def search_operations(self):
        """Perform search"""
        if not self.token:
            return

        import random
        queries = ['clinic', 'call', 'resident', 'faculty', 'emergency']
        query = random.choice(queries)

        self.client.get(
            f'/api/v1/rotations?search={query}',
            headers=self.get_auth_headers(),
            name='/api/v1/rotations (search)'
        )


# Event listeners for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print('=' * 50)
    print('LOCUST LOAD TEST STARTING')
    print(f'Host: {environment.host}')
    print(f'Users: {environment.parsed_options.num_users if hasattr(environment.parsed_options, "num_users") else "N/A"}')
    print('=' * 50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print('=' * 50)
    print('LOCUST LOAD TEST COMPLETED')
    print('=' * 50)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called for each request"""
    # Custom metrics can be tracked here
    if exception:
        print(f'Request failed: {name} - {exception}')


# Example custom shape for specific load patterns
from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    Step load pattern - gradually increase load in steps
    """
    step_time = 60  # Seconds per step
    step_load = 10  # Users to add per step
    spawn_rate = 2  # Users per second spawn rate
    time_limit = 600  # Total test time in seconds

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = run_time // self.step_time
        return (current_step + 1) * self.step_load, self.spawn_rate


class SpikeLoadShape(LoadTestShape):
    """
    Spike load pattern - sudden spike then drop
    """
    time_limit = 300  # 5 minutes

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        if run_time < 60:
            # Warm up
            return 10, 2
        elif run_time < 120:
            # Spike to 100 users
            return 100, 10
        elif run_time < 180:
            # Hold spike
            return 100, 10
        elif run_time < 240:
            # Drop back to baseline
            return 20, 5
        else:
            # Cool down
            return 10, 2


# To use a specific shape, run:
# locust -f locustfile.py --host=http://localhost:8000 --shape=StepLoadShape
