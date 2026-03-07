import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta    
import numpy as np


def time2sell(df):
        
        
    ticker = yf.Ticker('MSFT')

    # Fetch last 7 days of historical data (to handle weekends/holidays)
    end_date = datetime.today()
    start_date = end_date - timedelta(days=7)
    history = ticker.history(start=start_date.strftime('%Y-%m-%d'),
                              end=end_date.strftime('%Y-%m-%d'))
        
    latest_close = history['Close'].iloc[-1]
    latest_date = history.index[-1].strftime('%Y-%m-%d')
    latest_date = pd.to_datetime(latest_date)

    df['Date Vested'] = pd.to_datetime(df['Date Vested'])
    df['Time Period (Days)'] = (latest_date - df['Date Vested']).dt.days
    df['Vesting Price'] = df['Vesting Price'].astype(float)
    df['Time Period (Days)'] = df['Time Period (Days)'].astype(int)
    #df['CAGR'] = round (((latest_close / df['Vesting Price']) ** (365 / df['Time Period (Days)']) - 1), 2)

    # 1. Define the condition
    is_short_term = df['Time Period (Days)'] < 365

    # 2. Calculate the numeric return
    df['Return %'] = np.where(
        is_short_term,
        (latest_close / df['Vesting Price']) - 1,                      # Absolute Gain
        (latest_close / df['Vesting Price']) ** (365 / df['Time Period (Days)']) - 1 # CAGR
    )

    # 3. Add the descriptive label
    df['Return Type'] = np.where(is_short_term, 'Absolute Gain', 'CAGR')

    # 4. Final formatting
    df['Return %'] = (df['Return %'] * 100).round(2)
    return df

def percentchange(newvalue, oldvalue):
    return round (((newvalue - oldvalue)*100/oldvalue),2)