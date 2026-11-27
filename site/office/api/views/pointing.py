"""Propose corrections to a verse's chant pointing from the app.

    GET  api/v1/psalms/<psalm>/verses/<verse>/pointing   the verse's syllables and marks
    POST api/v1/pointing/preview                          how a proposed pointing is sung
    POST api/v1/pointing/proposals                        send a proposal for an editor

A proposal only moves marks: removing them must give back the verse's text.
Editors accept or decline proposals in the admin (Psalter > Pointing proposals).
"""

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from psalter.chant import dictionary
from psalter.chant.notation import NotationError, parse, validate
from psalter.chant.pointing import point_verse, segments
from psalter.chant.service import verse_texts, verse_tone
from psalter.chant.tones import TONES, get_tone
from psalter.models import PointingProposal, PsalmVerse


def syllables(notation):
    """The notation as editable syllables: [{t: text, m: mark, w: starts a word}].

    ``m`` is one of "", "^" (bold), "~" (italic), "=" (underlined) for book
    tones, or "+" (stressed) for the others.
    """
    out = []
    for syllable in parse(notation):
        mark = "=" if syllable.double else "~" if syllable.slur else "^" if syllable.pointed else ""
        if not mark and syllable.accent:
            mark = "+"
        out.append({"t": syllable.text, "m": mark, "w": syllable.word_start})
    return out


def tone_choices():
    return [{"code": code, "label": tone.label, "book": tone.book} for code, tone in TONES.items()]


def _verse(psalm, verse):
    return get_object_or_404(PsalmVerse.objects.select_related("psalm", "pointing"), psalm__number=psalm, number=verse)


class PointingEditorView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, psalm, verse):
        verse = _verse(psalm, verse)
        pointing = getattr(verse, "pointing", None)
        tone = verse_tone(verse, pointing)
        first_text, second_text = verse_texts(verse)
        if pointing is not None:
            first, second = pointing.first_half_stress, pointing.second_half_stress
        else:
            first, second = dictionary.notate(first_text), dictionary.notate(second_text)
        return Response(
            {
                "psalm": verse.psalm.number,
                "verse": verse.number,
                "tone": tone.as_dict(),
                "tones": tone_choices(),
                "status": pointing.status if pointing else "",
                "source": pointing.source if pointing else "",
                "book_page": pointing.book_page if pointing else None,
                "first_half": syllables(first),
                "second_half": syllables(second),
            }
        )


class ProposalInput(serializers.Serializer):
    psalm = serializers.IntegerField(min_value=1, max_value=150)
    verse = serializers.IntegerField(min_value=1)
    first_half = serializers.CharField(max_length=1200)
    second_half = serializers.CharField(max_length=1200)
    tone = serializers.ChoiceField(choices=sorted(TONES), required=False, allow_blank=True)
    note = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)


def _checked(data):
    """The verse, notations and tone of a proposal, or raise a ValidationError."""
    verse = _verse(data["psalm"], data["verse"])
    first_text, second_text = verse_texts(verse)
    try:
        validate(data["first_half"], first_text)
        validate(data["second_half"], second_text)
    except NotationError as error:
        raise serializers.ValidationError({"detail": str(error)}) from error
    tone = get_tone(data.get("tone")) if data.get("tone") else verse_tone(verse)
    return verse, tone


class PointingPreviewView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = ProposalInput(data=request.data)
        data.is_valid(raise_exception=True)
        verse, tone = _checked(data.validated_data)
        first, second = point_verse(
            data.validated_data["first_half"],
            data.validated_data["second_half"],
            tone,
            first_verse=verse.number == 1,
        )
        return Response(
            {
                "first_half": segments(first, tone.clef),
                "second_half": segments(second, tone.clef),
                "warnings": first.warnings + second.warnings,
                "tone": tone.code,
            }
        )


class PointingProposalView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "pointing_proposal"

    def post(self, request):
        data = ProposalInput(data=request.data)
        data.is_valid(raise_exception=True)
        verse, tone = _checked(data.validated_data)
        pointing = getattr(verse, "pointing", None)
        values = data.validated_data
        if pointing is not None and (
            values["first_half"] == pointing.first_half_stress
            and values["second_half"] == pointing.second_half_stress
            and tone.code == verse_tone(verse, pointing).code
        ):
            raise serializers.ValidationError({"detail": "That is the pointing as it stands; nothing to propose."})
        proposal = PointingProposal.objects.create(
            verse=verse,
            first_half_stress=values["first_half"],
            second_half_stress=values["second_half"],
            tone=tone.code,
            previous_first_half=pointing.first_half_stress if pointing else "",
            previous_second_half=pointing.second_half_stress if pointing else "",
            note=values.get("note", ""),
            name=values.get("name", ""),
            email=values.get("email", ""),
        )
        return Response({"id": str(proposal.id), "status": proposal.status}, status=201)
