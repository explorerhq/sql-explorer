from django.urls import path
from explorer.assistant.views import (TableDescriptionListView,
                                      TableDescriptionCreateView,
                                      TableDescriptionUpdateView,
                                      TableDescriptionDeleteView,
                                      AssistantHelpView,
                                      AssistantHistoryApiView)

assistant_urls = [
    path("assistant/", AssistantHelpView.as_view(), name="assistant"),
    path("assistant/history/", AssistantHistoryApiView.as_view(), name="assistant_history"),
    path("table-descriptions/", TableDescriptionListView.as_view(), name="table_description_list"),
    path("table-descriptions/new/", TableDescriptionCreateView.as_view(), name="table_description_create"),
    path("table-descriptions/<int:pk>/update/", TableDescriptionUpdateView.as_view(), name="table_description_update"),
    path("table-descriptions/<int:pk>/delete/", TableDescriptionDeleteView.as_view(), name="table_description_delete"),
]
