#!/usr/bin/env python
"""
Seed the database with portfolio demo events, seats, and sample bookings.

Usage:
    python seed_data.py
    python seed_data.py --reset
"""

import argparse
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.demo_seed import seed_database


def main():
    parser = argparse.ArgumentParser(description='Seed TicketFlow demo data')
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Clear existing demo events/seats/bookings before seeding',
    )
    parser.add_argument(
        '--no-bookings',
        action='store_true',
        help='Skip sample bookings',
    )
    args = parser.parse_args()

    app = create_app(os.getenv('FLASK_ENV', 'development'))

    with app.app_context():
        result = seed_database(
            reset=args.reset,
            include_sample_bookings=not args.no_bookings,
        )

    print('Seed complete:')
    for key, value in result.items():
        print(f'  {key}: {value}')


if __name__ == '__main__':
    main()
