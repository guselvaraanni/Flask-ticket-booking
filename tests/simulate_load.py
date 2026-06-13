"""
Load Testing Script - Simulates high concurrency seat booking
Tests the row-level locking mechanism with 50+ concurrent requests
"""

import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "http://localhost:8000/api"
NUM_CONCURRENT_REQUESTS = 51
TIMEOUT = 10


class BookingLoadTester:
    def __init__(self):
        self.results = {
            'success': 0,
            'conflict': 0,
            'error': 0,
            'details': []
        }
        self.lock = threading.Lock()

    def setup_test_event(self):
        """Create an event and generate seats for testing"""
        print("Setting up test event...")

        event_data = {
            'name': 'Load Test Concert',
            'date': (datetime.now() + timedelta(days=30)).isoformat(),
            'location': 'Test Venue'
        }

        response = requests.post(
            f"{API_BASE_URL}/events",
            json=event_data,
            timeout=TIMEOUT
        )

        if response.status_code != 201:
            print(f"Failed to create event: {response.text}")
            return None

        event = response.json()
        event_id = event['id']
        print(f"Created event with ID: {event_id}")

        seats_data = {
            'num_rows': 5,
            'seats_per_row': 20
        }

        response = requests.post(
            f"{API_BASE_URL}/events/{event_id}/seats",
            json=seats_data,
            timeout=TIMEOUT
        )

        if response.status_code != 201:
            print(f"Failed to create seats: {response.text}")
            return None

        print(f"Created seats: {response.json()['message']}")
        return event_id

    def get_available_seat(self, event_id):
        """Get the first available seat for the test"""
        response = requests.get(
            f"{API_BASE_URL}/bookings/event/{event_id}/available",
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            if data['available_seats']:
                return data['available_seats'][0]['id']

        return None

    def get_event_stats(self, event_id):
        """Fetch booking statistics for an event"""
        response = requests.get(
            f"{API_BASE_URL}/bookings/event/{event_id}/stats",
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()['stats']
        return None

    def get_seat_status(self, event_id, seat_id):
        """Fetch the current status of a specific seat"""
        response = requests.get(
            f"{API_BASE_URL}/events/{event_id}/seats",
            timeout=TIMEOUT
        )
        if response.status_code != 200:
            return None

        for seat in response.json():
            if seat['id'] == seat_id:
                return seat['status']

        return None

    def get_booked_seat_count(self, event_id, seat_id):
        """Count booking records for a specific seat via the booked-seats endpoint"""
        response = requests.get(
            f"{API_BASE_URL}/bookings/event/{event_id}/booked",
            timeout=TIMEOUT
        )
        if response.status_code != 200:
            return None

        booked_seats = response.json().get('booked_seats', [])
        return sum(1 for seat in booked_seats if seat['id'] == seat_id)

    def book_seat(self, seat_id, user_id):
        """Attempt to book a seat"""
        booking_data = {
            'seat_id': seat_id,
            'user_id': user_id
        }

        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/bookings",
                json=booking_data,
                timeout=TIMEOUT
            )
            elapsed_time = time.time() - start_time

            return {
                'status_code': response.status_code,
                'response': response.json(),
                'elapsed_time': elapsed_time,
                'user_id': user_id
            }
        except requests.exceptions.Timeout:
            return {
                'status_code': -1,
                'response': {'error': 'Request timeout'},
                'elapsed_time': TIMEOUT,
                'user_id': user_id
            }
        except Exception as e:
            return {
                'status_code': -1,
                'response': {'error': str(e)},
                'elapsed_time': 0,
                'user_id': user_id
            }

    def concurrent_booking_test(self, seat_id):
        """Run concurrent booking requests for the same seat"""
        print(f"\n{'='*70}")
        print(
            f"CONCURRENCY TEST: {NUM_CONCURRENT_REQUESTS} concurrent requests "
            f"for Seat ID {seat_id}"
        )
        print(f"{'='*70}\n")

        test_start_time = time.time()

        with ThreadPoolExecutor(max_workers=NUM_CONCURRENT_REQUESTS) as executor:
            futures = []

            for i in range(NUM_CONCURRENT_REQUESTS):
                user_id = f"user_{i}_{int(time.time())}"
                future = executor.submit(self.book_seat, seat_id, user_id)
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()

                with self.lock:
                    if result['status_code'] == 201:
                        self.results['success'] += 1
                        print(
                            f"SUCCESS ({result['elapsed_time']:.3f}s) - "
                            f"User: {result['user_id']}"
                        )
                    elif result['status_code'] == 409:
                        self.results['conflict'] += 1
                        print(
                            f"CONFLICT ({result['elapsed_time']:.3f}s) - "
                            f"Seat already booked"
                        )
                    else:
                        self.results['error'] += 1
                        print(
                            f"ERROR ({result['elapsed_time']:.3f}s) - "
                            f"Status: {result['status_code']}"
                        )

                    self.results['details'].append(result)

        test_duration = time.time() - test_start_time
        print(f"\nTest completed in {test_duration:.2f} seconds")

    def validate_consistency(self, event_id, seat_id):
        """
        Verify HTTP outcomes and database-backed state after the load test.
        Returns (passed: bool, failures: list[str])
        """
        failures = []
        expected_conflicts = NUM_CONCURRENT_REQUESTS - 1

        if self.results['success'] != 1:
            failures.append(
                f"Expected exactly 1 successful booking, got {self.results['success']}"
            )

        if self.results['conflict'] != expected_conflicts:
            failures.append(
                f"Expected {expected_conflicts} conflict responses, "
                f"got {self.results['conflict']}"
            )

        if self.results['error'] != 0:
            failures.append(
                f"Expected 0 errors, got {self.results['error']}"
            )

        stats = self.get_event_stats(event_id)
        if stats is None:
            failures.append("Could not fetch event statistics")
        elif stats['booked_seats'] != 1:
            failures.append(
                f"Expected 1 booked seat in database, got {stats['booked_seats']}"
            )

        seat_status = self.get_seat_status(event_id, seat_id)
        if seat_status is None:
            failures.append(f"Could not fetch status for seat {seat_id}")
        elif seat_status != 'BOOKED':
            failures.append(
                f"Expected seat {seat_id} status BOOKED, got {seat_status}"
            )

        booked_count = self.get_booked_seat_count(event_id, seat_id)
        if booked_count is None:
            failures.append(f"Could not verify booking records for seat {seat_id}")
        elif booked_count != 1:
            failures.append(
                f"Expected 1 booking record for seat {seat_id}, got {booked_count}"
            )

        return len(failures) == 0, failures

    def print_results(self, event_id, seat_id):
        """Print test results, consistency checks, and statistics"""
        print(f"\n{'='*70}")
        print("LOAD TEST RESULTS")
        print(f"{'='*70}\n")

        total_requests = (
            self.results['success'] + self.results['conflict'] + self.results['error']
        )

        print(f"Total Requests:        {total_requests}")
        print(f"Successful Bookings:   {self.results['success']}")
        print(f"Conflicts (409):       {self.results['conflict']}")
        print(f"Errors:                {self.results['error']}")

        passed, failures = self.validate_consistency(event_id, seat_id)

        stats = self.get_event_stats(event_id)
        if stats:
            print(f"\nEvent Statistics:")
            print(f"  Total Seats:       {stats['total_seats']}")
            print(f"  Booked:            {stats['booked_seats']}")
            print(f"  Available:         {stats['available_seats']}")
            print(f"  Occupancy Rate:    {stats['occupancy_rate']:.1f}%")

        seat_status = self.get_seat_status(event_id, seat_id)
        if seat_status:
            print(f"\nTarget Seat {seat_id} Status: {seat_status}")

        if passed:
            print(
                f"\nTEST PASSED: 1 booking succeeded, "
                f"{self.results['conflict']} rejected, database state consistent"
            )
        else:
            print("\nTEST FAILED: Consistency checks did not pass")
            for failure in failures:
                print(f"  - {failure}")

        print(f"\n{'='*70}\n")
        return passed

    def run_full_test(self):
        """Run the complete load test"""
        print("Starting Seat Booking Load Test...")
        print(f"API Base URL: {API_BASE_URL}\n")

        event_id = self.setup_test_event()
        if not event_id:
            print("Failed to setup test. Exiting.")
            return False

        seat_id = self.get_available_seat(event_id)
        if not seat_id:
            print("No available seats found. Exiting.")
            return False

        self.concurrent_booking_test(seat_id)
        return self.print_results(event_id, seat_id)


if __name__ == '__main__':
    tester = BookingLoadTester()
    success = tester.run_full_test()
    exit(0 if success else 1)
