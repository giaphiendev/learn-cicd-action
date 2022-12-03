from django.urls import re_path
from django.http import HttpResponse

app_name = "api.webhooks"


def health_webhook(request):
    return HttpResponse("webhook ok")


urlpatterns = [
    re_path(r"^$", health_webhook, name="check_health_webhook"),
]
