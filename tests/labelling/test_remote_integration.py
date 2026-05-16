"""Spec §10 integration tests — RemoteVlmLabeller against respx-mocked /detect."""
from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from src.labelling import Detection, LabelOutput, LabellerConfig, LabellerError
from src.labelling.remote_labeller import (
    MalformedResponseError,
    RemoteVlmLabeller,
)


@pytest.fixture
def cfg(tmp_path) -> LabellerConfig:
    return LabellerConfig(
        name="grounding-dino",
        mode="remote-vlm",
        endpoint="http://localhost:8000",
        model="grounding-dino-base",
        remote_image_root="/home/threenicorn/data",
        local_image_root=str(tmp_path),
        classes=["duct", "ruler", "whitepaper", "sitetag"],
        prompts={c: c for c in ("duct", "ruler", "whitepaper", "sitetag")},
        per_class_threshold={c: 0.25 for c in ("duct", "ruler", "whitepaper", "sitetag")},
        timeout_seconds=2.0,
        retries=2,
    )


@pytest.fixture
def image(tmp_path) -> Path:
    p = tmp_path / "foo.jpg"
    p.write_bytes(b"\xff\xd8\xff\xe0")  # JPEG magic; content not parsed
    return p


def _valid_response_body() -> dict:
    return {
        "detections": [
            {"cls": "duct", "bbox": [0.5, 0.4, 0.2, 0.3], "confidence": 0.91}
        ],
        "model": "grounding-dino-base",
        "image_size": [1200, 1600],
        "latency_ms": 87,
    }


@respx.mock
def test_success_returns_label_output(cfg, image):
    respx.post("http://localhost:8000/detect").mock(
        return_value=httpx.Response(200, json=_valid_response_body())
    )
    labeller = RemoteVlmLabeller(cfg)
    output = labeller.label(image)
    assert isinstance(output, LabelOutput)
    assert output.filename == "foo.jpg"
    assert output.image_size == (1200, 1600)
    assert len(output.detections) == 1
    assert output.detections[0].cls == "duct"
    assert output.detections[0].confidence == pytest.approx(0.91)


@respx.mock
def test_503_then_200_retries_and_succeeds(cfg, image, monkeypatch):
    # Speed up backoff for the test.
    import src.labelling.remote_labeller as rl
    monkeypatch.setattr(rl, "_backoff_seconds", lambda _: 0.0)

    responses = [
        httpx.Response(503, json={"error": "oom"}),
        httpx.Response(200, json=_valid_response_body()),
    ]
    respx.post("http://localhost:8000/detect").mock(side_effect=responses)
    labeller = RemoteVlmLabeller(cfg)
    output = labeller.label(image)
    assert output.detections[0].cls == "duct"


@respx.mock
def test_all_retries_exhausted_raises_labeller_error(cfg, image, monkeypatch):
    import src.labelling.remote_labeller as rl
    monkeypatch.setattr(rl, "_backoff_seconds", lambda _: 0.0)

    respx.post("http://localhost:8000/detect").mock(
        return_value=httpx.Response(503, json={"error": "oom"})
    )
    labeller = RemoteVlmLabeller(cfg)
    with pytest.raises(LabellerError, match="503"):
        labeller.label(image)


@respx.mock
def test_400_is_not_retried_and_raises_labeller_error(cfg, image):
    respx.post("http://localhost:8000/detect").mock(
        return_value=httpx.Response(400, text="bad request")
    )
    labeller = RemoteVlmLabeller(cfg)
    with pytest.raises(LabellerError, match="400"):
        labeller.label(image)


@respx.mock
def test_malformed_json_response_raises_malformed_response_error(cfg, image):
    bad_body = {
        "detections": [{"cls": "duct"}],  # missing bbox + confidence
        "model": "grounding-dino-base",
        "image_size": [1200, 1600],
        "latency_ms": 87,
    }
    respx.post("http://localhost:8000/detect").mock(
        return_value=httpx.Response(200, json=bad_body)
    )
    labeller = RemoteVlmLabeller(cfg)
    with pytest.raises(MalformedResponseError):
        labeller.label(image)


@respx.mock
def test_bbox_out_of_range_raises_malformed_response_error(cfg, image):
    bad_body = _valid_response_body()
    bad_body["detections"][0]["bbox"] = [1.2, 0.4, 0.2, 0.3]  # xc > 1
    respx.post("http://localhost:8000/detect").mock(
        return_value=httpx.Response(200, json=bad_body)
    )
    labeller = RemoteVlmLabeller(cfg)
    with pytest.raises(MalformedResponseError):
        labeller.label(image)


@respx.mock
def test_unknown_class_in_response_is_dropped(cfg, image):
    body = _valid_response_body()
    body["detections"].append(
        {"cls": "weird_class", "bbox": [0.1, 0.1, 0.1, 0.1], "confidence": 0.5}
    )
    respx.post("http://localhost:8000/detect").mock(
        return_value=httpx.Response(200, json=body)
    )
    labeller = RemoteVlmLabeller(cfg)
    output = labeller.label(image)
    # Only duct survives; weird_class dropped silently with a WARN.
    assert len(output.detections) == 1
    assert output.detections[0].cls == "duct"


@respx.mock
def test_health_check_ok(cfg):
    respx.get("http://localhost:8000/health").mock(
        return_value=httpx.Response(
            200, json={"status": "ok", "model": "grounding-dino-base", "uptime_s": 12,
                       "image_root": "/r", "images_under_root": 500},
        )
    )
    labeller = RemoteVlmLabeller(cfg)
    assert labeller.health_check() is True


@respx.mock
def test_health_check_bad_status(cfg):
    respx.get("http://localhost:8000/health").mock(
        return_value=httpx.Response(503)
    )
    labeller = RemoteVlmLabeller(cfg)
    assert labeller.health_check() is False


@respx.mock
def test_health_check_connect_error(cfg):
    respx.get("http://localhost:8000/health").mock(
        side_effect=httpx.ConnectError("refused")
    )
    labeller = RemoteVlmLabeller(cfg)
    assert labeller.health_check() is False


def test_image_path_not_under_local_root_raises(cfg, tmp_path):
    elsewhere = tmp_path.parent / "other_dir" / "x.jpg"
    elsewhere.parent.mkdir(parents=True, exist_ok=True)
    elsewhere.write_bytes(b"\xff\xd8\xff\xe0")
    labeller = RemoteVlmLabeller(cfg)
    with pytest.raises(LabellerError, match="not under local_image_root"):
        labeller.label(elsewhere)
