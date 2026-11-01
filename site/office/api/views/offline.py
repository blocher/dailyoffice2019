from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from office import offline_content


class ContentChangesView(APIView):
    """What changed since a version, so devices can refresh offline downloads.

    ``GET /api/v1/content_changes?since=<version>``; see
    ``office.offline_content.changes_since``.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        try:
            since = max(int(request.query_params.get("since") or 0), 0)
        except (TypeError, ValueError):
            since = 0
        response = Response(offline_content.changes_since(since))
        # Every device asks on each sync; a minute of caching (browser and
        # Cloudflare) keeps that cheap and still shows an edit within a minute.
        response["Cache-Control"] = "public, max-age=60"
        return response
