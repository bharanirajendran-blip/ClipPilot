"""Tests for Pydantic schemas and validation."""

import pytest
from pydantic import ValidationError
from app.models.schemas import CreateJobRequest, StyleEnum, DurationEnum, GuardrailResult


class TestCreateJobRequest:
    """Tests for CreateJobRequest validation."""

    def test_defaults(self):
        """Test that defaults are set correctly."""
        req = CreateJobRequest(topic="How solar panels work in detail")
        assert req.style == StyleEnum.educational
        assert req.duration == DurationEnum.thirty
        assert req.include_narration is True
        assert req.include_captions is True
        assert req.include_music is True
        assert req.music_url is None

    def test_all_options_disabled(self):
        """Test creating a job with all audio options disabled."""
        req = CreateJobRequest(
            topic="A robot finds a flower in a junkyard",
            style="storytelling",
            duration=30,
            include_narration=False,
            include_captions=False,
            include_music=False,
        )
        assert req.include_narration is False
        assert req.include_captions is False
        assert req.include_music is False

    def test_music_only_no_narration(self):
        """Test music-only mode (narration off, music on)."""
        req = CreateJobRequest(
            topic="Ocean waves and underwater life exploration",
            style="documentary",
            duration=60,
            include_narration=False,
            include_music=True,
        )
        assert req.include_narration is False
        assert req.include_music is True

    def test_topic_too_short(self):
        """Test that short topics are rejected."""
        with pytest.raises(ValidationError):
            CreateJobRequest(topic="Hi")

    def test_topic_too_long(self):
        """Test that topics over 500 chars are rejected."""
        with pytest.raises(ValidationError):
            CreateJobRequest(topic="x" * 501)


class TestStyleEnum:
    """Tests for StyleEnum values."""

    def test_all_styles_present(self):
        """Test that all expected styles exist."""
        expected = {"educational", "storytelling", "explainer", "documentary", "animated"}
        actual = {s.value for s in StyleEnum}
        assert actual == expected

    def test_news_style_removed(self):
        """Test that the old 'news' style no longer exists."""
        style_values = {s.value for s in StyleEnum}
        assert "news" not in style_values

    def test_documentary_style_exists(self):
        """Test that documentary style is valid."""
        req = CreateJobRequest(
            topic="Deep dive into ancient Roman architecture",
            style="documentary",
            duration=90,
        )
        assert req.style == StyleEnum.documentary

    def test_animated_style_exists(self):
        """Test that animated style is valid."""
        req = CreateJobRequest(
            topic="How DNA replication works inside your cells",
            style="animated",
            duration=30,
        )
        assert req.style == StyleEnum.animated

    def test_invalid_style_rejected(self):
        """Test that invalid styles are rejected."""
        with pytest.raises(ValidationError):
            CreateJobRequest(
                topic="Some valid topic for testing",
                style="news",
                duration=30,
            )


class TestDurationEnum:
    """Tests for DurationEnum values."""

    def test_all_durations_present(self):
        """Test that all expected durations exist."""
        expected = {30, 60, 90}
        actual = {d.value for d in DurationEnum}
        assert actual == expected

    def test_invalid_duration_rejected(self):
        """Test that invalid durations are rejected."""
        with pytest.raises(ValidationError):
            CreateJobRequest(
                topic="Some valid topic for testing",
                style="educational",
                duration=45,
            )


class TestGuardrailResult:
    """Tests for GuardrailResult model."""

    def test_safe_result(self):
        """Test a safe guardrail result."""
        result = GuardrailResult(is_safe=True)
        assert result.is_safe is True
        assert result.warnings == []

    def test_hard_block(self):
        """Test a hard block guardrail result."""
        result = GuardrailResult(
            is_safe=False,
            reason="Contains violent content",
            category="violence",
            severity="hard",
        )
        assert result.is_safe is False
        assert result.severity == "hard"

    def test_soft_warning(self):
        """Test a soft warning guardrail result."""
        result = GuardrailResult(
            is_safe=True,
            severity="soft",
            warnings=["Mild competitive language detected"],
        )
        assert result.is_safe is True
        assert len(result.warnings) == 1
