from services.services import PettyCashAccountService
from utils.response_provider import ResponseProvider
from utils.common import get_clean_request_data
from django.core.exceptions import ValidationError


class PettyCashService:

    @classmethod
    def create_petty_cash_account(cls,request) -> ResponseProvider:
        data = get_clean_request_data(request, required_fields={'name', 'description', 'mpesa_phone_number', 'minimum_threshold'})
        
        name = data.get('name')
        description = data.get('description')
        mpesa_phone_number = data.get('mpesa_phone_number')
        minimum_threshold=data.get('minimum_threshold')
        
        petty_cash = PettyCashAccountService().create_account(
            name,
            description,
            mpesa_phone_number,
            minimum_threshold,
            triggered_by=request.user,
            request=request
        )

        return ResponseProvider.created(message=f"{petty_cash.name} account created successfully", data=cls._serialize(petty_cash))

    @classmethod
    def get_petty_cash_account(cls,account_id: str):
        petty_cash = PettyCashAccountService().get_by_id(account_id)
        return ResponseProvider.success(data=cls._serialize(petty_cash))

    @classmethod
    def get_all_petty_cash_accounts(cls):
        accounts = PettyCashAccountService().get_active_accounts()
        data = []
        for account in accounts:
            data.append(cls._serialize(account))
        return ResponseProvider.success(data=data)

    @classmethod
    def update_petty_cash_account(cls,request, account_id: str):
        data = get_clean_request_data(
            request,
            allowed_fields={'name', 'description', 'mpesa_phone_number', 'minimum_threshold', 'account_type'}
        )

        petty_cash = PettyCashAccountService().update_account(account_id, data,triggered_by=request.user, request=request)
        return ResponseProvider.success(message=f"{petty_cash.name} updated successfully", data=cls._serialize(petty_cash))

    @staticmethod
    def deactivate_petty_cash_account(request,account_id: str):
        petty_cash = PettyCashAccountService().deactivate_account(account_id, triggered_by=request.user, request=request)
        return ResponseProvider.success(message=f"{petty_cash.name} deactivated successfully")


    @staticmethod
    def _serialize(petty_cash) -> dict:
        """
        Converting a Django model → JSON-safe dictionary 
        """
        return {
            'id': str(petty_cash.id),
            'name': petty_cash.name,
            'description': petty_cash.description,
            'mpesa_phone_number': petty_cash.mpesa_phone_number,
            'account_type': petty_cash.account_type,
            'current_balance': str(petty_cash.current_balance),
            'minimum_threshold': str(petty_cash.minimum_threshold),
            'is_active': petty_cash.is_active,
            'created_at': str(petty_cash.created_at),
            'updated_at': str(petty_cash.updated_at),
        }