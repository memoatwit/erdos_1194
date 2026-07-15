#!/bin/bash
#SBATCH --job-name=r3_cdcl_pair
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --constraint=amd7763
#SBATCH --time=26:00:00
#SBATCH --array=0-19%20
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --output=results/slurm_logs/cdcl_pair-%A_%a.out
#SBATCH --error=results/slurm_logs/cdcl_pair-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

# Hardware-matched native CDCL comparison on all 20 T1b chunks. Each task
# runs both solvers sequentially on the same allocated AMD EPYC 7763 core.
# Solver order alternates by chunk index to reduce order effects.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"

OUT_DIR=results/baselines/cdcl_paired_amd7763
WORK_DIR=results/baselines/scratch_cdcl_paired_amd7763
mkdir -p "$OUT_DIR" "$WORK_DIR" results/slurm_logs

INPUT=results/N212_K44_broad24_recap300_residual_t1b20.jsonl
IDX=$SLURM_ARRAY_TASK_ID
printf 'job_id=%s\narray_task_id=%s\nhostname=%s\n' \
  "$SLURM_JOB_ID" "$IDX" "$(hostname)" > "$OUT_DIR/hardware_idx$(printf '%02d' "$IDX").txt"
lscpu >> "$OUT_DIR/hardware_idx$(printf '%02d' "$IDX").txt"
uname -a >> "$OUT_DIR/hardware_idx$(printf '%02d' "$IDX").txt"

if (( IDX % 2 == 0 )); then
  ARMS=(cadical kissat)
else
  ARMS=(kissat cadical)
fi

run_arm() {
  local arm=$1
  local solver version out tmp
  if [[ "$arm" == cadical ]]; then
    solver="$R3_DIR/baselines/cadical_kissat_cli_adapter.sh"
    version=$("$R3_DIR/bin/cadical-3.0.0" --version | head -1)
  else
    solver="$R3_DIR/bin/kissat"
    version=$("$solver" --version | head -1)
  fi

  out="$OUT_DIR/${arm}_idx$(printf '%02d' "$IDX").jsonl"
  if [[ -s "$out" ]]; then
    echo "[skip] $out already exists"
    return
  fi
  tmp="$out.tmp_${SLURM_JOB_ID}_${IDX}"

  python r3_sat_attack.py \
    --input "$INPUT" \
    --N 212 --K 44 \
    --window-bounds results/b003002.txt \
    --window-lengths none \
    --array-index "$IDX" \
    --time-limit 43200 \
    --solver-binary "$solver" \
    --solver-label "$arm-no-windows-paired-amd7763" \
    --solver-version "$version" \
    --discard-external-proof \
    --work-dir "$WORK_DIR" \
    --output "$tmp"

  mv "$tmp" "$out"
  if grep -q '"status": "SAT"' "$out"; then
    echo "!!! SAT row: verify the candidate immediately with r3_verify.py" >&2
    scancel "$SLURM_ARRAY_JOB_ID"
    exit 1
  fi
}

for arm in "${ARMS[@]}"; do
  run_arm "$arm"
done

python - "$OUT_DIR" "$IDX" <<'PY'
import json
import pathlib
import sys

out_dir = pathlib.Path(sys.argv[1])
idx = int(sys.argv[2])
rows = {}
for arm in ("cadical", "kissat"):
    path = out_dir / f"{arm}_idx{idx:02d}.jsonl"
    rows[arm] = json.loads(path.read_text().strip())
if rows["cadical"]["cnf_sha256"] != rows["kissat"]["cnf_sha256"]:
    raise SystemExit(f"CNF hash mismatch at index {idx}")
summary = {
    "array_index": idx,
    "chunk_id": rows["cadical"]["chunk_id"],
    "cnf_sha256": rows["cadical"]["cnf_sha256"],
    "cadical_status": rows["cadical"]["status"],
    "cadical_seconds": rows["cadical"]["solver_seconds"],
    "kissat_status": rows["kissat"]["status"],
    "kissat_seconds": rows["kissat"]["solver_seconds"],
    "order": ["cadical", "kissat"] if idx % 2 == 0 else ["kissat", "cadical"],
}
(out_dir / f"paired_idx{idx:02d}.json").write_text(
    json.dumps(summary, sort_keys=True, indent=2) + "\n"
)
PY
