from enum import Enum


class ApplicationStatus(str, Enum):
    Draft = "Draft"
    Pending = "Pending"           # Submitted by Customer
    UnderReview = "UnderReview"   # Picked up by Reviewer
    Accepted = "Accepted"         # Reviewer accepted
    Adjusted = "Adjusted"         # Reviewer requested adjustments
    Rejected = "Rejected"         # Reviewer or Approver rejected
    Rereview = "Rereview"         # Approver sent back for re-review
    Approved = "Approved"         # Final approval
    Cancelled = "Cancelled"       # Customer cancelled


class LicenseType(str, Enum):
    TradeLicense = "TradeLicense"


class ReviewAction(str, Enum):
    Accept = "Accept"
    Reject = "Reject"
    Adjust = "Adjust"


class ApprovalAction(str, Enum):
    Approve = "Approve"
    Reject = "Reject"
    Rereview = "Rereview"
