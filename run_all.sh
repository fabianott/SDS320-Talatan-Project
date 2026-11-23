#!/usr/bin/env bash
#
# Run all notebooks once, in order, and write the outputs back into them.
#
#   conda activate sds320
#   caffeinate -i ./run_all.sh
#
# caffeinate keeps the Mac awake for as long as the script runs; without it a
# sleeping laptop interrupts the training. The whole run takes about two hours,
# most of it notebook 03. Progress goes to run_all.log, so a second terminal can
# follow along with:  tail -f run_all.log
#
# The script stops at the first notebook that raises an error, so a failure is
# never hidden by the notebooks that come after it.

set -euo pipefail
cd "$(dirname "$0")"

LOG="run_all.log"
: > "$LOG"

# Order matters: 02 needs the scenes from 01, 03 needs the tiles from 02,
# and 06 reads the metrics CSV that 04 writes.
NOTEBOOKS=(
  notebooks/01_data_search.ipynb
  notebooks/02_labels_and_tiles.ipynb
  notebooks/03_train_model.ipynb
  notebooks/04_predict_and_evaluate.ipynb
  notebooks/05_time_series.ipynb
  notebooks/06_golmud_transfer.ipynb
)

log() { echo "$*" | tee -a "$LOG"; }

log "Start: $(date '+%Y-%m-%d %H:%M')"

for nb in "${NOTEBOOKS[@]}"; do
  start=$SECONDS
  log ""
  log "=== $(basename "$nb") ==="

  if jupyter nbconvert --to notebook --execute --inplace \
       --ExecutePreprocessor.timeout=-1 "$nb" >>"$LOG" 2>&1; then
    log "   ok, $(( (SECONDS - start) / 60 )) min"
  else
    log "   FAILED after $(( (SECONDS - start) / 60 )) min"
    log ""
    log "Last lines of the log:"
    tail -n 25 "$LOG"
    exit 1
  fi
done

log ""
log "All six notebooks finished: $(date '+%Y-%m-%d %H:%M')"
