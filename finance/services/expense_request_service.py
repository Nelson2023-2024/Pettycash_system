from utils.response_provider import ResponseProvider
from utils.common import get_clean_request_data
from services.services import ExpenseRequestService
from finance.models import ExpenseRequest


class ExpenseRequestController:

    @classmethod
    def create_expense_request(cls, request):
        """
        Handles the creation of a new expense request for the authenticated employee.

        Validates and extracts required fields from the incoming request, delegates
        persistence to ExpenseRequestService, and returns a structured JSON response.

        Args:
            request: The HTTP request object. Must contain the following in the body:
                - expense_type (str): Type of expense — 'reimbursement' or 'disbursement'.
                - title (str): Short title describing the expense.
                - mpesa_phone (str): M-Pesa phone number for disbursement.
                - description (str): Detailed description of the expense.
                - amount (float): The monetary amount being requested.
                - receipt_url (list, optional): List of URLs pointing to uploaded receipts.

        Returns:
            JsonResponse: 201 Created with serialized expense data on success.
            JsonResponse: 400/409/500 etc. via ResponseProvider.handle_exception on failure.

        Raises:
            Exceptions are caught internally and routed through ResponseProvider.handle_exception.
        """

        try:
            data = get_clean_request_data(
                request,
                required_fields={
                    "expense_type",
                    "title",
                    "mpesa_phone",
                    "description",
                    "amount",
                },
                allowed_fields={
                    "expense_type",
                    "title",
                    "mpesa_phone",
                    "description",
                    "amount",
                },
            )

            # ADDED: validate expense_type against the allowed choices before hitting the service
            expense_type = data.get("expense_type")
            valid_expense_types = [
                choice.value for choice in ExpenseRequest.ExpenseType
            ]
            if expense_type not in valid_expense_types:
                raise ValueError(
                    f"Invalid expense_type '{expense_type}'. "
                    f"Allowed values are: {', '.join(valid_expense_types)}"
                )

            receipt = request.FILES.get("receipt")

            # Reimbursement must have a receipt at submission — disbursement submits later
            if expense_type == ExpenseRequest.ExpenseType.REIMBURSEMENT and not receipt:
                raise ValueError("A receipt is required for reimbursement requests.")

            expense = ExpenseRequestService().create(
                request=request,
                title=data.get("title"),
                mpesa_phone=data.get("mpesa_phone"),
                description=data.get("description"),
                amount=data.get("amount"),
                employee=request.user,
                expense_type=data.get("expense_type"),
                receipt=receipt,
            )

            return ResponseProvider().success(
                message="Expense request created successfully",
                data=cls._serialize(expense),
            )
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def get_all_expense_requests(cls, request):
        """
        Retrieves all active expense requests.

        Args:
            request: The HTTP request object.

        Returns:
            JsonResponse: 200 with list of serialized expense requests.
        """
        try:
            expenses = ExpenseRequestService().get_all()
            return ResponseProvider.success(
                data=[cls._serialize(expense) for expense in expenses]
            )
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def get_auth_user_expense_request(cls, request):
        """
        Retrieves all expense requests belonging to the authenticated employee.

        Args:
            request: The HTTP request object.

        Returns:
            JsonResponse: 200 with list of serialized expense requests.

        """
        try:
            authUser = request.user
            expenses = ExpenseRequestService().get_my_expense_requests(
                authUser=authUser
            )

            return ResponseProvider().success(
                data=[cls._serialize(expense) for expense in expenses]
            )

        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def update_expense_request(cls, request, expense_id):
        """
        Updates an existing expense request with the provided fields.

        Args:
            request: The HTTP request object.
            expense_id (str): The ID of the expense request to update.

        Returns:
            JsonResponse: 200 with serialized updated expense on success.

        """
        data = get_clean_request_data(
            request,
            allowed_fields={
                "expense_type",
                "title",
                "mpesa_phone",
                "description",
                "amount",
                "receipt_url",
            },
        )
        authUser = request.user
        try:
            # ADDED: validate expense_type on update too, but only if it was provided
            if "expense_type" in data:
                valid_expense_types = [
                    choice.value for choice in ExpenseRequest.ExpenseType
                ]
                if data["expense_type"] not in valid_expense_types:
                    raise ValueError(
                        f"Invalid expense_type '{data['expense_type']}'. "
                        f"Allowed values are: {', '.join(valid_expense_types)}"
                    )

            expense = ExpenseRequestService().update(
                triggered_by=authUser, request=request, expense_id=expense_id, data=data
            )

            return ResponseProvider().success(data=cls._serialize(expense))
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def deactivate_auth_expense_request(cls, request, expense_request_id):
        """
            Deactivates an expense request by setting is_active to False.

        Args:
            request: The HTTP request object.
            expense_request_id (str): The ID of the expense request to deactivate.

        Returns:
            JsonResponse: 200 with serialized deactivated expense on success.

        """
        authUser = request.user

        try:
            expense = ExpenseRequestService().deactivate(
                request=request,
                expense_request_id=expense_request_id,
                triggered_by=authUser,
            )
            return ResponseProvider().success(
                message="Expense Request Deactivated", data=cls._serialize(expense)
            )
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @staticmethod
    def _serialize(expense) -> dict:
        """
        Converting a Django model → JSON-safe dictionary
        """
        return {
            "id": str(expense.id),
            "title": expense.title,
            "amount": expense.amount,
            "expense_type": expense.expense_type,
            "description": expense.description,
            "status": expense.status.name if expense.status else None,
            "created_at": expense.created_at.isoformat(),
        }
