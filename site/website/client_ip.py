"""The address a request really came from.

In production a request reaches Django like this:

    client -> Cloudflare -> nginx -> gunicorn (listening on 127.0.0.1 only)

nginx sets ``X-Real-IP`` to whoever connected to it, overwriting anything the
client sent, and gunicorn can only be reached through nginx, so that header
can be trusted. When nginx's peer is Cloudflare, Cloudflare's own
``CF-Connecting-IP`` names the client. The server also answers requests that
skip Cloudflare (its address isn't firewalled), so ``CF-Connecting-IP`` is only
believed from Cloudflare's addresses.

``X-Forwarded-For`` is never used: clients write its first entries, and
Cloudflare and nginx only append to it.

Without nginx (local development) it is ``REMOTE_ADDR``.
"""

import ipaddress

# https://www.cloudflare.com/ips/ (checked 2026-11-01; it rarely changes).
CLOUDFLARE_NETWORKS = [
    ipaddress.ip_network(network)
    for network in (
        "173.245.48.0/20",
        "103.21.244.0/22",
        "103.22.200.0/22",
        "103.31.4.0/22",
        "141.101.64.0/18",
        "108.162.192.0/18",
        "190.93.240.0/20",
        "188.114.96.0/20",
        "197.234.240.0/22",
        "198.41.128.0/17",
        "162.158.0.0/15",
        "104.16.0.0/13",
        "104.24.0.0/14",
        "172.64.0.0/13",
        "131.0.72.0/22",
        "2400:cb00::/32",
        "2606:4700::/32",
        "2803:f800::/32",
        "2405:b500::/32",
        "2405:8100::/32",
        "2a06:98c0::/29",
        "2c0f:f248::/32",
    )
]


def parse_ip(value):
    try:
        return ipaddress.ip_address((value or "").strip())
    except ValueError:
        return None


def is_cloudflare(address):
    return any(address in network for network in CLOUDFLARE_NETWORKS if network.version == address.version)


def client_ip(request):
    """The client's address as a string, or ``""`` when it can't be told."""
    peer = parse_ip(request.META.get("HTTP_X_REAL_IP")) or parse_ip(request.META.get("REMOTE_ADDR"))
    if peer is None:
        return ""
    if is_cloudflare(peer):
        client = parse_ip(request.META.get("HTTP_CF_CONNECTING_IP"))
        if client is not None:
            return str(client)
    return str(peer)


class ClientIpThrottleMixin:
    """For DRF throttles: count by ``client_ip`` rather than ``X-Forwarded-For``."""

    def get_ident(self, request):
        return client_ip(request) or super().get_ident(request)
