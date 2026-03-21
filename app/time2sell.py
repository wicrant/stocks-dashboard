import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta    
import numpy as np


def time2sell(df):
        
    ticker = yf.Ticker('INTC')
    usdinr = yf.Ticker('USDINR=X')

    try:

        latest_close = ticker.fast_info['last_price']
        latest_usdinr = usdinr.fast_info['last_price']
    except KeyError as e:
        status = False
        return status, {e}, None, None, None, None, None 
        #print(f"Error: Missing data key {e}")
    except Exception as e:
        status = False
        return status, {e}, None, None, None, None, None 

    df['Current Date'] = datetime.today()
    df['Current Price'] = latest_close

    # Convert string to datetime dtype
    df['Grant Date'] = pd.to_datetime(df['Grant Date'],dayfirst=True)
    df['Vest Date'] = pd.to_datetime(df['Vest Date'],dayfirst=True)



    # Get the number of days between now to Grant date and Vest date    
    df['Time Period Grant (Days)'] = (df['Current Date'] - df['Grant Date']).dt.days
    df['Time Period Vest (Days)'] = (df['Current Date'] - df['Vest Date']).dt.days

    df['Grant Price'] = df['Grant Price'].astype(float)
    df['Vest Price'] = df['Vest Price'].astype(float)
    df['Quantity'] = df['Quantity'].astype(float)
    df['USDINR (Grant)'] = df['USDINR (Grant)'].astype(float)
    df['USDINR (Vesting)'] = df['USDINR (Vesting)'].astype(float)
    df['Current Price'] = df['Current Price'].astype(float)

    df['Time Period Grant (Days)'] = df['Time Period Grant (Days)'].astype(int)
    df['Time Period Vest (Days)'] = df['Time Period Vest (Days)'].astype(int)


    df['Grant Value'] = (df['Quantity'] * df['Grant Price'] * df['USDINR (Grant)'])
    df['Vest Value'] = (df['Quantity'] * df['Vest Price'] * df['USDINR (Vesting)'])
    df['Current Value'] = (df['Quantity'] * df['Current Price'] * latest_usdinr) 

    is_short_term = df['Time Period Vest (Days)'] < 365

    # Calculate Absolute and CAGR gains for both time periods - Grant and Vest 
    df['Grant Returns'] = np.where(
        is_short_term,
        (df['Current Value'] / df['Grant Value']) - 1,                      # Absolute Gain
        (df['Current Value'] / df['Grant Value']) ** (365 / df['Time Period Grant (Days)']) - 1 # CAGR
    )

    df['Vest Returns'] = np.where(
        is_short_term,
        (df['Current Value'] / df['Vest Value']) - 1,                      # Absolute Gain
        (df['Current Value'] / df['Vest Value']) ** (365 / df['Time Period Vest (Days)']) - 1 # CAGR
    )

    # Calculate Percentage 
    df['Grant Returns'] = (df['Grant Returns'] * 100)
    df['Vest Returns'] = (df['Vest Returns'] * 100)

    # Remove time stamp and display only date
    df['Grant Date'] = df['Grant Date'].dt.date
    df['Vest Date'] = df['Vest Date'].dt.date
    df['Current Date'] = df['Current Date'].dt.date

    TotalGrantValue = round(df['Grant Value'].sum(), 2)
    TotalVestValue = round (df['Vest Value'].sum(), 2)
    TotalCurrentValue = round(df['Current Value'].sum(), 2)
    latest_usdinr = round(latest_usdinr, 2)
    status = True
    return status, None, df, latest_usdinr, TotalGrantValue, TotalVestValue, TotalCurrentValue