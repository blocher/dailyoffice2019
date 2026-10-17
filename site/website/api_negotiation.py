from rest_framework.exceptions import NotAcceptable
from rest_framework.negotiation import DefaultContentNegotiation


class FirstRendererFallbackNegotiation(DefaultContentNegotiation):
    """Serve the view's first renderer when nothing matches the Accept header.

    A request that only accepts text/html gets JSON rather than a 406. An
    unknown `?format=` still raises 404.
    """

    def select_renderer(self, request, renderers, format_suffix=None):
        try:
            return super().select_renderer(request, renderers, format_suffix)
        except NotAcceptable:
            format = format_suffix or request.query_params.get(self.settings.URL_FORMAT_OVERRIDE)
            if format:
                renderers = self.filter_renderers(renderers, format)
            return renderers[0], renderers[0].media_type
