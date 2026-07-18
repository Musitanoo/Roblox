from __future__ import annotations


def srgb_to_linear(value: float) -> float:
    if not 0.0 <= value <= 1.0:
        raise ValueError("sRGB channel must be inside 0..1")
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def hex_to_linear_rgba(value: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    normalized = value.removeprefix("#")
    if len(normalized) != 6:
        raise ValueError("color must be a six-digit hexadecimal sRGB value")
    try:
        srgb = tuple(int(normalized[index : index + 2], 16) / 255.0 for index in (0, 2, 4))
    except ValueError as exc:
        raise ValueError("color must be a six-digit hexadecimal sRGB value") from exc
    return tuple(srgb_to_linear(channel) for channel in srgb) + (alpha,)
