from services.services import NotificationService, PettyCashAccountService, UserService
from utils.response_provider import ResponseProvider
from utils.common import get_clean_request_data
from django.core.exceptions import ValidationError
from audit.models import Notifications, TransactionLogBase


class PettyCashService:

    @classmethod
    def create_petty_cash_account(cls, request) -> ResponseProvider:
        data = get_clean_request_data(
            request,
            required_fields={
                "name",
                "description",
                "mpesa_phone_number",
                "minimum_threshold",
            },
        )

        name = data.get("name")
        description = data.get("description")
        mpesa_phone_number = data.get("mpesa_phone_number")
        minimum_threshold = data.get("minimum_threshold")

        petty_cash, log = PettyCashAccountService().create_account(
            name,
            description,
            mpesa_phone_number,
            minimum_threshold,
            triggered_by=request.user,
            request=request,
        )

        NotificationService.notify_many(
            transaction_log=log,
            recipients=UserService().get_active_admin_fo_cfo(),
            channel=Notifications.Channel.IN_APP
        )

        return ResponseProvider.created(
            message=f"{petty_cash.name} account created successfully",
            data=cls._serialize(petty_cash),
        )

    @classmethod
    def get_petty_cash_account(cls, account_id: str):
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
    def update_petty_cash_account(cls, request, account_id: str):
        data = get_clean_request_data(
            request,
            allowed_fields={
                "name",
                "description",
                "mpesa_phone_number",
                "minimum_threshold",
                "account_type",
            },
        )

        petty_cash, log = PettyCashAccountService().update_account(
            account_id, data, triggered_by=request.user, request=request
        )
        NotificationService.notify(
            transaction_log=log,
            recipient=request.user,
            channel=Notifications.Channel.IN_APP,
        )
        return ResponseProvider.success(
            message=f"{petty_cash.name} updated successfully",
            data=cls._serialize(petty_cash),
        )

    @staticmethod
    def deactivate_petty_cash_account(request, account_id: str):
        petty_cash, log = PettyCashAccountService().deactivate_account(
            account_id, triggered_by=request.user, request=request
        )

        NotificationService.notify(
            transaction_log=log,
            recipient=request.user,
            channel=Notifications.Channel.IN_APP,
        )
        return ResponseProvider.success(
            message=f"{petty_cash.name} deactivated successfully"
        )

    @classmethod
    def get_account_activity(cls, request) -> ResponseProvider:
        """
        Retrieves all transaction logs related to the active petty cash account.
        Returns a full audit trail including:
        - Who triggered the transaction
        - Money before and after
        - Amount deducted/added
        - Date and time
        - Event type (disbursement, topup, deduction, etc.)
        """
        try:
            account = PettyCashAccountService().get_active_accounts().first()
            if not account:
                return ResponseProvider.not_found(
                    message="No active petty cash account found."
                )

            logs = (
                TransactionLogBase.objects.filter(
                    event_type__code__in=[
                        "petty_cash_balance_deducted",  # money out — expense disbursed
                        "topup_disbursed",  # # money in — topup credited
                    ],
                    metadata__account_id=str(account.id),
                )
                .select_related("triggered_by")
                .order_by("-created_at")
            )

            return ResponseProvider.success(
                data={
                    "account": cls._serialize(account),
                    "activity": [cls._serialize_log(log) for log in logs],
                }
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @staticmethod
    def _serialize(petty_cash) -> dict:
        """
        Converting a Django model → JSON-safe dictionary
        """
        return {
            "id": str(petty_cash.id),
            "name": petty_cash.name,
            "description": petty_cash.description,
            "mpesa_phone_number": petty_cash.mpesa_phone_number,
            "account_type": petty_cash.account_type,
            "current_balance": str(petty_cash.current_balance),
            "minimum_threshold": str(petty_cash.minimum_threshold),
            "is_active": petty_cash.is_active,
            "created_at": str(petty_cash.created_at),
            "updated_at": str(petty_cash.updated_at),
        }

    @staticmethod
    def _serialize_log(log) -> dict:
        metadata = log.metadata or {}
        return {
            "id": str(log.id),
            "event_code": log.event_type.code if log.event_type else None,
            "event_name": log.event_type.name if log.event_type else None,
            "message": log.event_message,
            "triggered_by": (
                {
                    "id": str(log.triggered_by.id),
                    "name": f"{log.triggered_by.first_name} {log.triggered_by.last_name}".strip(),
                    "email": log.triggered_by.email,
                }
                if log.triggered_by
                else None
            ),
            "created_at": log.created_at.isoformat(),
            "amount": metadata.get("amount") or metadata.get("amount_deducted"),
            "expense_amount": metadata.get("expense_amount"),
            "transaction_cost": metadata.get("transaction_cost"),
            "previous_balance": metadata.get("previous_balance"),
            "new_balance": metadata.get("new_balance"),
        }
