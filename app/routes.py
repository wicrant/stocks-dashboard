from flask import render_template, jsonify, abort   
from datetime import datetime, timedelta, timezone
import pandas as pd
import sqlite3
from .config import DB_PATH
from .stocks import fetch_stock_metrics
from .ytstreamer import download_video

def register_routes(app):
    @app.route("/")
    def index():
        try:
            with open('tickers.txt', 'r') as file:
                lines = file.readlines()
            tickers = [line.strip() for line in lines]
        except FileNotFoundError:
            error_message = "Error: tickers.txt file was not found."
            return render_template("error.html", message=error_message), 404
        except PermissionError:
            error_message = "Error: Permission denied while trying to read the tickers.txt file."
            return render_template("error.html", message=error_message), 403
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            return render_template("error.html", message=error_message), 500

        data = fetch_stock_metrics(tickers)
        return render_template("index.html", data=data)

    @app.route("/pitemp.html")
    def pitemp_page():
        return render_template("pitemp.html")

    @app.route("/pimetrics.html")
    def pimetrics_page():
        return render_template("pimetrics.html")

    @app.route("/ytstreamer.html")
    def ytstreamer_page():
        return render_template("ytstreamer.html")

    @app.route("/api/pitemp")
    def pitemp_api():
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            "SELECT timestamp, temp FROM temp_metrics WHERE timestamp >= ? ORDER BY timestamp",
            conn, params=[cutoff.isoformat()], parse_dates=["timestamp"]
        ).dropna()
        conn.close()
        return jsonify({
            "timestamps": df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").tolist(),
            "temps": df["temp"].tolist()
        })

    @app.route("/api/pifreq")
    def pifreq_api():
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        conn = sqlite3.connect(DB_PATH)
        df = (
          pd.read_sql_query(
          "SELECT timestamp, freq, CPU0_utilization,CPU1_utilization, CPU2_utilization, CPU3_utilization, mem_utilization, disk_io_read, disk_io_write, net_stats_sent, net_stats_recv FROM temp_metrics "
          "WHERE timestamp >= ? ORDER BY timestamp",
      conn, params=[cutoff.isoformat()], parse_dates=["timestamp"]
        ).dropna()
        )
        conn.close()
        
        return jsonify({
            "timestamps": df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").tolist(),
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

    @app.route("/ytstreamer", methods=["GET"])
    def yt_download():
        return download_video()