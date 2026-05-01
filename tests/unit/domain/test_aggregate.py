import pytest

from src.domain.trade_license.aggregate import TradeLicenseApplication
from src.domain.trade_license.enums import (
    ApplicationStatus,
    ApprovalAction,
    ReviewAction,
)
from src.domain.trade_license.exceptions import DomainException
from src.domain.trade_license.value_objects import (
    AttachedDocument,
    BusinessDetails,
    PaymentRecord,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_application(**overrides) -> TradeLicenseApplication:
    defaults = dict(
        applicant_id="applicant-001",
        business_details=BusinessDetails(
            name="Test Biz",
            type="Electronics", 
            address="123 Main St", 
            capital=1000.0, 
            activity_description="Consumer electronics retail"
        ),
        attachments=[AttachedDocument(document_id="doc-1", file_name="reg.pdf", storage_uri="s3://bucket/reg.pdf")],
        payment=PaymentRecord(transaction_id="txn-001", amount=500.0, is_settled=True),
    )
    defaults.update(overrides)
    return TradeLicenseApplication.submit_new(**defaults)


# ── UC1: Submit ───────────────────────────────────────────────────────────────

class TestSubmitApplication:
    def test_submit_creates_pending_application(self):
        app = make_application()
        assert app.status == ApplicationStatus.Pending
        assert app.applicant_id == "applicant-001"

    def test_submit_raises_if_payment_not_settled(self):
        payment = PaymentRecord(transaction_id="txn-x", amount=100.0, is_settled=False)
        with pytest.raises(DomainException, match="Payment must be settled"):
            make_application(payment=payment)

    def test_submit_raises_if_no_attachments(self):
        with pytest.raises(DomainException, match="At least one attachment"):
            make_application(attachments=[])

    def test_submit_raises_business_type_empty(self):
        with pytest.raises(DomainException, match="Business type is required"):
            BusinessDetails(
                name="Test Biz",
                type="", 
                address="123 Main St",
                capital=100.0,
                activity_description="Something"
            )

    def test_submit_raises_payment_amount_zero(self):
        with pytest.raises(DomainException, match="Payment amount must be positive"):
            PaymentRecord(transaction_id="txn-x", amount=0, is_settled=True)

    def test_submit_emits_domain_event(self):
        app = make_application()
        events = app.pull_events()
        assert len(events) == 1
        assert events[0].__class__.__name__ == "ApplicationSubmittedEvent"

    def test_cancel_pending_application(self):
        app = make_application()
        app.pull_events()  # clear
        app.cancel(applicant_id="applicant-001")
        assert app.status == ApplicationStatus.Cancelled
        events = app.pull_events()
        assert events[0].__class__.__name__ == "ApplicationCancelledEvent"

    def test_cancel_raises_if_wrong_applicant(self):
        app = make_application()
        with pytest.raises(DomainException, match="Only the applicant"):
            app.cancel(applicant_id="intruder-999")

    def test_cancel_raises_if_not_pending(self):
        app = make_application()
        app.review(reviewer_id="rev-1", action=ReviewAction.Accept)
        with pytest.raises(DomainException, match="Only Pending"):
            app.cancel(applicant_id="applicant-001")


# ── UC2: Review ───────────────────────────────────────────────────────────────

class TestReviewApplication:
    def test_accept_moves_to_accepted(self):
        app = make_application()
        app.review(reviewer_id="rev-1", action=ReviewAction.Accept)
        assert app.status == ApplicationStatus.Accepted
        assert app.reviewer_id == "rev-1"

    def test_reject_moves_to_rejected(self):
        app = make_application()
        app.review(reviewer_id="rev-1", action=ReviewAction.Reject, note="Missing docs")
        assert app.status == ApplicationStatus.Rejected
        assert app.review_note == "Missing docs"

    def test_adjust_moves_to_adjusted(self):
        app = make_application()
        app.review(reviewer_id="rev-1", action=ReviewAction.Adjust, note="Update address")
        assert app.status == ApplicationStatus.Adjusted

    def test_review_raises_if_not_reviewable(self):
        app = make_application()
        app.review(reviewer_id="rev-1", action=ReviewAction.Accept)
        # Already Accepted — cannot review again
        with pytest.raises(DomainException, match="Cannot review"):
            app.review(reviewer_id="rev-1", action=ReviewAction.Accept)

    def test_review_emits_event(self):
        app = make_application()
        app.pull_events()
        app.review(reviewer_id="rev-1", action=ReviewAction.Accept)
        events = app.pull_events()
        assert events[0].__class__.__name__ == "ApplicationReviewedEvent"
        assert events[0].action == "Accept"


# ── UC3: Approve ─────────────────────────────────────────────────────────────

class TestProcessApproval:
    def _accepted_app(self) -> TradeLicenseApplication:
        app = make_application()
        app.review(reviewer_id="rev-1", action=ReviewAction.Accept)
        app.pull_events()
        return app

    def test_approve_moves_to_approved(self):
        app = self._accepted_app()
        app.process_approval(approver_id="appr-1", action=ApprovalAction.Approve)
        assert app.status == ApplicationStatus.Approved
        assert app.approver_id == "appr-1"

    def test_reject_moves_to_rejected(self):
        app = self._accepted_app()
        app.process_approval(approver_id="appr-1", action=ApprovalAction.Reject, note="Non-compliant")
        assert app.status == ApplicationStatus.Rejected
        assert app.approval_note == "Non-compliant"

    def test_rereview_moves_to_rereview(self):
        app = self._accepted_app()
        app.process_approval(approver_id="appr-1", action=ApprovalAction.Rereview)
        assert app.status == ApplicationStatus.Rereview

    def test_rereview_then_reviewer_can_review_again(self):
        app = self._accepted_app()
        app.process_approval(approver_id="appr-1", action=ApprovalAction.Rereview)
        app.review(reviewer_id="rev-1", action=ReviewAction.Accept)
        assert app.status == ApplicationStatus.Accepted

    def test_approval_raises_if_not_accepted(self):
        app = make_application()  # Still Pending
        with pytest.raises(DomainException, match="Only Accepted"):
            app.process_approval(approver_id="appr-1", action=ApprovalAction.Approve)

    def test_approval_emits_event(self):
        app = self._accepted_app()
        app.process_approval(approver_id="appr-1", action=ApprovalAction.Approve)
        events = app.pull_events()
        assert events[0].__class__.__name__ == "ApplicationApprovalProcessedEvent"
        assert events[0].action == "Approve"
