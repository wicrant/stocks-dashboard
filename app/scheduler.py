from .metrics import record_temp, record_metrics_to_db, prune_old
from .config import TEMP_INTERVAL_SECONDS, METRICS_INTERVAL_SECONDS, PRUNE_INTERVAL_HOURS


def register_jobs(sched):
    sched.add_job(record_temp, "interval", seconds=TEMP_INTERVAL_SECONDS, id="record_temp")
    sched.add_job(record_metrics_to_db, "interval", seconds=METRICS_INTERVAL_SECONDS, id="record_freq")
    sched.add_job(prune_old, "interval", hours=PRUNE_INTERVAL_HOURS, id="prune_old")