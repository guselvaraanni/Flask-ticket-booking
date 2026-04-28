"""
Load Testing Script - Simulates high concurrency seat booking
Tests the row-level locking mechanism with 50 concurrent requests
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import json

# Configuration
API_BASE_URL = "http://localhost:5000/api"
NUM_CONCURRENT_REQUESTS = 50
TIMEOUT = 10

class BookingLoadTester:
    def __init__(self):
        self.results = {
            'success': 0,
            'conflict': 0,
            'error': 0,
            'details': []
        }
        self.lock = __import__('threading').Lock()

    def setup_test_event(self):
        """Create an event and generate seats for testing"""
        print("Setting up test event...")
        
        # Create event
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
        
        # Generate seats (5 rows, 20 seats per row = 100 seats)
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

    def concurrent_booking_test(self, event_id, seat_id):
        """Run concurrent booking requests for the same seat"""
        print(f"\n{'='*70}")
        print(f"CONCURRENCY TEST: {NUM_CONCURRENT_REQUESTS} concurrent requests for Seat ID {seat_id}")
        print(f"{'='*70}\n")
        
        test_start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            
            # Submit all requests at roughly the same time
            for i in range(NUM_CONCURRENT_REQUESTS):
                user_id = f"user_{i}_{int(time.time())}"
                future = executor.submit(self.book_seat, seat_id, user_id)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                result = future.result()
                
                with self.lock:
                    if result['status_code'] == 201:
                        self.results['success'] += 1
                        print(f"✓ SUCCESS ({result['elapsed_time']:.3f}s) - User: {result['user_id']}")
                    elif result['status_code'] == 409:
                        self.results['conflict'] += 1
                        print(f"✗ CONFLICT ({result['elapsed_time']:.3f}s) - Seat already booked")
                    else:
                        self.results['error'] += 1
                        print(f"✗ ERROR ({result['elapsed_time']:.3f}s) - Status: {result['status_code']}")
                    
                    self.results['details'].append(result)
        
        test_duration = time.time() - test_start_time
        print(f"\nTest completed in {test_duration:.2f} seconds")

    def print_results(self, event_id):
        """Print test results and statistics"""
        print(f"\n{'='*70}")
        print("LOAD TEST RESULTS")
        print(f"{'='*70}\n")
        
        total_requests = self.results['success'] + self.results['conflict'] + self.results['error']
        
        print(f"Total Requests:        {total_requests}")
        print(f"Successful Bookings:   {self.results['success']}")
        print(f"Conflicts (409):       {self.results['conflict']}")
        print(f"Errors:                {self.results['error']}")
        
        if self.results['success'] == 1:
            print(f"\n✓ TEST PASSED: Exactly 1 seat booked, {self.results['conflict']} rejected")
        else:
            print(f"\n✗ TEST FAILED: Expected 1 booking, got {self.results['success']}")
        
        # Get seat status
        try:
            response = requests.get(
                f"{API_BASE_URL}/bookings/event/{event_id}/stats",
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                stats = response.json()['stats']
                print(f"\nEvent Statistics:")
                print(f"  Total Seats:       {stats['total_seats']}")
                print(f"  Booked:            {stats['booked_seats']}")
                print(f"  Available:         {stats['available_seats']}")
                print(f"  Occupancy Rate:    {stats['occupancy_rate']:.1f}%")
        except Exception as e:
            print(f"Could not fetch event stats: {e}")
        
        print(f"\n{'='*70}\n")

    def run_full_test(self):
        """Run the complete load test"""
        print("Starting Seat Booking Load Test...")
        print(f"API Base URL: {API_BASE_URL}\n")
        
        # Setup
        event_id = self.setup_test_event()
        if not event_id:
            print("Failed to setup test. Exiting.")
            return False
        
        # Get a seat to test
        seat_id = self.get_available_seat(event_id)
        if not seat_id:
            print("No available seats found. Exiting.")
            return False
        
        # Run concurrent test
        self.concurrent_booking_test(event_id, seat_id)
        
        # Print results
        self.print_results(event_id)
        
        return self.results['success'] == 1


if __name__ == '__main__':
    tester = BookingLoadTester()
    success = tester.run_full_test()
    exit(0 if success else 1)
