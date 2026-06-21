from django.db import models


class Notification(models.Model):
    TYPE_TRANSACTION_VERIFICATION = "transaction_verification"
    TYPE_TRANSACTION_AGREED = "transaction_agreed"
    TYPE_TRANSACTION_REJECTED = "transaction_rejected"
    TYPE_TRANSACTION_REPAYMENT = "transaction_repayment"
    TYPE_DUE_SOON = "due_soon"
    TYPE_OVERDUE = "overdue"
    TYPE_FRIEND_REQUEST = "friend_request"
    TYPE_FRIEND_ACCEPTED = "friend_accepted"

    TYPE_CHOICES = (
        (TYPE_TRANSACTION_VERIFICATION, "Transaction Verification"),
        (TYPE_TRANSACTION_AGREED, "Transaction Agreed"),
        (TYPE_TRANSACTION_REJECTED, "Transaction Rejected"),
        (TYPE_TRANSACTION_REPAYMENT, "Transaction Repayment"),
        (TYPE_DUE_SOON, "Due Soon"),
        (TYPE_OVERDUE, "Overdue"),
        (TYPE_FRIEND_REQUEST, "Friend Request"),
        (TYPE_FRIEND_ACCEPTED, "Friend Accepted"),
    )

    id = models.BigAutoField(primary_key=True)
    recipient_id = models.UUIDField(db_index=True)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    payload = models.JSONField(default=dict)
    is_cleared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(
                fields=["recipient_id", "is_cleared", "created_at"],
                name="notif_rec_clear_created_idx",
            ),
            models.Index(fields=["type", "created_at"], name="notif_type_created_idx"),
        ]

    @property
    def should_repeat_on_login(self) -> bool:
        return (
            self.type in {self.TYPE_DUE_SOON, self.TYPE_OVERDUE} and not self.is_cleared
        )
