"""Serve completed local audio files with browser-compatible byte ranges."""

import os
import re

from django.http import FileResponse, HttpResponse, HttpResponseNotFound, StreamingHttpResponse


def audio_file_response(media_root, filename, range_header="", if_range=""):
    # Resolve symlinks as well as '..'; provider subfolders remain supported.
    root = os.path.realpath(media_root)
    path = os.path.realpath(os.path.join(root, filename))
    if os.path.commonpath([root, path]) != root or not os.path.isfile(path):
        return HttpResponseNotFound("Audio file not found.")
    try:
        source = open(path, "rb")
    except OSError:
        return HttpResponseNotFound("Audio file not found.")
    size = os.fstat(source.fileno()).st_size
    if not size:
        source.close()
        return HttpResponseNotFound("Audio file not found.")

    # Without a validator to compare, If-Range must fall back to the entire
    # representation. Unsupported multi-ranges may likewise be ignored.
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip()) if not if_range else None
    if match and any(match.groups()):
        first, last = match.groups()
        start = _range_integer(first, size) if first else max(size - _range_integer(last, size), 0)
        end = min(_range_integer(last, size), size - 1) if first and last else size - 1
        if start >= size or start > end or (not first and _range_integer(last, size) == 0):
            source.close()
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{size}"
            response["Accept-Ranges"] = "bytes"
            return response
        source.seek(start)
        length = end - start + 1
        response = StreamingHttpResponse(_read_window(source, length), status=206, content_type="audio/mpeg")
        # Close even if the response is discarded before iteration starts.
        response._resource_closers.append(source.close)
        response["Content-Range"] = f"bytes {start}-{end}/{size}"
        response["Content-Length"] = str(length)
    else:
        response = FileResponse(source, content_type="audio/mpeg")
        response["Content-Length"] = str(size)
    response["Accept-Ranges"] = "bytes"
    return response


def _read_window(source, length, chunk_size=64 * 1024):
    try:
        remaining = length
        while remaining:
            chunk = source.read(min(chunk_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk
    finally:
        source.close()


def _range_integer(value, size):
    # Bound untrusted decimal headers before int(), preserving leading zeroes.
    value = value.lstrip("0") or "0"
    return size + 1 if len(value) > len(str(size)) else int(value)
