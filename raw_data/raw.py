import json,time,hmac
from requests import Request, Session
from sqlalchemy import true
import ftx.rest.client
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.stattools import jarque_bera

def log_in():
    with open("./key/id.txt","r") as f:
        lines = f.readlines()
        f.close()
    a_k = lines[0].split(',')[0]
    a_s = lines[0].split(',')[1]
    return a_k,a_s


def price_history(market,timeframe):
    s_a = 'dayTrade'
    a_k,a_s = log_in()
    client = ftx.rest.client.FtxClient(api_key=a_k,api_secret=a_s,subaccount_name=s_a)
    df = pd.DataFrame(client.get_historical_prices(market,timeframe))
    df = df.rename(columns={'close':market})
    df['startTime'] = pd.to_datetime(df['startTime'])
    df = df.set_index('startTime') #,'volume'
    return df

def price_history2(market,timeframe):
    s_a = 'dayTrade'
    a_k,a_s = log_in()
    client = ftx.rest.client.FtxClient(api_key=a_k,api_secret=a_s,subaccount_name=s_a)
    df = pd.DataFrame(client.get_historical_prices(market,timeframe))
    df = df.rename(columns={'close':market})
    df['startTime'] = pd.to_datetime(df['startTime'])
    df = df.set_index('startTime') #,'volume'
    return df

def atr(market):
    # market='DOT-PERP'
    timeframe=60*15
    smoother=4*4
    s_a = 'dayTrade'
    a_k,a_s = log_in()
    client = ftx.rest.client.FtxClient(api_key=a_k,api_secret=a_s,subaccount_name=s_a)
    df = pd.DataFrame(client.get_historical_prices(market,timeframe))
    df['high_low'] = df['high']-df['low']
    df['high_close'] = df['high']-df['close']
    df['close_low'] = df['close']-df['low']
    df['tr'] = df[['high_low','high_close','close_low']].max(axis=1)
    df['atr'] = df['tr'].rolling(smoother).mean()
    df['dm_plus']=df['high'].diff()
    df['dm_minus']=df['low'].diff()
    df['dm_plus_smoother'] = 100*df['dm_plus'].ewm(span=smoother).mean()/df['atr']
    df['dm_minus_smoother'] = 100*df['dm_minus'].ewm(span=smoother).mean()/df['atr']
    df['di_smoother'] = abs(df['dm_plus_smoother']-df['dm_minus_smoother']) / abs(df['dm_plus_smoother']+df['dm_minus_smoother'])*100
    return df['di_smoother'].iloc[-1]
def price_min_max(market,timeframe):
    # market='DOT-PERP'
    # timeframe=60*5
    s_a = 'dayTrade'
    a_k,a_s = log_in()
    client = ftx.rest.client.FtxClient(api_key=a_k,api_secret=a_s,subaccount_name=s_a)
    df = pd.DataFrame(client.get_historical_prices(market,timeframe))
    df = df.rename(columns={'close':market})
    df['startTime'] = pd.to_datetime(df['startTime'])
    df = df.set_index('startTime') #,'volume'
    lows = df[["high"]].rolling(20).min().dropna().iloc[-1].values[-1]
    highs = df[["low"]].rolling(20).max().dropna().iloc[-1].values[-1]
    range = (highs - lows)
    long_entry = lows+(range*20/100)
    short_entry = highs-(range*20/100)
    return long_entry,short_entry,lows,highs
# price_min_max("UNI-PERP",60)
def get_top_perps():
    s_a = 'dayTrade'
    a_k,a_s = log_in()
    client = ftx.rest.client.FtxClient(api_key=a_k,api_secret=a_s,subaccount_name=s_a)
    df = pd.DataFrame(client.get_all_futures())
    df = df[(df['type']=="perpetual") & (~df['underlying'].str.contains("|".join(["USD","UST"])))]
    # df['actual_spot'] = df['volumeUsd24h'] - df['openInterestUsd']
    df = df[['name','volumeUsd24h', 'volume','openInterest', 'openInterestUsd']].sort_values(by='volumeUsd24h',ascending=False)
    # df = df[['name','volumeUsd24h', 'volume','openInterest', 'openInterestUsd']].sort_values(by='volumeUsd24h',ascending=False)
    return df.head(30)['name'].to_list()

def get_futures():
    s_a = 'dayTrade'
    a_k,a_s = log_in()
    client = ftx.rest.client.FtxClient(api_key=a_k,api_secret=a_s,subaccount_name=s_a)
    df = pd.DataFrame(client.get_all_futures())
    df = df[(df['type']=="future") & (~df['underlying'].str.contains("|".join(["USD","UST"]))) & (df['expired']!=True)]
    df = df[['name','volumeUsd24h', 'volume','openInterest', 'openInterestUsd']].sort_values(by='volumeUsd24h',ascending=False)
    return df.head(30)['name'].to_list()


def make_corr(p_d):
    corr_m = p_d.pct_change().dropna().corr().abs().unstack().sort_values(kind="quicksort")
    corr_m = corr_m.reset_index()
    corr_m.columns=['quote','base','corr']
    corr_m = corr_m[corr_m['quote']!=corr_m['base']]
    corr_m = corr_m.sort_values(by='quote',ascending=True).drop_duplicates(subset=['corr'])
    corr_m = corr_m.sort_values(by='corr',ascending=False).reset_index(drop=True)
    top_10_corr = corr_m[:10]
    return top_10_corr


def adf(quote:str,base:str,p_d:pd.DataFrame):
    a = sm.add_constant(p_d[quote])
    res = sm.OLS(p_d[base],a).fit()
    b=res.params[0]
    adf_stats = adfuller(p_d[quote]-b*p_d[base],maxlag=1,autolag='t-stat')
    # adf_stats = adfuller(res.resid,maxlag=1,autolag='t-stat')
    jb_test = pd.DataFrame(jarque_bera(res.resid)).T
    jb_test.columns=['JB','JB_p','skew','kurtosis']
    print(adf_stats)
    return adf_stats,jb_test

def run_coint(top_10_corr:pd.DataFrame,p_d:pd.DataFrame):
    q_b = top_10_corr[['quote','base']].reset_index(drop=True)
    coint_d = {}
    jb_test_d = pd.DataFrame()
    for k in range(len(q_b)):
        quote =q_b["quote"].iloc[k]
        base = q_b["base"].iloc[k]
        pair = quote+"_"+base
        print(f"{quote}/{base}\n")
        adf_stats,jb_test = adf(quote,base,p_d)
        coint_d.update({pair:adf_stats[:4]})
        jb_test_d = pd.concat([jb_test_d,jb_test],axis=0)
    coint_d = pd.DataFrame(coint_d).T
    coint_d.columns=['adf_stat','p_value','max_lags','obs']
    coint_d = coint_d.sort_values(by='p_value',ascending=True)
    coint_d = pd.concat([coint_d.reset_index(drop=False),jb_test_d.reset_index(drop=True)],axis=1).set_index('index')
    return coint_d
    
def bb1(df0:pd.DataFrame,ticker:str,lookback:int):
    df0['mb'] = df0[ticker].rolling(lookback).mean()
    sd = df0[ticker].rolling(lookback).std()
    df0['ub_short_stop'] = df0['mb'] + sd*2.36
    df0['ub_short_entry'] = df0['mb'] + sd*1.96
    df0['lb_long_stop'] = df0['mb'] - sd*2.36
    df0['lb_long_entry'] = df0['mb'] - sd*1.96
    df0['mb_short_stop'] = df0['mb'] + sd*.5
    df0['mb_long_stop'] = df0['mb'] - sd*.5
    df0.set_index('date')
    df0['impulsebb'] = (df0[ticker]-df0['lb_long_entry']) / (df0['ub_short_entry']-df0['lb_long_entry'])
    output = df0[[ticker,"impulsebb",'ub_short_stop','ub_short_entry','lb_long_stop','lb_long_entry','mb_short_stop','mb_long_stop','mb']].dropna()
    return output

def screener(coint_df,timeframe):
    trade_screen = {}
    quote_base =pd.DataFrame()
    bt_numbers = pd.DataFrame()
    for k in coint_df.index:
        # print(k.split('_'))
        # ticker1,ticker2 = coint_df.index[0].split('_')
        ticker1,ticker2 = k.split('_')
        bb_lookback = 21
        p1 = prices(ticker1,timeframe)
        p2 = prices(ticker2,timeframe)
        combined_pair = pd.concat([p1,p2],axis=1)
        chrt_lgd = combined_pair.columns[0]+"_"+combined_pair.columns[1]
        px_last= pd.DataFrame([chrt_lgd,p1.iloc[-1].to_list()[0],p2.iloc[-1].to_list()[0]]).T
        px_last.columns=['pair','quote','base']
        px_last = px_last.set_index('pair')
        combined_pair['mrv_pair'] = combined_pair[combined_pair.columns[0]]/combined_pair[combined_pair.columns[1]]
        output = bb(combined_pair.reset_index(),"mrv_pair",bb_lookback)
        trade_screen.update({chrt_lgd:output.iloc[-1]})
        quote_base = pd.concat([quote_base,px_last],axis=0)
        # top_btm_only(output,"mrv_pair",bb_lookback)
        ### this function plots bollinger bands
        ### backtester function to be added
        no_of_trades,win_rate,net_ret = backtester(fees,output,chrt_lgd)
        bt_nn = pd.DataFrame([chrt_lgd,no_of_trades,win_rate,net_ret]).T
        bt_nn.columns=['pair','no_of_trades','win-rate','netReturn']
        bt_nn = bt_nn.set_index('pair')
        bt_numbers = pd.concat([bt_numbers,bt_nn],axis=0)
    trade_screener_latest = pd.concat([coint_df,pd.DataFrame(trade_screen).T,quote_base],axis=1)

    print("here's the latest screener's top 6: \n",trade_screener_latest[['adf_stat','p_value','impulsebb','ub','lb']].head(6))
    print("here're the backtest results' top 6:\n",bt_numbers.head(6))
    return trade_screener_latest,bt_numbers