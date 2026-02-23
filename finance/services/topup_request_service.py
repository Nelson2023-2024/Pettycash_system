from finance.models import TopUpRequest
from utils.response_provider import ResponseProvider
from utils.common import get_clean_request_data
from services.services import TopUpRequestService


class TopUpRequestController:

    @classmethod
    def create(cls, request, pettycash_account_id: str) -> ResponseProvider:
        """
        Handles creation of a new top-up request for a petty cash account.

        Args:
            request: HTTP request. Body must contain:
                - amount (float): The amount to top up.
                - request_reason (str): Reason for the top-up request.
            pettycash_account_id (str): The ID of the petty cash account to top up.

        Returns:
            JsonResponse: 201 on success, 400/500 on failure.
        """

        data = get_clean_request_data(
            request,
            required_fields={"amount", "request_reason"},
            allowed_fields={"amount", "request_reason"},
        )

        try:
            topup = TopUpRequestService().create_top_up_request(
                request=request,
                pettycash_account_id=pettycash_account_id,
                requested_by=request.user,
                request_reason=data.get("request_reason"),
                amount=data.get("amount"),
            )
            return ResponseProvider().created(
                message=f"Topup Request created successfully",
                data=cls._serialize(topup),
            )
        except Exception as e:
            return ResponseProvider().handle_exception(ex=e)

    @classmethod
    def list_all(cls, request):
        """
        Retrieves all active top-up requests.

        Args:
            request: The HTTP request object.

        Returns:
            JsonResponse: 200 with list of serialized top-up requests.

        """
        try:
            topups = TopUpRequestService().get_all()
            return ResponseProvider().success(
                data=[cls._serialize(topup) for topup in topups]
            )
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def list_auth_user_requests(cls, request):
        """
        Retrieves all active top-up requests made by the authenticated user.

        Args:
            request: The HTTP request object.

        Returns:
            JsonResponse: 200 with list of serialized top-up requests.

        """
        try:
            topups = TopUpRequestService().get_authuser_top_up_requests(
                auth_user=request.user
            )

            return ResponseProvider().success(
                data=[cls._serialize(topup) for topup in topups]
            )

        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def decide(cls, request, topup_id: str):
        """
        Approves or rejects a top-up request.

        Args:
            request: HTTP request. Body must contain:
                - decision (str): Either 'approved' or 'rejected'.
                - decision_reason (str, optional): Reason for the decision.
            topup_id (str): The ID of the top-up request.

        Returns:
            JsonResponse: 200 on success, 400/500 on failure.
        """
        data = get_clean_request_data(
            request,
            required_fields={"decision"},
            allowed_fields={"decision", "decision_reason"},
        )

        try:
            decision = data.get("decision")

            VALID_DECISIONS = {"approve", "reject"}

            if decision not in VALID_DECISIONS:
                raise ValueError(
                    f"Invalid decision '{decision}'. Must be one of {VALID_DECISIONS}."
                )

            topup = TopUpRequestService().decide_top_up_request(
                topup_id=topup_id,
                decision=decision,
                decision_reason=data.get("decision_reason"),
                triggered_by=request.user,
                request=request,
            )
            return ResponseProvider().success(
                message=f"Top-up request {data.get('decision')} successfully",
                data=cls._serialize(topup),
            )
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def disburse(cls, request, topup_id: str):
        """
        Disburses an approved top-up request.

        Args:
            request: The HTTP request object.
            topup_id (str): The ID of the top-up request to disburse.

        Returns:
            JsonResponse: 200 on success, 400/500 on failure.
        """
        try:
            topup = TopUpRequestService().disburse_top_up_request(
                topup_id=topup_id, triggered_by=request.user, request=request
            )

            return ResponseProvider().success(
                message="Top-up request disbursed successfully",
                data=cls._serialize(topup),
            )

        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def update(cls, request, topup_id: str):
        """
        Updates a pending top-up request with the provided fields.

        Args:
            request: HTTP request. Body may contain:
                - amount (float, optional): Updated amount.
                - request_reason (str, optional): Updated reason.
            topup_id (str): The ID of the top-up request to update.

        Returns:
            JsonResponse: 200 on success, 400/500 on failure.
        """

        try:

            data = get_clean_request_data(
                request, required_fields={}, allowed_fields={"amount", "request_reason"}
            )

            topup = TopUpRequestService().update_topup_request(
                topup_id=topup_id, data=data, triggered_by=request.user, request=request
            )
            return ResponseProvider.success(
                message="Top-up request updated successfully",
                data=cls._serialize(topup),
            )

        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def deactivate(cls, request, topup_id: str):
        """
        Soft deletes a top-up request by setting is_active to False.

        Args:
            request: The HTTP request object.
            topup_id (str): The ID of the top-up request to deactivate.

        Returns:
            JsonResponse: 200 on success, 400/500 on failure.
        """
        try:
            topup = TopUpRequestService().deactivate_top_up_request(
                topup_id=topup_id,
                triggered_by=request.user,
                request=request,
            )

            return ResponseProvider.success(
                message="Top-up request deactivated successfully",
                data=cls._serialize(topup),
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @staticmethod
    def _serialize(topup) -> dict:
        """
        Converting a Django model → JSON-safe dictionary
        """
        return {
            "id": str(topup.id),
            "account_name": topup.pettycash_account.name,
            "amount": str(topup.amount),
            "request_reason": topup.request_reason,
            "decision_reason": topup.decision_reason,
            "status": topup.status.name if topup.status else None,
            "event_type": topup.event_type.code if topup.event_type else None,
            "requested_by": topup.requested_by.email,
            "decision_by": topup.decision_by.email if topup.decision_by else None,
            "is_auto_triggered": topup.is_auto_triggered,
            "is_active": topup.is_active,
            "created_at": topup.created_at.isoformat(),
        }
