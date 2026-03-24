from django.urls import path, include
from .views import (create_expense_view, create_petty_cash_view, create_topup_view,
  deactivate_expense_view, deactivate_petty_cash_view, deactivate_topup_view, decide_expense_view,
  decide_topup_view, disburse_expense_view, disburse_topup_view, get_all_petty_cash_view,
  get_expense_request_view, get_petty_cash_view, get_reconciliation_view, list_all_expenses_view,
  list_all_reconciliations_view, list_all_topups_view, list_my_expenses_view,
  list_my_reconciliations_view, list_my_topups_view, review_reconciliation_view,
  submit_reconciliation_receipt_view, update_expense_view, update_petty_cash_view,
  update_topup_view, get_petty_cash_activity_view,list_my_loans_view,disburse_loan_view,decide_loan_view,get_loan_view,mark_loan_repaid_view, create_loan_view, list_all_loans_view)

urlpatterns = [
  path('petty_cash/create/',create_petty_cash_view, name='create-petty-cash-account'),
  path('petty_cash/', get_all_petty_cash_view, name='get-all-petty-cash-accounts'),
  path("petty_cash/activity/", get_petty_cash_activity_view, name="get-petty-cash-activity",),
  path('petty_cash/<str:account_id>/', get_petty_cash_view, name='get-petty-cash-account'),
  path('petty_cash/<str:account_id>/update/', update_petty_cash_view, name='update-petty-cash-account'),
  path('petty_cash/<str:account_id>/deactivate/', deactivate_petty_cash_view, name='deactivate-petty-cash-account'),

  # ── expense requests ─────────────────────────────────────
  path('expense/create/', create_expense_view, name='create-expense-request'),
  path('expense/', list_all_expenses_view, name='list-all-expense-requests'),
  path('expense/mine/', list_my_expenses_view, name='list-my-expense-requests'),
  path("expense/<str:expense_id>/",get_expense_request_view, name='get-expense-request'),
  path('expense/<str:expense_id>/decide/', decide_expense_view, name='decide-expense-request'),
  path('expense/<str:expense_id>/disburse/', disburse_expense_view, name='disburse-expense-request'),
  path('expense/<str:expense_id>/update/', update_expense_view, name='update-expense-request'),
  path('expense/<str:expense_request_id>/deactivate/', deactivate_expense_view, name='deactivate-expense-request'),

  # ── top up requests ─────────────────────────────────────
  path('topup/<str:pettycash_account_id>/create/', create_topup_view, name='create-topup-request'),
  path('topup/', list_all_topups_view, name='list-all-topup-requests'),
  path('topup/mine/', list_my_topups_view, name='list-my-topup-requests'),
  path('topup/<str:topup_id>/decide/', decide_topup_view, name='decide-topup-request'),
  path('topup/<str:topup_id>/disburse/', disburse_topup_view, name='disburse-topup-request'),
  path('topup/<str:topup_id>/update/', update_topup_view, name='update-topup-request'),
  path('topup/<str:topup_id>/deactivate/', deactivate_topup_view, name='deactivate-topup-request'),

   # ── disbursement reconciliation ──────────────────────────
  path('reconciliation/', list_all_reconciliations_view, name='list-all-reconciliations'),
  path('reconciliation/mine/', list_my_reconciliations_view, name='list-my-reconciliations'),
  path('reconciliation/<str:reconciliation_id>/', get_reconciliation_view, name='get-reconciliation'),
  path('reconciliation/<str:reconciliation_id>/submit/', submit_reconciliation_receipt_view, name='submit-reconciliation-receipt'),
  path('reconciliation/<str:reconciliation_id>/review/', review_reconciliation_view, name='review-reconciliation'),

  path("loan/", list_all_loans_view, name="list-all-loans"),
  path("loan/mine/", list_my_loans_view, name="list-my-loans"),
  path("loan/create/", create_loan_view, name="create-loan"),
  path("loan/<str:loan_id>/", get_loan_view, name="get-loan"),
  path("loan/<str:loan_id>/decide/", decide_loan_view, name="decide-loan"),
  path("loan/<str:loan_id>/disburse/", disburse_loan_view, name="disburse-loan"),
  path("loan/<str:loan_id>/repaid/", mark_loan_repaid_view, name="mark-loan-repaid"),
]
