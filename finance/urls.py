from django.urls import path, include
from .views import create_petty_cash_view, get_all_petty_cash_view,get_petty_cash_view, update_petty_cash_view, deactivate_petty_cash_view

urlpatterns = [
  path('petty_cash/create/',create_petty_cash_view, name='create-petty-cash-account'),
  path('petty_cash/', get_all_petty_cash_view, name='get-all-petty-cash-accounts'),
  path('petty_cash/<str:account_id>/', get_petty_cash_view, name='get-petty-cash-account'),
  path('petty_cash/<str:account_id>/update/', update_petty_cash_view, name='update-petty-cash-account'),
  path('petty_cash/<str:account_id>/deactivate/', deactivate_petty_cash_view, name='deactivate-petty-cash-account'),
]
