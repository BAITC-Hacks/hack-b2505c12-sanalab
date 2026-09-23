from django.conf import settings
from django.db import models


class Proposal(models.Model):
    task = models.ForeignKey(
        "backend.BusinessRequest",
        on_delete=models.CASCADE,
        related_name="proposals",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_proposals",
    )
    solution = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task", "student"],
                name="one_proposal_per_student_per_task",
            ),
        ]