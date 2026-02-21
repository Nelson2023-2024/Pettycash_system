
from base.models import Category, Status

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