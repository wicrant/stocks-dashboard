import sqlite3
import psutil
import time
from datetime import datetime, timedelta, timezone

from .config import DB_PATH

# ——————————————
#  DB Initialization
# ——————————————
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS temp_metrics (
            timestamp TEXT PRIMARY KEY,
            temp REAL,
            freq INT,
            CPU0_utilization REAL,
            CPU1_utilization REAL,
            CPU2_utilization REAL,
            CPU3_utilization REAL,
            mem_utilization REAL,
            disk_io_read REAL,
            disk_io_write REAL,
            net_stats_sent INT,
            net_stats_recv INT
        )
    """)
    conn.commit()
    conn.close()

# ——————————————
#  Temperature Recording
# ——————————————
def record_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            temp_c = round(float(f.read()) / 1000, 1)
    except FileNotFoundError:
        temp_c = None

    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO temp_metrics (timestamp, temp) VALUES (?, ?)",
        (now, temp_c)
    )
    conn.commit()
    conn.close()

# ——————————————
#  System Metrics Collection
# ——————————————
def read_cpu_freq(core_id):
    path = f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_cur_freq"
    try:
        with open(path) as f:
            return int(f.read().strip()) // 1000  # kHz to MHz
    except FileNotFoundError:
        return None

def get_per_core_cpu_usage(interval=1):
    return psutil.cpu_percent(interval=interval, percpu=True)

def get_cpu_metrics():
    usage = get_per_core_cpu_usage()
    return {f"cpu{i}_percent": usage[i] for i in range(len(usage))}

def get_system_metrics():
    timestamp = datetime.now(timezone.utc).isoformat()
    cpufreq = read_cpu_freq(0)
    cpu_percent = get_cpu_metrics()

    mem = psutil.virtual_memory()
    mem_util = mem.percent

    disk_io_start = psutil.disk_io_counters()
    net_start = psutil.net_io_counters()
    time.sleep(1)
    disk_io_end = psutil.disk_io_counters()
    net_end = psutil.net_io_counters()

    disk_read = disk_io_end.read_bytes - disk_io_start.read_bytes
    disk_write = disk_io_end.write_bytes - disk_io_start.write_bytes
    net_sent = net_end.bytes_sent - net_start.bytes_sent
    net_recv = net_end.bytes_recv - net_start.bytes_recv

    return (
        timestamp,
        cpufreq,
        cpu_percent.get("cpu0_percent", 0),
        cpu_percent.get("cpu1_percent", 0),
        cpu_percent.get("cpu2_percent", 0),
        cpu_percent.get("cpu3_percent", 0),
        mem_util,
        disk_read,
        disk_write,
        net_recv,
        net_sent
    )

def record_metrics_to_db():
    metrics = get_system_metrics()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO temp_metrics (
            timestamp, freq, CPU0_utilization, CPU1_utilization,
            CPU2_utilization, CPU3_utilization, mem_utilization,
            disk_io_read, disk_io_write, net_stats_sent, net_stats_recv
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, metrics)
    conn.commit()
    conn.close()

# ——————————————
#  Prune Old Records
# ——————————————
def prune_old():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM temp_metrics WHERE timestamp < ?", (cutoff,))
    conn.commit()
    conn.close()