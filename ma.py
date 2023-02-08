from raw_data.raw import price_history,get_top_perps,price_min_max,atr
from rest import enter_trade,market_close_positions,get_existing_positions
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
pair = "ETH"
perp = pair+"-PERP"
leg_1 = pair+"-0930"
leg_2 = pair+"-1230"
### dailies
# l = get_top_perps()
d = {}
timeframe = str(60*5)
l=[perp,leg_1,leg_2]
for p in l:
    df = price_history(p,60*5).iloc[-24*12*7:]
    d.update({p:df[p]})
# df = price_history(p,60*60*24).iloc[90:]
df = pd.DataFrame(d).dropna()
basis_1 = (df[leg_1]-df[perp])/df[perp]
basis_2 = (df[leg_2]-df[leg_1])/df[leg_1]
test1 = basis_2-basis_1
# test2 = test1.rolling(200).mean().dropna()
fig,ax1 = plt.subplots()
ax1.plot(test1,color='blue',label="basis_2 divide by basis_1")
ax2 = ax1.twinx()
ax2.plot(df[perp],color = 'red',label=perp)
ax1.legend()
ax2.legend()
plt.show()
