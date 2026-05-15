import base64
import os
from dataclasses import dataclass, field
from decimal import Decimal

import requests
from django.conf import settings
from django.utils import timezone

from office.models import AudioGenerationConfig, AudioGenerationEvent


class AudioProviderError(Exception):
    pass


@dataclass
class ProviderResult:
    characters: int = 0
    cost_units: Decimal = Decimal("0")
    request_id: str | None = None
    metadata: dict = field(default_factory=dict)
    voice_segments: list = field(default_factory=list)
    alignment: dict | None = None


def _request_id_from_headers(headers):
    for header in ("request-id", "x-request-id", "xi-request-id"):
        if headers.get(header):
            return headers[header]
    return None


class BaseAudioProvider:
    provider_name = ""

    def __init__(self, config):
        self.config = config

    @property
    def model_id(self):
        raise NotImplementedError

    def generate_spoken_file(self, text, voice_id, output_path):
        raise NotImplementedError

    def generate_dialogue_file(self, inputs, output_path):
        if len(inputs) != 1:
            raise NotImplementedError
        item = inputs[0]
        return self.generate_spoken_file(item["text"], item["voice_id"], output_path)

    def generate_sound_file(self, prompt, output_path, duration_seconds=None):
        raise NotImplementedError


class OpenAIAudioProvider(BaseAudioProvider):
    provider_name = "openai"

    @property
    def model_id(self):
        return self.config.openai_model

    def generate_spoken_file(self, text, voice_id, output_path):
        from openai import OpenAI

        client = OpenAI()
        response = client.audio.speech.create(
            model=self.config.openai_model,
            voice=voice_id,
            input=text,
        )
        response.stream_to_file(output_path)
        return ProviderResult(characters=len(text), metadata={"voice_id": voice_id})


class ElevenLabsV3AudioProvider(BaseAudioProvider):
    provider_name = "elevenlabs"
    base_url = "https://api.elevenlabs.io"

    @property
    def model_id(self):
        return self.config.elevenlabs_model_id

    @property
    def api_key(self):
        return getattr(settings, "ELEVENLABS_API_KEY", None) or os.getenv("ELEVENLABS_API_KEY", "")

    @property
    def headers(self):
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _raise_for_response(self, response):
        if response.status_code < 400:
            return
        message = response.text
        try:
            message = response.json()
        except ValueError:
            pass
        raise AudioProviderError(f"ElevenLabs request failed ({response.status_code}): {message}")

    def generate_dialogue_file(self, inputs, output_path):
        payload = {
            "inputs": inputs,
            "model_id": "eleven_v3",
            "apply_text_normalization": self.config.elevenlabs_apply_text_normalization,
        }
        if self.config.elevenlabs_language_code:
            payload["language_code"] = self.config.elevenlabs_language_code
        if self.config.elevenlabs_seed is not None:
            payload["seed"] = self.config.elevenlabs_seed

        response = requests.post(
            f"{self.base_url}/v1/text-to-dialogue/with-timestamps",
            headers=self.headers,
            params={"output_format": self.config.elevenlabs_output_format},
            json=payload,
            timeout=180,
        )
        self._raise_for_response(response)
        data = response.json()
        audio_base64 = data.get("audio_base64", "")
        with open(output_path, "wb") as audio_file:
            audio_file.write(base64.b64decode(audio_base64))

        characters = sum(len(item.get("text", "")) for item in inputs)
        return ProviderResult(
            characters=characters,
            cost_units=Decimal(response.headers.get("character-cost", characters) or characters),
            request_id=_request_id_from_headers(response.headers),
            metadata={
                "endpoint": "/v1/text-to-dialogue/with-timestamps",
                "output_format": self.config.elevenlabs_output_format,
                "input_count": len(inputs),
            },
            voice_segments=data.get("voice_segments", []),
            alignment=data.get("alignment"),
        )

    def generate_spoken_file(self, text, voice_id, output_path):
        return self.generate_dialogue_file([{"text": text, "voice_id": voice_id}], output_path)

    def generate_sound_file(self, prompt, output_path, duration_seconds=None):
        payload = {
            "text": prompt,
            "loop": self.config.sound_loop,
            "prompt_influence": float(self.config.sound_prompt_influence),
            "model_id": self.config.elevenlabs_sound_model_id,
        }
        if duration_seconds is not None:
            payload["duration_seconds"] = float(duration_seconds)

        response = requests.post(
            f"{self.base_url}/v1/sound-generation",
            headers=self.headers,
            params={"output_format": self.config.elevenlabs_output_format},
            json=payload,
            timeout=180,
        )
        try:
            self._raise_for_response(response)
        except AudioProviderError as exc:
            if self.config.elevenlabs_sound_model_id == "eleven_v3":
                raise AudioProviderError(
                    "ElevenLabs rejected model_id='eleven_v3' for /v1/sound-generation. "
                    "The configured model was not changed automatically."
                ) from exc
            raise

        with open(output_path, "wb") as audio_file:
            audio_file.write(response.content)

        return ProviderResult(
            characters=len(prompt),
            cost_units=Decimal(response.headers.get("character-cost", len(prompt)) or len(prompt)),
            request_id=_request_id_from_headers(response.headers),
            metadata={
                "endpoint": "/v1/sound-generation",
                "output_format": self.config.elevenlabs_output_format,
                "loop": self.config.sound_loop,
                "prompt_influence": str(self.config.sound_prompt_influence),
                "model_id": self.config.elevenlabs_sound_model_id,
            },
        )


class ElevenLabsStudioAudioProvider(ElevenLabsV3AudioProvider):
    """Studio placeholder.

    Studio is request-only. Until access is granted, the factory falls back to
    the public ElevenLabs v3 provider and records the health-check result.
    """

    def health_check(self):
        response = requests.get(
            f"{self.base_url}/v1/studio/projects",
            headers={"xi-api-key": self.api_key},
            timeout=30,
        )
        if response.status_code < 400:
            return True, None
        return False, response.text


def get_audio_provider(config=None):
    config = config or AudioGenerationConfig.get_solo()
    if config.provider_mode == AudioGenerationConfig.ProviderMode.OPENAI:
        return OpenAIAudioProvider(config), config.provider_mode

    if config.provider_mode == AudioGenerationConfig.ProviderMode.ELEVENLABS_STUDIO:
        if not config.elevenlabs_studio_enabled:
            AudioGenerationEvent.objects.create(
                action=AudioGenerationEvent.Action.FALLBACK,
                provider="elevenlabs",
                provider_mode=config.provider_mode,
                generation_type="studio",
                model_id="eleven_v3",
                metadata={"reason": "Studio mode is selected but the Studio toggle is off."},
            )
            return ElevenLabsV3AudioProvider(config), AudioGenerationConfig.ProviderMode.ELEVENLABS_V3

        studio_provider = ElevenLabsStudioAudioProvider(config)
        ok, error = studio_provider.health_check()
        config.elevenlabs_studio_access_granted = ok
        config.elevenlabs_studio_last_checked = timezone.now()
        config.elevenlabs_studio_last_error = "" if ok else error
        config.save(
            update_fields=[
                "elevenlabs_studio_access_granted",
                "elevenlabs_studio_last_checked",
                "elevenlabs_studio_last_error",
                "updated",
            ]
        )
        AudioGenerationEvent.objects.create(
            action=AudioGenerationEvent.Action.HEALTH_CHECK,
            provider="elevenlabs",
            provider_mode=config.provider_mode,
            generation_type="studio",
            model_id="eleven_v3",
            metadata={"studio_access_granted": ok},
            error_message=error,
        )
        if ok:
            return studio_provider, config.provider_mode
        AudioGenerationEvent.objects.create(
            action=AudioGenerationEvent.Action.FALLBACK,
            provider="elevenlabs",
            provider_mode=config.provider_mode,
            generation_type="studio",
            model_id="eleven_v3",
            metadata={"reason": "Studio API access was not granted."},
            error_message=error,
        )
        return ElevenLabsV3AudioProvider(config), AudioGenerationConfig.ProviderMode.ELEVENLABS_V3

    return ElevenLabsV3AudioProvider(config), AudioGenerationConfig.ProviderMode.ELEVENLABS_V3
