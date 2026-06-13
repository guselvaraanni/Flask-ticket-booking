"""
Jinja2 templates for the TicketFlow UI.
"""

import os

from fastapi.templating import Jinja2Templates

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
templates = Jinja2Templates(directory=os.path.join(_ROOT, 'templates'))


def format_inr(value):
    try:
        amount = int(round(float(value or 0)))
    except (TypeError, ValueError):
        amount = 0
    return f'₹{amount:,}'


templates.env.filters['inr'] = format_inr
