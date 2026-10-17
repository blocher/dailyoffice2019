"""Timed transcripts (WebVTT and SRT) for podcast episodes, from the office audio timeline.

An episode is the combined track the in-app player plays, and the API view that
renders it already says where every spoken line falls in that track: the
``single_track`` has a span per line and the speech provider's timing for every
word, rescaled to the track's real length (``get_single_track`` in
``office/api/views/index.py``). A transcript is that timeline with each line's
printed text, so it needs no speech recognition and matches the audio exactly.

Cues are stored on the episode as ``[start, end, speaker, text]`` lists (seconds,
"Officiant"/"People"/"Reader" or ""), and rendered as WebVTT or SRT on request.
Long lines, such as a paragraph of a reading, are split into sentences, each
timed from its own words.
"""

import re
from collections import defaultdict
from html import escape

from office.audio_text import reading_text

SPEAKERS = {
    "leader": "Officiant",
    "leader_dialogue": "Officiant",
    "congregation": "People",
    "congregation_dialogue": "People",
    "reader": "Reader",
}
SOUNDS = {"audio_opening_bells": "[Bells]", "audio_closing_bells": "[Bells]"}
# Readings arrive as HTML holding several paragraphs, each spoken as its own clip
# and marked with the clip's line id.
LINE_MARKER = re.compile(r"<span data-line-id='([^']+)'></span>")
# Pointing marks (* between half verses, † at a line break) are for chanting.
POINTING = re.compile(r"\s*[*†]\s*")
# The divine name is printed LORD in small capitals ("Lᴏʀᴅ"); write plain letters.
SMALL_CAPITALS = str.maketrans("ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘʀꜱᴛᴜᴠᴡʏᴢ", "abcdefghijklmnoprstuvwyz")
SENTENCE_END = re.compile(r"(?:(?<=[.!?;:])|(?<=[.!?;:][\"”’')\]])|(?<=[.!?;:][\"”’')\]]{2}))\s+")
CLAUSE_END = re.compile(r"(?<=[,;:])\s+")
WORD = re.compile(r"[\w’']+")
CUE_CHARACTERS = 200


def clean(text):
    text = reading_text(text).translate(SMALL_CAPITALS)
    return re.sub(r"\s+", " ", POINTING.sub(" ", text)).strip()


def line_texts(data):
    """{line id: (text, line_type)} for every line the audio can speak."""
    texts = {}
    for module in data.get("modules") or []:
        for line in module.get("lines") or []:
            content = str(line.get("content") or "")
            kind = line.get("line_type") or ""
            parts = LINE_MARKER.split(content)
            if len(parts) > 1:
                # ['', id, html, id, html, ...]: one paragraph per spoken clip.
                for line_id, html in zip(parts[1::2], parts[2::2]):
                    texts[line_id] = (clean(html), "reader")
            elif line.get("id"):
                texts[line["id"]] = (clean(content), kind)
    # Lines only the audio has, such as the opening announcement.
    for track in (data.get("audio") or {}).get("tracks") or []:
        if track.get("line_id") and track.get("text") and track["line_id"] not in texts:
            texts[track["line_id"]] = (clean(track["text"]), "")
    return texts


def chunks(text):
    """``text`` in pieces of about CUE_CHARACTERS, broken at sentence ends (or clauses)."""
    if len(text) <= CUE_CHARACTERS:
        return [text]
    pieces = []
    for sentence in SENTENCE_END.split(text):
        pieces.extend(CLAUSE_END.split(sentence) if len(sentence) > CUE_CHARACTERS * 1.5 else [sentence])
    result = []
    for piece in filter(None, (piece.strip() for piece in pieces)):
        if result and len(result[-1]) + len(piece) < CUE_CHARACTERS:
            result[-1] = f"{result[-1]} {piece}"
        else:
            result.append(piece)
    return result


def timed(pieces, words, start, end):
    """[(start, end, piece)]: each piece timed from its share of the line's words.

    The provider's words don't always match the printed ones (numbers, hyphens),
    so pieces take the words in proportion to their own word counts.
    """
    if len(pieces) == 1:
        return [(start, end, pieces[0])]
    counts = [max(len(WORD.findall(piece)), 1) for piece in pieces]
    total = sum(counts)
    result = []
    done = 0
    for piece, count in zip(pieces, counts):
        first, last = done, done + count
        done = last
        if words:
            begin = words[min(round(first / total * len(words)), len(words) - 1)]["start_time"]
            index = max(round(last / total * len(words)) - 1, 0)
            finish = words[min(index, len(words) - 1)]["end_time"]
        else:
            begin = start + (end - start) * first / total
            finish = start + (end - start) * last / total
        result.append((begin, max(finish, begin), piece))
    return result


def cues(data, duration=None):
    """The episode's transcript as ``[start, end, speaker, text]`` cues, in order.

    ``data`` is the office API's response (``modules`` and ``audio``). Cues are
    kept within ``duration`` when it is given.
    """
    single_track = (data.get("audio") or {}).get("single_track") or []
    if len(single_track) < 5:
        return []
    spans, words = single_track[3], single_track[4]
    texts = line_texts(data)
    words_by_line = defaultdict(list)
    for word in words:
        words_by_line[word["id"]].append(word)

    result = []
    seen = set()
    for span in sorted(spans, key=lambda span: span["start_time"]):
        line_id = span["id"]
        if line_id in seen:
            continue
        seen.add(line_id)
        if line_id in SOUNDS:
            result.append([span["start_time"], span["end_time"], "", SOUNDS[line_id]])
            continue
        text, kind = texts.get(line_id, ("", ""))
        if not text:
            continue
        line_words = sorted(words_by_line.get(line_id, []), key=lambda word: word["start_time"])
        if line_words:
            start, end = line_words[0]["start_time"], line_words[-1]["end_time"]
            speaker = SPEAKERS.get(line_words[0].get("speaker"), SPEAKERS.get(kind, ""))
        else:
            start, end = span["start_time"], span["end_time"]
            speaker = SPEAKERS.get(kind, "")
        for begin, finish, piece in timed(chunks(text), line_words, start, end):
            result.append([begin, finish, speaker, piece])

    result.sort(key=lambda cue: cue[0])
    for index, cue in enumerate(result):
        # Never overlap the next cue, and never run past the audio.
        if index + 1 < len(result):
            cue[1] = min(cue[1], result[index + 1][0])
        if duration:
            cue[0], cue[1] = min(cue[0], duration), min(cue[1], duration)
        cue[0], cue[1] = round(cue[0], 3), round(max(cue[1], cue[0]), 3)
    return result


def timestamp(seconds, separator="."):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02}{separator}{milliseconds:03}"


def to_vtt(transcript):
    blocks = ["WEBVTT"]
    for index, (start, end, speaker, text) in enumerate(transcript, start=1):
        body = (
            f"<v {escape(speaker, quote=False)}>{escape(text, quote=False)}" if speaker else escape(text, quote=False)
        )
        blocks.append(f"{index}\n{timestamp(start)} --> {timestamp(end)}\n{body}")
    return "\n\n".join(blocks) + "\n"


def to_srt(transcript):
    blocks = []
    for index, (start, end, speaker, text) in enumerate(transcript, start=1):
        body = f"{speaker}: {text}" if speaker else text
        blocks.append(f"{index}\n{timestamp(start, ',')} --> {timestamp(end, ',')}\n{body}")
    return "\n\n".join(blocks) + "\n"
