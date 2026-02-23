
from base.models import Category, Status
from users.models import User
from audit.models import EventTypes

# EXPENSEREQUEST
def get_default_expense_category():
    """
    Auto-resolves the default category for an expense request.
    Returns the ID of the 'Expense Management' category,
    creating it if it doesn't exist.
    """
    category, _ = Category.objects.get_or_create(
        code='expense',
        defaults={
            'name': 'Expense Management',
            'description': 'Expense submission and approval workflow'
        }
    )
    return category.id


def get_default_pending_status():
    """
    Auto-resolves the default status for an expense request.
    Returns the ID of the 'Pending' status,
    creating it if it doesn't exist.
    """
    status, _ = Status.objects.get_or_create(
        code='pending',
        defaults={
            'name': 'Pending',
            'description': 'Awaiting review and approval'
        }
    )
    return status.id

def get_default_finance_officer():
    """
    Auto-resolves a default Finance Officer for an expense request.
    Returns the ID of the first active user with the FO role.
    Returns None if no Finance Officer exists.
    """
    
    officer = User.objects.filter(
        role__code='FO',
        is_active=True
    ).first()
    
    return officer.id if officer else None


def get_default_expense_submitted_event():
    """
    Auto-resolves the default event type for a newly submitted expense request.
    Returns the ID of the 'expense_submitted' event, creating it if it doesn't exist.
    """
       # local import to avoid circular imports
    category, _ = Category.objects.get_or_create(
        code='expense',
        defaults={
            'name': 'Expense Management',
            'description': 'Expense submission and approval workflow'
        }
    )
    event, _ = EventTypes.objects.get_or_create(
        code='expense_submitted',
        defaults={
            'name': 'Expense Submitted',
            'description': 'Employee submitted an expense request',
            'event_category': category,
        }
    )
    return event.id


def get_default_topup_requested_event():
    """
    Auto-resolves the default event type for a newly created top-up request.
    Returns the ID of the 'topup_requested' event, creating it if it doesn't exist.
    """
    category, _ = Category.objects.get_or_create(
        code='topup',
        defaults={
            'name': 'Top Up',
            'description': 'Petty cash top-up workflow'
        }
    )
    event, _ = EventTypes.objects.get_or_create(
        code='topup_requested',
        defaults={
            'name': 'Top Up Requested',
            'description': 'Finance Officer initiated a top-up request',
            'event_category': category,
        }
    )
    return event.id