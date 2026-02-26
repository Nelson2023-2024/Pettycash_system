from utils.response_provider import ResponseProvider
from utils.common import get_clean_request_data
from services.services import DisbursementReconciliationService
from decimal import Decimal, InvalidOperation


class DisbursementReconciliationController:

    @classmethod
    def get_my_reconciliations(cls, request):
        """
        Retrieves all reconciliations for the authenticated employee
        regardless of status — full history in one call.

        Args:
            request: The HTTP request object.

        Returns:
            JsonResponse: 200 with list of serialized reconciliations.
        """
        try:
            reconciliations = DisbursementReconciliationService().get_my_reconciliations(
                auth_user=request.user
            )
            return ResponseProvider.success(
                data=[cls._serialize(r) for r in reconciliations]
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def get_all_reconciliations(cls, request):
        """
        Retrieves all reconciliations across all employees.
        Intended for Finance Officer use.

        Args:
            request: The HTTP request object.

        Returns:
            JsonResponse: 200 with list of serialized reconciliations.
        """
        try:
            reconciliations = DisbursementReconciliationService().get_all_reconciliations()
            return ResponseProvider.success(
                data=[cls._serialize(r) for r in reconciliations]
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def get_reconciliation(cls, request, reconciliation_id: str):
        """
        Retrieves a single reconciliation by ID.
        Used for detail view on both employee and FO side.

        Args:
            request: The HTTP request object.
            reconciliation_id (str): The UUID of the reconciliation.

        Returns:
            JsonResponse: 200 with serialized reconciliation on success.
        """
        try:
            reconciliation = DisbursementReconciliationService().get_by_id(
                reconciliation_id=reconciliation_id
            )
            return ResponseProvider.success(data=cls._serialize(reconciliation))
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def submit_reconciliation_receipt(cls, request, reconciliation_id: str):
        """
        Employee submits receipt after cash has been disbursed.
        Requires reconciled_amount and surplus_returned in the request body.
        Receipt is uploaded as a file via multipart/form-data.

        Args:
            request: The HTTP request object. Must contain:
                - reconciled_amount (Decimal): Amount actually spent.
                - surplus_returned (Decimal): Cash being returned if underspent.
                - comments (str, optional): Notes from the employee.
                - receipt (file): The uploaded receipt file.

        Returns:
            JsonResponse: 200 with serialized updated reconciliation on success.
        """
        try:
            data = get_clean_request_data(
                request,
                required_fields={"reconciled_amount", "surplus_returned"},
                allowed_fields={"reconciled_amount", "surplus_returned", "comments"},
            )
            # convert to Decimal here — request data always comes in as strings
            try:
                reconciled_amount = Decimal(str(data.get("reconciled_amount")))
                surplus_returned = Decimal(str(data.get("surplus_returned")))
            except InvalidOperation:
                raise ValueError("reconciled_amount and surplus_returned must be valid numbers.")

            receipt = request.FILES.get("receipt")
            if not receipt:
                raise ValueError("A receipt file is required for reconciliation.")

            reconciliation = DisbursementReconciliationService().submit_receipt(
                request=request,
                reconciliation_id=reconciliation_id,
                submitted_by=request.user,
                receipt=receipt,
                reconciled_amount=reconciled_amount,
                surplus_returned=surplus_returned,
                comments=data.get("comments"),
            )

            return ResponseProvider.success(
                message="Reconciliation submitted successfully.",
                data=cls._serialize(reconciliation),
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def review_reconciliation(cls, request, reconciliation_id: str):
        """
        Finance Officer reviews a submitted reconciliation.
        Approves (completed) or rejects (sends back to employee for resubmission).

        Args:
            request: The HTTP request object. Must contain:
                - decision (str): 'completed' or 'rejected'.
                - comments (str, optional): Feedback. Required on rejection
                  so the employee knows what to fix.

        Returns:
            JsonResponse: 200 with serialized updated reconciliation on success.
        """
        try:
            data = get_clean_request_data(
                request,
                required_fields={"decision"},
                allowed_fields={"decision", "comments"},
            )

            decision = data.get("decision")
            if decision not in ["completed", "rejected"]:
                raise ValueError("Decision must be 'completed' or 'rejected'.")

            reconciliation = DisbursementReconciliationService().review(
                request=request,
                reconciliation_id=reconciliation_id,
                decision=decision,
                triggered_by=request.user,
                comments=data.get("comments"),
            )

            return ResponseProvider.success(
                message=f"Reconciliation {decision} successfully.",
                data=cls._serialize(reconciliation),
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @staticmethod
    def _serialize(reconciliation) -> dict:
        """
        Converting a DisbursementReconciliation model → JSON-safe dictionary.
        """
        return {
            "id": str(reconciliation.id),
            "expense_request_id": str(reconciliation.expense_request.id),
            "expense_request_title": reconciliation.expense_request.title,
            "disbursed_amount": str(reconciliation.expense_request.amount),
            "reconciled_amount": str(reconciliation.reconciled_amount) if reconciliation.reconciled_amount else None,
            "surplus_returned": str(reconciliation.surplus_returned) if reconciliation.surplus_returned else None,
            "comments": reconciliation.comments,
            "status": reconciliation.status.name if reconciliation.status else None,
            "submitted_by": reconciliation.submitted_by.email,
            "approved_by": reconciliation.approved_by.email if reconciliation.approved_by else None,
            "approved_at": reconciliation.approved_at.isoformat() if reconciliation.approved_at else None,
            "receipt": reconciliation.receipt.url if reconciliation.receipt else None,
            "is_active": reconciliation.is_active,
            "created_at": str(reconciliation.created_at),
            "updated_at": str(reconciliation.updated_at),
        }