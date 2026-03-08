import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta    
import numpy as np


def time2sell(df):
        
    ticker = yf.Ticker('INTC')

    # Fetch last 7 days of historical data (to handle weekends/holidays)
    end_date = datetime.today()
    start_date = end_date - timedelta(days=7)
    history = ticker.history(start=start_date.strftime('%Y-%m-%d'),
                              end=end_date.strftime('%Y-%m-%d'))

    # Get the latest closing price and the date of the last recorded closing price    
    latest_close = history['Close'].iloc[-1]
    latest_date = history.index[-1].normalize().tz_localize(None)

    # Get the most recent working day of the stock market and the closing price on that day
    df['Current Date'] = latest_date
    df['Current Price'] = round (latest_close, 2)

    # Convert string to datetime dtype
    df['Grant Date'] = pd.to_datetime(df['Grant Date'])
    df['Vest Date'] = pd.to_datetime(df['Vest Date'])

    # Get the number of days between now to Grant date and Vest date    
    df['Time Period Grant (Days)'] = (df['Current Date'] - df['Grant Date']).dt.days
    df['Time Period Vest (Days)'] = (df['Current Date'] - df['Vest Date']).dt.days

    df['Vest Price'] = df['Vest Price'].astype(float)
    df['Time Period Grant (Days)'] = df['Time Period Grant (Days)'].astype(int)
    df['Time Period Vest (Days)'] = df['Time Period Vest (Days)'].astype(int)

    is_short_term = df['Time Period Vest (Days)'] < 365

    # Calculate Absolute and CAGR gains for both time periods - Grant and Vest 
    df['Grant Returns'] = np.where(
        is_short_term,
        (latest_close / df['Grant Price']) - 1,                      # Absolute Gain
        (latest_close / df['Grant Price']) ** (365 / df['Time Period Grant (Days)']) - 1 # CAGR
    )
    df['Vest Returns'] = np.where(
        is_short_term,
        (latest_close / df['Vest Price']) - 1,                      # Absolute Gain
        (latest_close / df['Vest Price']) ** (365 / df['Time Period Vest (Days)']) - 1 # CAGR
    )

    # Calculate Percentage 
    df['Grant Returns'] = (df['Grant Returns'] * 100).round(2)
    df['Vest Returns'] = (df['Vest Returns'] * 100).round(2)

    # Remove time stamp and display only date
    df['Grant Date'] = df['Grant Date'].dt.date
    df['Vest Date'] = df['Vest Date'].dt.date
    df['Current Date'] = df['Current Date'].dt.date
    
    return df