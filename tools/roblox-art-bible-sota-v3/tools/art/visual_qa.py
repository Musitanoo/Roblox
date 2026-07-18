from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

# Machado, Oliveira & Fernandes (2009), severity 1.0 matrices.
MATRICES = {
    "protanopia": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]], dtype=np.float64),
    "deuteranopia": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]], dtype=np.float64),
    "tritanopia": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]], dtype=np.float64),
}


def srgb_to_linear(v: np.ndarray) -> np.ndarray:
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(v: np.ndarray) -> np.ndarray:
    return np.where(v <= 0.0031308, 12.92 * v, 1.055 * np.power(np.maximum(v, 0), 1 / 2.4) - 0.055)


def transform(rgb: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    linear = srgb_to_linear(rgb)
    simulated = np.einsum("...c,dc->...d", linear, matrix)
    return np.clip(linear_to_srgb(np.clip(simulated, 0, 1)), 0, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate grayscale and color-vision-deficiency evidence images.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(args.input).convert("RGB")
    rgb = np.asarray(image, dtype=np.float64) / 255.0
    outputs = []
    luminance = np.dot(srgb_to_linear(rgb), np.array([0.2126, 0.7152, 0.0722]))
    gray = np.clip(linear_to_srgb(luminance), 0, 1)
    gray_rgb = np.repeat(gray[..., None], 3, axis=-1)
    gray_path = args.output_dir / f"{args.input.stem}__grayscale.png"
    Image.fromarray((gray_rgb * 255 + 0.5).astype(np.uint8)).save(gray_path)
    outputs.append(gray_path.name)
    for name, matrix in MATRICES.items():
        out = transform(rgb, matrix)
        path = args.output_dir / f"{args.input.stem}__{name}.png"
        Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(path)
        outputs.append(path.name)
    report = {
        "status": "REQUIRES_HUMAN_REVIEW",
        "source": str(args.input),
        "outputs": outputs,
        "model": "Machado_2009_severity_1.0",
        "note": "Transforms are evidence views, not an automatic readability PASS. Shape/motion/audio redundancy remains mandatory.",
    }
    report_path = args.output_dir / f"{args.input.stem}__visual_qa.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[PASS] Generated {len(outputs)} visual QA views and a review-required report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
