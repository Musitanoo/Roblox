from __future__ import annotations

import argparse
import json
import math


def projected_pixels(thickness: float, distance: float, vertical_fov_degrees: float, viewport_height: int) -> float:
    if thickness <= 0 or distance <= 0 or not (0 < vertical_fov_degrees < 180) or viewport_height <= 0:
        raise ValueError("thickness, distance and viewport height must be positive; FOV must be in (0, 180)")
    angular_size = 2.0 * math.atan(thickness / (2.0 * distance))
    return viewport_height * angular_size / math.radians(vertical_fov_degrees)


def required_thickness(pixels: float, distance: float, vertical_fov_degrees: float, viewport_height: int) -> float:
    if pixels <= 0 or distance <= 0 or not (0 < vertical_fov_degrees < 180) or viewport_height <= 0:
        raise ValueError("pixels, distance and viewport height must be positive; FOV must be in (0, 180)")
    angular_size = pixels / viewport_height * math.radians(vertical_fov_degrees)
    return 2.0 * distance * math.tan(angular_size / 2.0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exact screen-space calibration for a vertical field of view.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_pixels = sub.add_parser("pixels")
    p_pixels.add_argument("--thickness", type=float, required=True)
    p_pixels.add_argument("--distance", type=float, required=True)
    p_pixels.add_argument("--fov", type=float, required=True)
    p_pixels.add_argument("--height", type=int, required=True)

    p_thickness = sub.add_parser("thickness")
    p_thickness.add_argument("--pixels", type=float, required=True)
    p_thickness.add_argument("--distance", type=float, required=True)
    p_thickness.add_argument("--fov", type=float, required=True)
    p_thickness.add_argument("--height", type=int, required=True)

    args = parser.parse_args()
    if args.command == "pixels":
        value = projected_pixels(args.thickness, args.distance, args.fov, args.height)
        result = {"projectedPixels": value}
    else:
        value = required_thickness(args.pixels, args.distance, args.fov, args.height)
        result = {"requiredThicknessStuds": value}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
