#!/bin/bash
# Main confirmatory study: 2 populations x 3 topologies x 2 institution
# levels x 2 environments = 24 cells x 8 replicates = 192 runs.
# Runs against the main-study-dedicated, isolated society-service
# instance (port 8092, separate DB from the pilot instance on 8091) so
# nothing here can collide with any other concurrent work.
#
# Model: DeepSeek (deepseek-v4-flash) via e-INFRA CZ's hosted gateway
# (phase2_planning.md, "Execution venue" decision, 2026-08-08) --
# free/institutional compute, capped at the gateway's known
# max_parallel_requests=4 per key.
#
# Usage:
#   bash run_main_study.sh                  # full run, all 24 cells
#   bash run_main_study.sh commons           # only the commons environment
#   bash run_main_study.sh triage            # only the triage environment
set -uo pipefail

source ~/.e_infra_env
export LIGHTWEIGHT_API_KEY="$OPENAI_API_KEY"
SOCIETY_ADMIN_TOKEN="${SOCIETY_ADMIN_TOKEN:?set SOCIETY_ADMIN_TOKEN in the environment (e.g. in ~/.e_infra_env, gitignored) before running this script}"
SERVICE_URL=http://127.0.0.1:8092
MODEL="deepseek-v4-flash"
REPS=8
ROUNDS=15
MAX_PARALLEL=4
TIMEOUT=120

REG_DIR=/opt/continuants/lightweight/runs
OUTROOT=/opt/ArtificialMoralSocieties/tools/reports/raw_exports/main_study
cd /opt/ArtificialMoralSocieties/tools

ENV_FILTER="${1:-all}"

if [ ! -f "$(dirname "$0")/dashboard/progress.json" ]; then
  python3 update_progress.py init 192
fi

run_cell() {
  local ENVIRONMENT=$1      # commons | triage
  local POPULATION=$2       # uniform_fair | mixed
  local TOPOLOGY=$3         # fully_connected | clustered | scale_free
  local SANCTIONING=$4      # off | on
  local RUNNER=$5           # run_commons.py | run_triage.py
  local REG=$6
  local AGENTS=$7

  local INSTITUTIONS="reputation"
  if [ "$SANCTIONING" = "on" ]; then
    INSTITUTIONS="reputation,sanctioning"
  fi

  local OUTDIR="$OUTROOT/$ENVIRONMENT/${POPULATION}__${TOPOLOGY}__sanctioning_${SANCTIONING}"
  mkdir -p "$OUTDIR"

  for rep in $(seq 1 $REPS); do
    local LABEL="rep${rep}"
    local OUTFILE="$OUTDIR/${LABEL}.json"
    if [ -f "$OUTFILE" ]; then
      echo "=== SKIP (already done): $ENVIRONMENT/$POPULATION/$TOPOLOGY/sanctioning_$SANCTIONING/$LABEL ==="
      continue
    fi
    echo "=== $ENVIRONMENT/$POPULATION/$TOPOLOGY/sanctioning_$SANCTIONING/$LABEL ==="
    python3 update_progress.py current "$ENVIRONMENT" "$POPULATION" "$TOPOLOGY" "$SANCTIONING" "$LABEL"
    python3 "$RUNNER" \
      --service-url "$SERVICE_URL" \
      --admin-token "$SOCIETY_ADMIN_TOKEN" \
      --agents "$AGENTS" \
      --topology "$TOPOLOGY" \
      --inter-cluster-edges 40 \
      --rounds "$ROUNDS" \
      --institutions "$INSTITUTIONS" \
      --reset-first \
      --agent-mode lightweight \
      --lightweight-registry "$REG" \
      --lightweight-base-url "$OPENAI_BASE_URL" \
      --lightweight-model "$MODEL" \
      --max-parallel "$MAX_PARALLEL" \
      --timeout "$TIMEOUT"
    RC=$?
    local CELL_LABEL="$ENVIRONMENT/$POPULATION/$TOPOLOGY/sanctioning_$SANCTIONING/$LABEL"
    if [ $RC -ne 0 ]; then
      echo "!!! FAILED rc=$RC: $CELL_LABEL -- skipping export, continuing"
      python3 update_progress.py fail "$CELL_LABEL"
      continue
    fi
    curl -sf -H "Authorization: Bearer $SOCIETY_ADMIN_TOKEN" "$SERVICE_URL/admin/export" -o "$OUTFILE"
    echo "--- exported: $OUTFILE ---"
    python3 update_progress.py done "$CELL_LABEL"
    sleep 3
  done
}

run_environment() {
  local ENVIRONMENT=$1
  local RUNNER=$2
  local REG_UF="$REG_DIR/mainstudy_uniform_fair_${ENVIRONMENT}_registry.json"
  local REG_MX="$REG_DIR/mainstudy_mixed_${ENVIRONMENT}_registry.json"
  local PREFIX_UF MPREFIX_MX
  if [ "$ENVIRONMENT" = "commons" ]; then
    AGENTS_UF=$(python3 -c "print(','.join(f'MSUFC-{i:02d}' for i in range(1,21)))")
    AGENTS_MX=$(python3 -c "print(','.join(f'MSMXC-{i:02d}' for i in range(1,21)))")
  else
    AGENTS_UF=$(python3 -c "print(','.join(f'MSUFT-{i:02d}' for i in range(1,21)))")
    AGENTS_MX=$(python3 -c "print(','.join(f'MSMXT-{i:02d}' for i in range(1,21)))")
  fi

  for TOPOLOGY in fully_connected clustered scale_free; do
    for SANCTIONING in off on; do
      run_cell "$ENVIRONMENT" "uniform_fair" "$TOPOLOGY" "$SANCTIONING" "$RUNNER" "$REG_UF" "$AGENTS_UF"
      run_cell "$ENVIRONMENT" "mixed"        "$TOPOLOGY" "$SANCTIONING" "$RUNNER" "$REG_MX" "$AGENTS_MX"
    done
  done
}

if [ "$ENV_FILTER" = "all" ] || [ "$ENV_FILTER" = "commons" ]; then
  run_environment "commons" "run_commons.py"
fi
if [ "$ENV_FILTER" = "all" ] || [ "$ENV_FILTER" = "triage" ]; then
  run_environment "triage" "run_triage.py"
fi

echo "MAIN STUDY RUN DONE (environment filter: $ENV_FILTER)"
