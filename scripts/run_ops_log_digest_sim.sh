#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME/.openclaw/workspace"
TS="$(date -u +%Y-%m-%dT%H-%MZ)"
BUNDLE_DIR="$ROOT/simulations/no1r-2/ops_log_digest/input_bundles"
REPORT_DIR="$ROOT/simulations/no1r-2/ops_log_digest/reports"
mkdir -p "$BUNDLE_DIR" "$REPORT_DIR"

BUNDLE_FILE="$BUNDLE_DIR/${TS}_bundle.json"
REPORT_FILE="$REPORT_DIR/${TS}_report.json"
TMP_REPORT="$REPORT_FILE.tmp"

python3 "$ROOT/scripts/build_ops_log_bundle.py" > "$BUNDLE_FILE"
BUNDLE_JSON="$(cat "$BUNDLE_FILE")"

PROMPT=$(cat <<EOF
You are no1r-2, an ops analyst running entirely on local infrastructure. You only analyze data and NEVER take direct actions.

INPUT (OpsLogBundle JSON):
$BUNDLE_JSON

TASK: (1) reconstruct the ops situation, (2) summarize overall health, (3) detect anomalies/tensions, (4) offer hypotheses with explicit uncertainty, (5) classify overall state as one of normal|watch|investigate|policy_tension|low_value_task|high_value_task, (6) list watch_items for main no1r. Follow spec v0.1.

OUTPUT: A single JSON object named SimulationReport with exactly these fields:
{
  "simulation_type": "ops_log_digest_v0.1",
  "timestamp": "ISO8601 now",
  "situation": "1-3 sentences",
  "observed_signals": ["..."],
  "analysis": "dense explanation",
  "anomalies_or_tensions": ["..."],
  "hypotheses": ["..."],
  "uncertainties": ["..."],
  "recommended_classification": "normal|watch|investigate|policy_tension|low_value_task|high_value_task",
  "watch_items": ["..."],
  "notes_for_main_no1r": "targeted notes",
  "confidence": "low|medium|high",
  "safety_note": "Simulation only. No external actions taken."
}

No extra prose or markdown—JSON only.
EOF
)

openclaw run --model qwen-portal/coder-model --no-stream "$PROMPT" > "$TMP_REPORT"

python3 - "$TMP_REPORT" "$REPORT_FILE" <<'PY'
import json, sys, pathlib
src = pathlib.Path(sys.argv[1])
dst = pathlib.Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
start = text.find('{')
end = text.rfind('}')
if start == -1 or end == -1:
    raise SystemExit('no JSON object found')
json_blob = text[start:end+1]
data = json.loads(json_blob)
if data.get('simulation_type') != 'ops_log_digest_v0.1':
    raise SystemExit('invalid simulation_type')
dst.write_text(json.dumps(data, indent=2), encoding='utf-8')
src.unlink()
PY

cd "$ROOT"
git add "$BUNDLE_FILE" "$REPORT_FILE"
if git diff --cached --quiet; then
  git reset HEAD "$BUNDLE_FILE" "$REPORT_FILE" >/dev/null 2>&1 || true
else
  git commit -m "ops_log_digest: add report $TS" >/dev/null 2>&1 || true
  if ! git push origin master --quiet; then
    echo "[warn] git push failed (check credentials)" >&2
  fi
fi

echo "Saved bundle to $BUNDLE_FILE"
echo "Saved report to $REPORT_FILE"
