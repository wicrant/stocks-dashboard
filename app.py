from flask import Flask, render_template, jsonify, request
import subprocess
import yfinance as yf
import pandas as pd
import psutil
import sqlite3
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
import os
import time

app = Flask(__name__)
#DB = "metrics.db"
DB = "/app/data/metrics.db"
# ——————————————
#  STOCK METRICS (existing)
# ——————————————
def fetch_stock_metrics(tickers):
    data = []
    for ticker in tickers:
        df = yf.Ticker(ticker).history(period="1y", interval="1d")
        df["H-L"] = df["High"] - df["Low"]
        df["H-PC"] = abs(df["High"] - df["Close"].shift(1))
        df["L-PC"] = abs(df["Low"] - df["Close"].shift(1))
        df["TR"] = df[["H-L","H-PC","L-PC"]].max(axis=1)
        df["ATR"] = df["TR"].rolling(window=14).mean()
        info = df.info 
        data.append({
            "Ticker": ticker,
            "current_price": round(df["Close"].iloc[-1],2),
            "P/E Ratio": round(yf.Ticker(ticker).info.get("trailingPE", 0),2),
            "52_week_high": round(df["Close"].rolling(window=252).max().iloc[-1],2),
            "52_week_low": round(df["Close"].rolling(window=252).min().iloc[-1],2),
            "atr": round(df["ATR"].iloc[-1],2),
            "support": round(df["Close"].rolling(20).min().iloc[-1],2),
            "resistance": round(df["Close"].rolling(20).max().iloc[-1],2),
            "Volume": int(df["Volume"].iloc[-1]),
            "Market Cap": yf.Ticker(ticker).info.get("marketCap", 0)
            })
    print (data)
    return data

# ——————————————
#  PI METRICS STORAGE
# ——————————————

def init_db():
    conn = sqlite3.connect(DB)
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
        net_stats_recv INT)
    """)
    conn.commit()
    conn.close()

def record_temp():
    # Read CPU temp (°C)
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            temp_c = round (float(f.read()) / 1000, 1)
    except FileNotFoundError:
        temp_c = None

    now = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB)
    conn.execute(
      "INSERT OR REPLACE INTO temp_metrics (timestamp, temp) VALUES (?, ?)",
      (now, temp_c)
    )
    conn.commit()
    conn.close()
'''
def record_freq():
   # Read CPU frequency (MHz)
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq") as f:
            freq0_mhz = int(f.read() / 1000)  # Convert from kHz to MHz
    except FileNotFoundError:
        freq0_mhz = None
    try:
        with open("/sys/devices/system/cpu/cpu1/cpufreq/scaling_cur_freq") as f:
            freq1_mhz = int(f.read() / 1000)  # Convert from kHz to MHz
    except FileNotFoundError:
        freq1_mhz = None
    try:
        with open("/sys/devices/system/cpu/cpu2/cpufreq/scaling_cur_freq") as f:
            freq2_mhz = int(f.read() / 1000)  # Convert from kHz to MHz
    except FileNotFoundError:
        freq2_mhz = None
    try:
        with open("/sys/devices/system/cpu/cpu3/cpufreq/scaling_cur_freq") as f:
            freq3_mhz = int(f.read() / 1000) # Convert from kHz to MHz
    except FileNotFoundError:
        freq3_mhz = None
    now = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT OR REPLACE INTO temp_metrics (timestamp, freq0, freq1, freq2, freq3) VALUES (?, ?,?,?,?)",
        (now, freq0_mhz, freq1_mhz, freq2_mhz, freq3_mhz))
    
    conn.commit()
    conn.close()

'''


def get_per_core_cpu_usage(interval=1):
    return psutil.cpu_percent(interval=interval, percpu=True)

def get_cpu_metrics():
    usage = get_per_core_cpu_usage()
    return {f"cpu{i}_percent": usage[i] for i in range(len(usage))}



def get_system_metrics():
    timestamp = datetime.now(timezone.utc).isoformat()

    cpufreq = read_cpu_freq(0)  # Assumingall cores run at the same frequency
    # CPU Utilization (%)
    cpu_percent = get_cpu_metrics()

    # Memory Utilization
    mem = psutil.virtual_memory()
    memory_stats = {
        "total_mb": mem.total // (1024 * 1024),
        "used_mb": mem.used // (1024 * 1024),
        "available_mb": mem.available // (1024 * 1024),
        "percent": mem.percent
    }

    # Disk Utilization
    disk = psutil.disk_usage('/')
    disk_stats = {
        "total_gb": disk.total // (1024 ** 3),
        "used_gb": disk.used // (1024 ** 3),
        "free_gb": disk.free // (1024 ** 3),
        "percent": disk.percent
    }

    # Disk and Network I/O Counters
    disk_io_start = psutil.disk_io_counters()
    net_start = psutil.net_io_counters()

    time.sleep(1)  # Wait a second to measure I/O over time

    disk_io_end = psutil.disk_io_counters()
    net_end = psutil.net_io_counters()

    read_bytes = disk_io_end.read_bytes - disk_io_start.read_bytes
    write_bytes = disk_io_end.write_bytes - disk_io_start.write_bytes
    bytes_sent = net_end.bytes_sent - net_start.bytes_sent
    bytes_recv = net_end.bytes_recv - net_start.bytes_recv
    disk_io_stats = {
        "read_bytes_per_sec": read_bytes // 1,
        "write_bytes_per_sec": write_bytes // 1
    }


    # Network I/O (bytes sent/received since boot)
    # net = psutil.net_io_counters()
    network_stats = {
        "bytes_sent_per_sec": bytes_sent // 1,
        "bytes_recv_per_sec": bytes_recv // 1
    }

    return \
        timestamp, \
        cpufreq, \
        cpu_percent["cpu0_percent"], \
        cpu_percent["cpu1_percent"], \
        cpu_percent["cpu2_percent"], \
        cpu_percent["cpu3_percent"], \
        memory_stats["percent"], \
        disk_io_stats["read_bytes_per_sec"], \
        disk_io_stats["write_bytes_per_sec"], \
        network_stats["bytes_recv_per_sec"], \
        network_stats["bytes_sent_per_sec"]


def read_cpu_freq(core_id):
    path = f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_cur_freq"
    try:
        with open(path) as f:
            return int(f.read().strip()) // 1000  # Convert kHz to MHz
    except FileNotFoundError:
        return None

def record_metrics_to_db():
    #freq_mhz = read_cpu_freq(0)  # Just one core. All cores on Raspberry Pi  run at the same frequency
    #now = datetime.now(timezone.utc).isoformat()
    timestamp, cpufreq, cpu0_percent, cpu1_precent, cpu2_percent, cpu3_percent, memory_stats, disk_io_stats_read, disk_io_stats_write, network_stats_recv, network_stats_sent = get_system_metrics()
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO temp_metrics (timestamp, freq, CPU0_utilization , CPU1_utilization, CPU2_utilization, CPU3_utilization, mem_utilization, \
        disk_io_read,disk_io_write, net_stats_sent, net_stats_recv) VALUES (?, ?, ?, ?, ?, ?,?, ?, ?, ?, ?)",
        (timestamp, cpufreq, cpu0_percent, cpu1_precent, cpu2_percent, cpu3_percent, memory_stats, disk_io_stats_read,disk_io_stats_write, network_stats_recv, network_stats_sent)
    )
    conn.commit()
    conn.close()

def prune_old():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    conn = sqlite3.connect(DB)
    conn.execute(
      "DELETE FROM temp_metrics WHERE timestamp < ?", 
      (cutoff,)
    )
    conn.commit()
    conn.close()

# initialize DB and scheduler
init_db()
sched = BackgroundScheduler()
sched.add_job(record_temp, "interval", seconds=60, id="record_temp")
sched.add_job(record_metrics_to_db, "interval", seconds=3, id="record_freq")
sched.add_job(prune_old,   "interval", hours=1,   id="prune_old")
sched.start()

# serve the new page
@app.route("/pitemp.html")
def pitemp_page():
    return render_template("pitemp.html")

@app.route("/pimetrics.html")
def pimetrics_page():
    return render_template("pimetrics.html")

@app.route("/ytstreamer.html")
def ytstreamer_page():
    return render_template("ytstreamer.html") 

# JSON API for chart data
@app.route("/api/pitemp")
def pitemp_api():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    conn = sqlite3.connect(DB)
    df = (
          pd.read_sql_query(
          "SELECT timestamp, temp FROM temp_metrics "
          "WHERE timestamp >= ? ORDER BY timestamp",
      conn, params=[cutoff.isoformat()], parse_dates=["timestamp"]
    ).dropna()
    )
    conn.close()

    return jsonify({
      "timestamps": df["timestamp"]
                        .dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                        .tolist(),
      "temps": df["temp"].tolist()
    })

@app.route("/api/pifreq")
def pifreq_api():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    conn = sqlite3.connect(DB)
    df = (
          pd.read_sql_query(
          "SELECT timestamp, freq, CPU0_utilization,CPU1_utilization, CPU2_utilization, CPU3_utilization, mem_utilization, disk_io_read, disk_io_write, net_stats_sent, net_stats_recv FROM temp_metrics "
          "WHERE timestamp >= ? ORDER BY timestamp",
      conn, params=[cutoff.isoformat()], parse_dates=["timestamp"]
    ).dropna()
    )
    conn.close()

    return jsonify({
        "timestamps": df["timestamp"]
                        .dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                        .tolist(),
        "freqs": df["freq"].tolist(),
        "cpu0_utils": df["CPU0_utilization"].tolist(),
        "cpu1_utils": df["CPU1_utilization"].tolist(),
        "cpu2_utils": df["CPU2_utilization"].tolist(),
        "cpu3_utils": df["CPU3_utilization"].tolist(),
        "mem_utils": df["mem_utilization"].tolist(),
        "disk_utils_read": df["disk_io_read"].tolist(),
        "disk_utils_write": df["disk_io_write"].tolist(),
        "net_utils_sent": df["net_stats_sent"].tolist(),
        "net_utils_recv": df["net_stats_recv"].tolist()
    })



@app.route("/")
def index():
    tickers = [ "MSFT", "INTC"]
    data = fetch_stock_metrics(tickers)
    return render_template("index.html", data=data)


@app.route('/ytstreamer', methods=['GET'])
def download_video():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    # Define the host folder where videos will be saved
    save_folder = '/app/videos'  # This should be a mounted volume path

    # Ensure the folder exists
    os.makedirs(save_folder, exist_ok=True)

    try:
        # Download and merge best video + audio into mp4
        result = subprocess.run([
            'yt-dlp',
            '-S', 'res:1440,fps',
            '-t', 'mp4',
            '-o', os.path.join(save_folder, '%(title)s.%(ext)s'),
            url
        ], capture_output=True, text=True)

        print("YT-DLP Output:", result.stdout)
        print("YT-DLP Error:", result.stderr)

        if result.returncode != 0:
            return jsonify({'error': 'Download failed', 'details': result.stderr}), 500

        return jsonify({'status': 'Download successful', 'output': result.stdout})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    try:
      app.run(host="0.0.0.0", port=5000)
    finally:
      sched.shutdown()  