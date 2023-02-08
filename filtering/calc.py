from turtle import color
import pandas as pd
from raw_data.raw import price_history,get_top_perps,make_corr,run_coint,bb1
import matplotlib.pyplot as plt
### get the top volume
top_vol = get_top_perps()
timeframe = 60*5 ### 60s * 60 mins --- hourly timeframe
df = pd.DataFrame()
### get the time series for all the top volume
for k in top_vol:
    df = pd.concat([df,price_history(k,timeframe)],axis=1)
### test here
p = 'SOL-PERP'
df = price_history(p,timeframe)
spread = .5/df[p].mean()
### instead of dropping any data, forward fill the data
df=df.fillna(method='ffill')
roll_frame = 200 ### 12 sets of 5 mins times 12 hours
vwap = ((df['volume']*(df['high']+df['low'])/2).cumsum()/df['volume'].cumsum()).dropna()
lows = df['low'].rolling(roll_frame).min().dropna()
highs = df['high'].rolling(roll_frame).max().dropna()
mp = (lows+highs)/2
decile_seventy =(highs+mp)/2# + spread
decile_thirty = (mp+lows)/2# - spread
smooth_price_ma = df[p].rolling(roll_frame).mean()
price = df[p]
# smooth_price = df[p].rolling(60).mean()-df[p].rolling(roll_frame).mean()
smooth_price = (df[p].rolling(30).sum()/df[p].rolling(roll_frame).sum()).diff().dropna()
smooth_low = smooth_price.rolling(60).min().dropna()
smooth_high = smooth_price.rolling(60).max().dropna()
l = pd.concat([lows,highs,smooth_price_ma,price,vwap,decile_seventy,decile_thirty,mp],axis=1).dropna()
ll = pd.concat([smooth_price,smooth_low,smooth_high],axis=1)
ax = plt.gca()
ax.plot(l)
ax2= ax.twinx()
ax2.plot(ll,color='black',linestyle='-.')
ax2.axhline(y=0)
plt.show()


### resample the time frame to respective
# df_10m = df.resample('10T').mean()
df_30m = df.resample('30T').mean()
df_60m = df.resample('60T').mean()
### generate correlation matrix
top_10_corr = make_corr(df_30m)
### cointegration to be run on pairs
cointd = run_coint(top_10_corr,df_30m.dropna())

p1 = cointd.index[0].split('_')[0]
p2 = cointd.index[0].split('_')[1]
mrv = df_3m[cointd.index[0].split('_')][p1] / df_3m[cointd.index[0].split('_')][p2]
mrv.name = 'mrv_pair'
mrv.index.name = 'date'
import matplotlib.pyplot as plt
plt.plot(mrv)
plt.show()
output = bb1(mrv.reset_index(),"mrv_pair",20).iloc[-1]
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