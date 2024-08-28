from django.db import models
from django.conf import settings
from explorer.ee.db_connections.models import DatabaseConnection


class PromptLog(models.Model):

    class Meta:
        app_label = "explorer"

    prompt = models.TextField(blank=True)
    user_request = models.TextField(blank=True)
    response = models.TextField(blank=True)
    run_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    run_at = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(blank=True, null=True)  # seconds
    model = models.CharField(blank=True, max_length=128, default="")
    error = models.TextField(blank=True, null=True)
    database_connection = models.ForeignKey(to=DatabaseConnection, on_delete=models.SET_NULL, blank=True, null=True)


class TableDescription(models.Model):

    class Meta:
        app_label = "explorer"
        unique_together = ("database_connection", "table_name")

    database_connection = models.ForeignKey(to=DatabaseConnection, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=512)
    description = models.TextField()

    def __str__(self):
        return f"{self.database_connection.alias} - {self.table_name}"
