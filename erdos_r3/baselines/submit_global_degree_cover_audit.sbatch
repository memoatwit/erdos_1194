#!/bin/bash
#SBATCH --job-name=r3_gdeg_audit
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/gdeg_audit-%j.out
#SBATCH --error=results/slurm_logs/gdeg_audit-%j.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
OUTDIR=results/baselines/global_degree_cover_audit
mkdir -p "$OUTDIR" results/slurm_logs

cc -O3 -std=c11 -Wall -Wextra -pedantic \
  baselines/r3_global_degree_cover_audit.c \
  -o "$OUTDIR/r3_global_degree_cover_audit"

python baselines/r3_generate_split_survivor_sample.py \
  --output "$OUTDIR/production_sample100.jsonl" \
  --summary "$OUTDIR/production_summary.json" \
  --survivors-output "$OUTDIR/production_survivors.txt"

"$OUTDIR/r3_global_degree_cover_audit" \
  "$OUTDIR/independent_survivors.txt" \
  "$OUTDIR/independent_summary.json"

cmp "$OUTDIR/production_survivors.txt" "$OUTDIR/independent_survivors.txt"
sha256sum \
  "$OUTDIR/production_survivors.txt" \
  "$OUTDIR/independent_survivors.txt" \
  baselines/r3_generate_split_survivor_sample.py \
  baselines/r3_global_degree_cover_audit.c \
  "$OUTDIR/r3_global_degree_cover_audit" \
  > "$OUTDIR/SHA256SUMS"

python - "$OUTDIR" results/global_degree_cover_independent_audit.json <<'PY'
import hashlib
import json
import pathlib
import platform
import subprocess
import sys

outdir = pathlib.Path(sys.argv[1])
final = pathlib.Path(sys.argv[2])

def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()

production = json.load(open(outdir / "production_summary.json"))
independent = json.load(open(outdir / "independent_summary.json"))
production_list = outdir / "production_survivors.txt"
independent_list = outdir / "independent_survivors.txt"
same_variables = production["split_variables"] == independent["split_variables"]
same_count = production["survivor_count"] == independent["survivor_count"] == 96847
same_masks = production["forbidden_mask_count"] == independent["forbidden_mask_count"] == 132
same_list_hash = sha(production_list) == sha(independent_list)
status = "VERIFIED" if all((same_variables, same_count, same_masks, same_list_hash)) else "MISMATCH"
payload = {
    "status": status,
    "N": 212,
    "split_count": 24,
    "split_variables": production["split_variables"],
    "forbidden_mask_count": independent["forbidden_mask_count"],
    "raw_assignment_count": independent["raw_assignment_count"],
    "survivor_count": independent["survivor_count"],
    "same_split_variables": same_variables,
    "same_forbidden_mask_count": same_masks,
    "same_survivor_count": same_count,
    "same_ordered_survivor_list_sha256": same_list_hash,
    "ordered_survivor_list_sha256": sha(independent_list),
    "production_generator_sha256": sha("baselines/r3_generate_split_survivor_sample.py"),
    "independent_source_sha256": sha("baselines/r3_global_degree_cover_audit.c"),
    "independent_binary_sha256": sha(outdir / "r3_global_degree_cover_audit"),
    "compiler": subprocess.run(["cc", "--version"], capture_output=True, text=True).stdout.splitlines()[0],
    "platform": platform.platform(),
}
final.parent.mkdir(parents=True, exist_ok=True)
final.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps(payload, indent=2, sort_keys=True))
if status != "VERIFIED":
    raise SystemExit("independent cover audit failed")
PY

echo ">>> independent global-degree cover audit VERIFIED"
