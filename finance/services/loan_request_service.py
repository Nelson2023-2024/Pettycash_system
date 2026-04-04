from django.core.exceptions import ValidationError
from utils.response_provider import ResponseProvider
from utils.common import get_clean_request_data
from services.services import LoanRequestService, NotificationService, UserService
from decimal import Decimal


class LoanController:

    @classmethod
    def create(cls, request) -> ResponseProvider:
        try:
            data = get_clean_request_data(
                request,
                required_fields={"amount", "reason",'phone_number'},
                allowed_fields={"amount", "reason", 'phone_number'},
            )

            # ── Validate amount is positive ───────────────
            amount = Decimal(str(data.get("amount")))
            if amount <= 0:
                raise ValueError("Loan amount must be greater than 0.")

            loan, log = LoanRequestService().create(
                employee=request.user,
                amount=amount,
                reason=data.get("reason", ""),
                request=request,
                phone_number=data.get("phone_number")
            )
            return ResponseProvider.created(
                message="Loan request submitted successfully.",
                data=cls._serialize(loan),
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def get_all(cls, request) -> ResponseProvider:
        try:
            loans = LoanRequestService().get_all()
            return ResponseProvider.success(
                data=[cls._serialize(loan) for loan in loans]
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def get_my_loans(cls, request) -> ResponseProvider:
        try:
            loans = LoanRequestService().get_my_loans(employee=request.user)
            return ResponseProvider.success(
                data=[cls._serialize(loan) for loan in loans]
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def get_by_id(cls, request, loan_id: str) -> ResponseProvider:
        try:
            loan = LoanRequestService().get_by_id(loan_id)
            return ResponseProvider.success(data=cls._serialize(loan))
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def decide(cls, request, loan_id: str) -> ResponseProvider:
        """FO approves or rejects a pending loan."""
        try:
            data = get_clean_request_data(
                request,
                required_fields={"decision"},
                allowed_fields={"decision", "decision_reason"},
            )

            decision = data.get("decision")
            if decision not in ["approved", "rejected"]:
                raise ValueError("Decision must be 'approved' or 'rejected'.")

            # ── Status guard — controller responsibility ──
            loan = LoanRequestService().get_by_id(loan_id)
            if loan.status.code != "pending":
                raise ValueError(
                    f"Only pending loans can be approved or rejected. "
                    f"Current status: '{loan.status.name}'."
                )

            loan, log = LoanRequestService().decide(
                loan_id=loan_id,
                decision=decision,
                triggered_by=request.user,
                decision_reason=data.get("decision_reason", ""),
                request=request,
            )

            NotificationService.notify(
                transaction_log=log,
                recipient=loan.employee,
            )

            return ResponseProvider.success(
                message=f"Loan {decision} successfully.",
                data=cls._serialize(loan),
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def disburse(cls, request, loan_id: str) -> ResponseProvider:
        """CFO disburses an approved loan."""
        try:
            # ── Status guard — controller responsibility ──
            loan = LoanRequestService().get_by_id(loan_id)
            if loan.status.code != "approved":
                raise ValueError(
                    f"Only approved loans can be disbursed. "
                    f"Current status: '{loan.status.name}'."
                )

            loan, log = LoanRequestService().disburse(
                loan_id=loan_id,
                triggered_by=request.user,
                request=request,
            )

            NotificationService.notify(
                transaction_log=log,
                recipient=loan.employee,
            )

            return ResponseProvider.success(
                message="Loan disbursed successfully.",
                data=cls._serialize(loan),
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def mark_repaid(cls, request, loan_id: str) -> ResponseProvider:
        """CFO marks a loan as repaid after M-Pesa confirmation."""
        try:
            # ── Status guard — controller responsibility ──
            loan = LoanRequestService().get_by_id(loan_id)
            if loan.status.code != "disbursed":
                raise ValueError(
                    f"Only disbursed loans can be marked as repaid. "
                    f"Current status: '{loan.status.name}'."
                )

            loan = LoanRequestService().mark_repaid(
                loan_id=loan_id,
                triggered_by=request.user,
                request=request,
            )

            return ResponseProvider.success(
                message="Loan marked as repaid. Petty cash credited.",
                data=cls._serialize(loan),
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def deactivate(cls, request, loan_id: str) -> ResponseProvider:
        """Employee cancels a loan request."""
        try:
            loan = LoanRequestService().deactivate(
                loan_id=loan_id,
                triggered_by=request.user,
                request=request,
            )

            return ResponseProvider.success(
                message="Loan request cancelled successfully.",
                data=cls._serialize(loan),
            )

        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def update(cls, request, loan_id: str) -> ResponseProvider:
        """Employee updates a pending loan request."""
        try:
            data = get_clean_request_data(
                request,
                allowed_fields={"amount", "reason"},
            )

            loan = LoanRequestService().get_by_id(loan_id)
            if loan.status.code != "pending":
                raise ValueError(
                    f"Only pending loans can be updated. "
                    f"Current status: '{loan.status.name}'."
                )

            loan, log = LoanRequestService().update(
                loan_id=loan_id,
                data=data,
                triggered_by=request.user,
                request=request,
            )
            return ResponseProvider.success(
                message="Loan updated successfully.",
                data=cls._serialize(loan),
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @staticmethod
    def _serialize(loan) -> dict:
        return {
            "id": str(loan.id),
            "amount": str(loan.amount),
            "reason": loan.reason,
            "due_date": loan.due_date.isoformat() if loan.due_date else None,
            "repaid_at": loan.repaid_at.isoformat() if loan.repaid_at else None,
            "decision_reason": loan.decision_reason,
            "phone_number": loan.phone_number,
            "is_active": loan.is_active,
            "created_at": loan.created_at.isoformat(),
            "updated_at": loan.updated_at.isoformat(),
            # ── Status ────────────────────────────────────
            "status": loan.status.name if loan.status else None,
            "status_code": loan.status.code if loan.status else None,
            # ── Employee ──────────────────────────────────
            "employee": {
                "id": str(loan.employee.id),
                "name": f"{loan.employee.first_name} {loan.employee.last_name}".strip(),
                "email": loan.employee.email,
            },
            # ── Decision by ───────────────────────────────
            "decision_by": (
                {
                    "id": str(loan.decision_by.id),
                    "name": f"{loan.decision_by.first_name} {loan.decision_by.last_name}".strip(),
                    "email": loan.decision_by.email,
                }
                if loan.decision_by
                else None
            ),
            # ── Financial details from metadata ───────────
            "transaction_cost": loan.metadata.get("transaction_cost"),
            "total_deduction": loan.metadata.get("total_deduction"),
            "previous_balance": loan.metadata.get("previous_balance"),
            "new_balance": loan.metadata.get("new_balance"),
            "disbursed_at": loan.metadata.get("disbursed_at"),
        }
