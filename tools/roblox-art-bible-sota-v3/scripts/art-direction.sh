#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMAND="${1:-validate}"
shift || true

resolve_python() {
  if [[ -n "${ART_PYTHON:-}" ]] && "$ART_PYTHON" --version >/dev/null 2>&1; then
    printf '%s\n' "$ART_PYTHON"
    return
  fi
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    printf '%s\n' "$ROOT/.venv/bin/python"
    return
  fi
  local candidate
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" --version >/dev/null 2>&1; then
      command -v "$candidate"
      return
    fi
  done
  echo "Python 3 was not found. Set ART_PYTHON." >&2
  exit 127
}

resolve_blender() {
  if [[ -n "${ART_BLENDER:-}" ]] && "$ART_BLENDER" --version >/dev/null 2>&1; then
    printf '%s\n' "$ART_BLENDER"
    return
  fi
  if command -v blender >/dev/null 2>&1; then
    command -v blender
    return
  fi
  if [[ -x /Applications/Blender.app/Contents/MacOS/Blender ]]; then
    printf '%s\n' /Applications/Blender.app/Contents/MacOS/Blender
    return
  fi
  echo "Blender was not found. Set ART_BLENDER." >&2
  exit 127
}

run_python() {
  local label="$1"
  shift
  echo "> $label"
  "$PYTHON" "$@"
}

PYTHON="$(resolve_python)"
cd "$ROOT"

case "$COMMAND" in
  bootstrap)
    if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
      "$PYTHON" -m venv "$ROOT/.venv"
    fi
    PYTHON="$ROOT/.venv/bin/python"
    "$PYTHON" -m pip install --disable-pip-version-check --requirement "$ROOT/requirements-dev.txt"
    run_python "Pinned Python dependencies" -m tools.art.check_dependencies
    ;;
  doctor)
    echo "=== Art-direction doctor ==="
    "$PYTHON" --version
    run_python "Pinned Python dependencies" -m tools.art.check_dependencies
    echo "Root: $ROOT"
    if BLENDER="$(resolve_blender 2>/dev/null)"; then
      "$BLENDER" --version | head -n 2
      echo "Blender: $BLENDER"
    else
      echo "Blender execution status: BLOCKED_IN_THIS_ENVIRONMENT"
    fi
    run_python "Static validation" -m tools.art.validate_library --report evidence/static-validation-report.json
    ;;
  precanon-init)
    [[ $# -ge 3 ]] || { echo "Usage: $0 precanon-init BRIEF REQUEST_ID OUTPUT [STAGE] [MAX_GENERATIONS] [BROWSER_ADAPTER]" >&2; exit 2; }
    run_python "Compile precanonical packet" -m tools.art.precanonical init \
      --brief "$1" --request-id "$2" --output "$3" \
      --stage "${4:-exploration}" --maximum-generations "${5:-4}" \
      --browser-adapter "${6:-codex_chrome}"
    ;;
  precanon-preflight)
    [[ $# -ge 1 ]] || { echo "Usage: $0 precanon-preflight REQUEST [OUTPUT]" >&2; exit 2; }
    args=(-m tools.art.precanonical preflight "$1")
    [[ $# -ge 2 ]] && args+=(--output "$2")
    run_python "Validate prompt, hashes, budget and authority" "${args[@]}"
    ;;
  precanon-handoff)
    [[ $# -ge 3 ]] || { echo "Usage: $0 precanon-handoff REQUEST PREFLIGHT OUTPUT" >&2; exit 2; }
    run_python "Prepare Web transport handoff without submission" \
      -m tools.art.precanonical handoff "$1" --preflight "$2" --output "$3"
    ;;
  precanon-import)
    [[ $# -ge 4 ]] || { echo "Usage: $0 precanon-import REQUEST RESULT_ID OUTPUT IMAGE..." >&2; exit 2; }
    request="$1"
    result_id="$2"
    output="$3"
    shift 3
    args=(-m tools.art.precanonical import "$request" --result-id "$result_id" --output "$output")
    for image in "$@"; do args+=(--image "$image"); done
    run_python "Import downloaded image with conservative provenance" "${args[@]}"
    ;;
  precanon-review)
    [[ $# -ge 4 ]] || { echo "Usage: $0 precanon-review RESULT REVIEW_ID DECISION OUTPUT [ASSESSMENT] [REVIEWER]" >&2; exit 2; }
    args=(-m tools.art.precanonical review "$1" --review-id "$2" --decision "$3" --output "$4")
    [[ $# -ge 5 ]] && args+=(--assessment "$5")
    [[ $# -ge 6 ]] && args+=(--reviewer "$6")
    run_python "Record bounded result decision" "${args[@]}"
    ;;
  precanon-status)
    [[ $# -ge 1 ]] || { echo "Usage: $0 precanon-status REQUEST" >&2; exit 2; }
    run_python "Inspect request, results and reviews" -m tools.art.precanonical status "$1"
    ;;
  validate)
    run_python "Pinned Python dependencies" -m tools.art.check_dependencies
    run_python "Generated-code drift check" -m tools.art.generate_luau --check
    run_python "Schema and semantic validation" -m tools.art.validate_library --report evidence/static-validation-report.json
    ;;
  generate)
    run_python "Pinned Python dependencies" -m tools.art.check_dependencies
    run_python "Generate Luau from canonical JSON" -m tools.art.generate_luau
    run_python "Post-generation validation" -m tools.art.validate_library --report evidence/static-validation-report.json
    ;;
  test)
    run_python "Pinned Python dependencies" -m tools.art.check_dependencies
    run_python "pytest" -m pytest
    ;;
  validate-luau)
    command -v stylua >/dev/null || { echo "stylua is required" >&2; exit 127; }
    command -v selene >/dev/null || { echo "selene is required" >&2; exit 127; }
    command -v luau-lsp >/dev/null || { echo "luau-lsp is required" >&2; exit 127; }
    mapfile -t hand_authored < <(find studio/src studio/plugin -type f -name '*.luau' -print | sort)
    stylua --config-path studio/tooling/stylua.toml --verify --check "${hand_authored[@]}"
    selene --config studio/tooling/selene.toml "${hand_authored[@]}"
    luau-lsp analyze --platform roblox --definitions "@roblox=$ROOT/studio/tooling/globalTypes.d.luau" \
      studio/src/AssetKitStager.luau studio/src/GoldenSceneBuilder.luau \
      studio/src/GoldenSceneValidator.luau studio/src/LightingProfileService.luau \
      studio/generated/ArtDirectionConfig.luau studio/generated/LightingProfiles.luau \
      studio/generated/TerritoryStyles.luau
    echo "[PASS] Luau static validation completed."
    ;;
  build)
    RENDER_MODE="${1:-smoke}"
    BLENDER="$(resolve_blender)"
    run_python "Pre-build validation" -m tools.art.validate_library --report evidence/static-validation-report.json
    for territory in industrial-toy-defense salvaged-frontier clean-tactical-diorama; do
      echo "> Blender build: $territory"
      "$BLENDER" --background --factory-startup --threads 1 --python-exit-code 19 \
        --python tools/blender/build_art_direction.py -- \
        --root "$ROOT" --territory "$territory" --render-mode "$RENDER_MODE"
      validation_args=(-m tools.art.validate_build_report "build/$territory/build-report.json")
      [[ "$RENDER_MODE" == "full" ]] && validation_args+=(--require-complete)
      run_python "Validate Blender report: $territory" "${validation_args[@]}"
    done
    echo "[PASS] Blender builds completed. Studio, physical-device, and human evidence remain separate gates."
    ;;
  verify-blender)
    BLENDER="$(resolve_blender)"
    run_python "Pinned Python dependencies" -m tools.art.check_dependencies
    run_python "Verify Blender builds and determinism" -m tools.art.verify_blender --blender "$BLENDER"
    ;;
  measure-visual)
    run_python "Pinned Python dependencies" -m tools.art.check_dependencies
    run_python "Measure current full-build visual quality" -m tools.art.measure_visual_quality
    ;;
  validate-studio)
    [[ $# -ge 1 ]] || { echo "Usage: $0 validate-studio REPORT [--require-pass]" >&2; exit 2; }
    args=(-m tools.art.validate_studio_report "$1")
    [[ "${2:-}" == "--require-pass" ]] && args+=(--require-pass)
    run_python "Validate Studio Golden Scene report" "${args[@]}"
    ;;
  bind-studio-captures)
    [[ $# -ge 1 ]] || { echo "Usage: $0 bind-studio-captures REPORT" >&2; exit 2; }
    run_python "Bind Studio captures to report" -m tools.art.bind_studio_captures "$1"
    ;;
  validate-mobile)
    [[ $# -ge 1 ]] || { echo "Usage: $0 validate-mobile REPORT [--require-pass]" >&2; exit 2; }
    args=(-m tools.art.validate_performance_report "$1")
    [[ "${2:-}" == "--require-pass" ]] && args+=(--require-pass)
    run_python "Validate physical-device mobile report" "${args[@]}"
    ;;
  validate-simulator)
    [[ $# -ge 1 ]] || { echo "Usage: $0 validate-simulator REPORT [--require-pass]" >&2; exit 2; }
    args=(-m tools.art.validate_studio_simulator_report "$1")
    [[ "${2:-}" == "--require-pass" ]] && args+=(--require-pass)
    run_python "Validate Studio simulator report" "${args[@]}"
    ;;
  package)
    run_python "Run complete static verification" -m tools.art.verify_static --output evidence/static-verification-report.json
    run_python "Validate fresh verification evidence" -m tools.art.validate_library --report evidence/static-validation-report.json
    output="${1:-$ROOT/../roblox-art-bible-sota-v3.zip}"
    run_python "Build deterministic release archive" -m tools.art.package_release --output "$output"
    ;;
  evidence-index)
    [[ $# -ge 1 ]] || { echo "Usage: $0 evidence-index TERRITORY [OUTPUT]" >&2; exit 2; }
    output="${2:-evidence/evidence-index.json}"
    run_python "Build evidence index template" -m tools.art.build_evidence_index --territory "$1" --output "$output"
    ;;
  score)
    [[ $# -ge 2 ]] || { echo "Usage: $0 score SUBMISSIONS BLIND_MAP [OUTPUT]" >&2; exit 2; }
    output="${3:-evidence/human/scoring-report.json}"
    run_python "Score sealed blind study" -m tools.art.score_territories "$1" "$2" --output "$output"
    ;;
  prepare-study)
    output="${1:-evidence/human/art-direction-study-v1}"
    evidence_root="${2:-.}"
    run_python "Prepare sealed-capable blind study" -m tools.art.blind_study prepare --output "$output" --evidence-root "$evidence_root"
    ;;
  seal-study)
    study_root="${1:-evidence/human/art-direction-study-v1}"
    evidence_root="${2:-.}"
    run_python "Validate and seal blind-study submissions" -m tools.art.blind_study seal --study-root "$study_root" --evidence-root "$evidence_root"
    ;;
  lock)
    [[ $# -ge 5 ]] || { echo "Usage: $0 lock DECISION BLIND_MAP SCORING_REPORT EVIDENCE_INDEX LOCKED_BY [--apply]" >&2; exit 2; }
    extra=()
    [[ "${6:-}" == "--apply" ]] && extra+=(--apply)
    run_python "Validate or apply art lock" -m tools.art.lock_direction "$1" "$2" "$3" "$4" --locked-by "$5" "${extra[@]}"
    ;;
  *)
    echo "Unknown command: $COMMAND" >&2
    echo "Commands: bootstrap doctor precanon-init precanon-preflight precanon-handoff precanon-import precanon-review precanon-status validate generate test validate-luau build verify-blender measure-visual bind-studio-captures validate-studio validate-simulator validate-mobile prepare-study seal-study evidence-index score lock package" >&2
    exit 2
    ;;
esac
