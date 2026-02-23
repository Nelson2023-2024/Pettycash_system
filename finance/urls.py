from django.urls import path, include
from .views import (create_expense_view, create_petty_cash_view, deactivate_expense_view,
  deactivate_petty_cash_view, get_all_petty_cash_view, get_petty_cash_view, list_all_expenses_view,
  list_my_expenses_view, update_expense_view, update_petty_cash_view)

urlpatterns = [
  path('petty_cash/create/',create_petty_cash_view, name='create-petty-cash-account'),
  path('petty_cash/', get_all_petty_cash_view, name='get-all-petty-cash-accounts'),
  path('petty_cash/<str:account_id>/', get_petty_cash_view, name='get-petty-cash-account'),
  path('petty_cash/<str:account_id>/update/', update_petty_cash_view, name='update-petty-cash-account'),
  path('petty_cash/<str:account_id>/deactivate/', deactivate_petty_cash_view, name='deactivate-petty-cash-account'),

  # ── expense requests ─────────────────────────────────────
  path('expense/create/', create_expense_view, name='create-expense-request'),
  path('expense/', list_all_expenses_view, name='list-all-expense-requests'),
  path('expense/mine/', list_my_expenses_view, name='list-my-expense-requests'),
  path('expense/<str:expense_id>/update/', update_expense_view, name='update-expense-request'),
  path('expense/<str:expense_request_id>/deactivate/', deactivate_expense_view, name='deactivate-expense-request'),
]
