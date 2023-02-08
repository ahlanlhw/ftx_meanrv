from raw_data.raw import price_history,get_top_perps,price_min_max,atr
from rest import enter_trade,market_close_positions,get_existing_positions
import time
import pandas as pd
import numpy as np
from datetime import datetime
while True:
    interval=3
    if datetime.now().minute % interval == 0:
        l = get_top_perps()
        d = {}
        d2 ={}
        timeframe = str(60*5)
        smoother = 20
        # candles_in_a_day = 24*60+1 ### 480 5minute candles in a day
        for p in l:
            # p = 'BTC-PERP'
            df = np.log(1+(price_history(p,timeframe)[p].iloc[:-1].pct_change()))
            df = ((df-df.rolling(smoother).mean())/df.rolling(smoother).std()).dropna()
            df = df.resample('15T').sum()
            df2 = df.resample('90T').sum()
        # df = (df.rolling(5).mean()-df.rolling(20).mean()).dropna()
            d.update({p:df})
            d2.update({p:df2})
        ### ST trend
        cross_section = pd.DataFrame(d).fillna(method='ffill').T
        cross_section = ((cross_section - cross_section.mean())/cross_section.std()).T
        # new_tokens =['LDO-PERP']
        # cross_section = cross_section.drop(columns=new_tokens)
        # rotator = (cross_section.rolling(3).mean()-cross_section.rolling(9).mean()).dropna().iloc[-3:].T
        rotator = cross_section.dropna().iloc[-3:].T
        rotator = rotator[rotator.columns[-1]].sort_values(ascending=False)
        # print(rotator)

        ### MT trend
        cross_section2 = pd.DataFrame(d2).fillna(method='ffill').T
        cross_section2 = ((cross_section2 - cross_section2.mean())/cross_section2.std()).T
        # new_tokens =['LDO-PERP']
        # cross_section2 = cross_section2.drop(columns=new_tokens)
        # rotator2 = (cross_section2.rolling(3).mean()-cross_section2.rolling(9).mean()).dropna().iloc[-3:].T
        rotator2 = cross_section2.dropna().iloc[-3:].T
        rotator2 = rotator2[rotator2.columns[-1]].sort_values(ascending=False)
        # print(rotator2)
        mom = (((rotator+rotator2).sort_values(ascending=False)))
        # outlier_long = list(mom.head(1).index.values)
        # outlier_short = list(mom.tail(1).index.values)
        print(mom)
        long_size = round(len(mom[mom<0])/len(mom),1)
        longs = mom[mom>0]
        # longs = longs[longs<1.96].sort_values(ascending=False)
        shorts = mom[mom<0]
        # shorts = shorts[shorts>-1.96].sort_values(ascending=False)
        top = list(shorts[:3].index.values)#+outlier_short
        bottom = list(longs[-3:].index.values)#+outlier_long
        short_size = 1-long_size 
        print(f"{'|'.join(top)},{'|'.join(bottom)}")
        print(f"Long/Short Ratio is {round(long_size/short_size,1)}")
        print("Closing previous trades first --- rebalancing positions")
        market_close_positions()
        print("Sleeping for 15seconds wait for trades to be closed.")
        time.sleep(15)

        for k in top:
            long_entry,short_entry,lows,highs = price_min_max(k,60)
            # if atr(k) <20:
            try:
                enter_trade(k,'sell',short_size,short_entry,highs)
            except Exception as e:
                print(f"Error returned for {k}: {e}; {short_entry}; {highs}")
                # else:
                #     try:
                #         enter_trade(k,'buy',long_size,long_entry,lows)
                #     except Exception as e:
                #         print(f"Error returned for {k}: {e}; {long_entry}; {lows}")
        for k in bottom:
            long_entry,short_entry,lows,highs = price_min_max(k,60)
            # if atr(k) <20:
            try:
                enter_trade(k,'buy',long_size,long_entry,lows)
            except Exception as e:
                print(f"Error returned for {k}: {e}; {long_entry}; {lows}")
                # else:
                #     try:
                #         enter_trade(k,'sell',short_size,short_entry,highs)
                #     except Exception as e:
                #         print(f"Error returned for {k}: {e}; {short_entry}; {highs}")
        get_existing_positions()
    slp_time = interval-datetime.now().minute%interval - 1
    if slp_time >0: 
        print(f"Time now is: {datetime.now().time()}")
        print(f"Sleeping for {slp_time} minutes before next rebalance")
        time.sleep(slp_time*60)
    else:
        print("Script should run trades now.")
    # interval+=2
    # if interval >15:
    #     interval-=3

