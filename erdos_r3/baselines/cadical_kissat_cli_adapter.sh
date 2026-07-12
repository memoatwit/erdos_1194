#!/bin/bash
# Adapt r3_sat_attack.py's kissat-style invocation
#   solver --time=SECONDS INPUT.cnf PROOF.drat
# to native CaDiCaL while enforcing the same wall cap externally.
set -euo pipefail

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
CADICAL=${CADICAL:-$R3_DIR/bin/cadical-3.0.0}
LIMIT=""
if [[ ${1:-} == --time=* ]]; then
  LIMIT=${1#--time=}
  shift
fi
[ -n "$LIMIT" ] || { echo "missing --time=SECONDS" >&2; exit 2; }
[ -x "$CADICAL" ] || { echo "missing $CADICAL" >&2; exit 1; }
exec timeout --signal=TERM --kill-after=60s "${LIMIT}s" "$CADICAL" "$@"
