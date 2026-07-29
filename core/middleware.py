"""Middleware de journalisation des actions sensibles."""
from django.utils.deprecation import MiddlewareMixin


class ActionLogMiddleware(MiddlewareMixin):
    """Enregistre les POST authentifiés (hors admin/static)."""

    SKIP_PREFIXES = ("/static/", "/media/", "/admin/jsi18n/")

    def process_response(self, request, response):
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return response
        path = request.path
        if any(path.startswith(p) for p in self.SKIP_PREFIXES):
            return response
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return response
        if 200 <= response.status_code < 400:
            try:
                from core.models import ActionLog

                ActionLog.objects.create(
                    user=request.user,
                    action=f"{request.method} {path}",
                    path=path,
                    ip_address=self._client_ip(request),
                    details=f"status={response.status_code}",
                )
            except Exception:
                pass
        return response

    @staticmethod
    def _client_ip(request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
