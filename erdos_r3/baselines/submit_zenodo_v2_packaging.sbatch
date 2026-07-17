#!/bin/bash
#SBATCH --job-name=r3_zenodo_v2_pack
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=24:00:00
#SBATCH --array=0-2
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --output=results/slurm_logs/zenodo-v2-pack-%A_%a.out
#SBATCH --error=results/slurm_logs/zenodo-v2-pack-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

set -euo pipefail

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
SCRATCH4=${SCRATCH4:-/scratch4/workspace/ergezerm_wit_edu-soft_speech}
SCRATCH3=${SCRATCH3:-/scratch3/workspace/ergezerm_wit_edu-superfund}
OUTDIR=${OUTDIR:-$SCRATCH4/r3_212_zenodo_v2_upload}
ZSTD_LEVEL=${ZSTD_LEVEL:-10}

mkdir -p "$OUTDIR" "$R3_DIR/results/slurm_logs"

pack() {
  local output=$1
  shift
  local tmp="${output}.tmp"

  if [ -s "$output" ] && [ -s "${output}.sha256" ]; then
    echo "[skip] $output already packaged"
    return
  fi

  rm -f "$tmp"
  echo "[pack] $output"
  tar -I "zstd -T${SLURM_CPUS_PER_TASK} -${ZSTD_LEVEL}" -cf "$tmp" "$@"
  mv "$tmp" "$output"
  sha256sum "$output" > "${output}.sha256"
  ls -lh "$output" "${output}.sha256"
}

case "$SLURM_ARRAY_TASK_ID" in
  0)
    # Keep only the exact CNFs from the archived input directory; the fresh,
    # independently verified proof objects and provenance live in
    # t1c_certified. The earlier unverified proof copies are intentionally
    # omitted.
    pack "$OUTDIR/r3-212-v2-t1c-certified.tar.zst" \
      -C "$R3_DIR" \
      results/baselines/t1c_proofs/chunk_00040959.cnf \
      results/baselines/t1c_proofs/chunk_00048895.cnf \
      results/baselines/t1c_proofs/SHA256SUMS \
      results/baselines/t1c_certified
    ;;
  1)
    pack "$OUTDIR/r3-212-v2-exact-certificates.tar.zst" \
      -C "$SCRATCH4" r3_exact_certified \
      -C "$SCRATCH3" r3_exact_certified \
      -C "$R3_DIR" results/baselines/known_exact_certified
    ;;
  2)
    pack "$OUTDIR/r3-212-v2-global-degree-certificates.tar.zst" \
      -C "$SCRATCH4" r3_global_degree_cert_sample6 \
      -C "$SCRATCH3" r3_global_degree_cert_sample6 \
      -C "$R3_DIR" results/baselines/global_degree_cert_sample6
    ;;
  *)
    echo "unexpected array index: $SLURM_ARRAY_TASK_ID" >&2
    exit 2
    ;;
esac
