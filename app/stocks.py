import yfinance as yf
import pandas as pd

from .config import DB_PATH

def fetch_stock_metrics(tickers):
    data = []
    for ticker in tickers:
        df = yf.Ticker(ticker).history(period="1y", interval="1d")
        df["H-L"] = df["High"] - df["Low"]
        df["H-PC"] = abs(df["High"] - df["Close"].shift(1))
        df["L-PC"] = abs(df["Low"] - df["Close"].shift(1))
        df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
        df["ATR"] = df["TR"].rolling(window=14).mean()
        info = yf.Ticker(ticker).info
        var_52WH =  percentchange((df["Close"].iloc[-1]), info.get("fiftyTwoWeekHigh", 0))
        var_52WL = percentchange ((df["Close"].iloc[-1]), info.get("fiftyTwoWeekLow", 0))
        data.append({
            "Ticker": ticker,
            "current_price": round(df["Close"].iloc[-1], 2),
            "P/E Ratio": round(info.get("trailingPE", 0), 2),
            "P/B Ratio": round(info.get("priceToBook", 0), 2),
            "Beta": round(info.get("beta", 0), 2),
            "52_week_high": round(info.get("fiftyTwoWeekHigh", 0), 2),
            "52_week_low": round(info.get("fiftyTwoWeekLow", 0), 2),
            "atr": round(df["ATR"].iloc[-1], 2),
            "support": round(df["Close"].rolling(20).min().iloc[-1], 2),
            "resistance": round(df["Close"].rolling(20).max().iloc[-1], 2),
            "Volume": int(df["Volume"].iloc[-1]),
            "Market Cap": info.get("marketCap", 0),
            "CP to 52WH": var_52WH,
            "CP to 52WL": var_52WL
        })
    return data

def percentchange(newvalue, oldvalue):
    return round (((newvalue - oldvalue)*100/oldvalue),2)