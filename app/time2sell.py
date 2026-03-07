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
        
    latest_close = history['Close'].iloc[-1]
    #latest_date = history.index[-1].strftime('%Y-%m-%d')
    #latest_date = pd.to_datetime(latest_date)
    latest_date = history.index[-1].normalize().tz_localize(None)

    df['Current Date'] = latest_date
    df['Current Price'] = round (latest_close, 2)

    df['Grant Date'] = pd.to_datetime(df['Grant Date'])
    df['Vest Date'] = pd.to_datetime(df['Vest Date'])
    df['Time Period Grant (Days)'] = (latest_date - df['Grant Date']).dt.days
    df['Time Period Vest (Days)'] = (latest_date - df['Vest Date']).dt.days
    df['Vest Price'] = df['Vest Price'].astype(float)
    df['Time Period Grant (Days)'] = df['Time Period Grant (Days)'].astype(int)
    df['Time Period Vest (Days)'] = df['Time Period Vest (Days)'].astype(int)
    #df['CAGR'] = round (((latest_close / df['Vesting Price']) ** (365 / df['Time Period (Days)']) - 1), 2)

    # 1. Define the condition
    is_short_term = df['Time Period Vest (Days)'] < 365

    # 2. Calculate the numeric return
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

    # 3. Add the descriptive label
    #df['Return Type'] = np.where(is_short_term, 'Absolute Gain', 'CAGR')

    # 4. Final formatting
    df['Grant Returns'] = (df['Grant Returns'] * 100).round(2)
    df['Vest Returns'] = (df['Vest Returns'] * 100).round(2)
    return df

def percentchange(newvalue, oldvalue):
    return round (((newvalue - oldvalue)*100/oldvalue),2)