from utils.response_provider import ResponseProvider
from utils.common import get_clean_request_data
from services.services import ExpenseRequestService


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
                    "receipt_url",
                },
            )

            expense = ExpenseRequestService().create(
                title=data.get("titlee"),
                mpesa_phone=data.get("mpesa_phone"),
                description=data.get("description"),
                amount=data.get("amount"),
                employee=request.user,
                receipt_url=data.get("receipt_url"),
            )

            return ResponseProvider().success(
                message="Expense request created successfully",
                data=cls._serialize(expense),
            )
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @staticmethod
    def _serialize(expense) -> dict:
        return {
            "id": str(expense.id),
            "title": expense.title,
            "amount": expense.amount,
            "expense_type": expense.expense_type,
            "description": expense.description,
            "status": expense.expense.status.name if expense.status else None,
            "assigned_to": expense.assigned_to.email if expense.assigned_to else None,
            "created_at": expense.created_at.isoformat(),
        }
