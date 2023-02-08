import json,time,hmac
from requests import Request, Session
from sqlalchemy import true
from orders import place_order,get_open_order
import ftx.rest.client
import pandas as pd
import time
def log_in():
    with open("./key/id.txt","r") as f:
        lines = f.readlines()
        f.close()
    a_k = lines[0].split(',')[0]
    a_s = lines[0].split(',')[1]
    return a_k,a_s
# enter_trade("BCH-PERP",'buy',.5,135)
def enter_trade(market,side,proportion,entry,stops):
    # proportion = .5
    # market = 'ANC-PERP'
    # enter_trade(k,'buy',long_size,long_entry,lows)
    # stops = lows
    # entry = long_entry
    # entry = 135
    s_a = 'dayTrade'
    a_k,a_s = log_in()
    client = ftx.rest.client.FtxClient(api_key=a_k,api_secret=a_s,subaccount_name=s_a)
    notional = round(int(client.get_account_info()['totalAccountValue']),-2)
    size = notional*2*proportion
    risk = .1/100*size
    rr_ratio = risk*2
    digits = client.get_single_market(market)['priceIncrement']
    bid = round(client.get_single_market(market)['ask'],len(str(digits))-1)
    ask = round(client.get_single_market(market)['bid'],len(str(digits))-1)
    spread = round(ask-bid,len(str(digits)))/2
    # try:
    if side =='buy':
        entry = (entry+ask+ask)/3+3*spread
        tp = (size + rr_ratio)/(size/entry)
        sl = round((size - risk)/round(size/entry,2),len(str(digits)))
        client.place_order(market,side,entry+spread,round(size/entry,2))
        # client.place_order(market,'sell',tp,round(size/entry,2))
        client.place_conditional_order(market,'sell',trigger_price=tp,size=round(size/entry,2),type='take_profit',reduce_only=True,cancel=False)#
        # time.sleep(3)
        # client.place_conditional_order(market,'sell',type='trailing_stop',size=round(size/entry,2),trail_value=-abs(sl-entry))
        client.place_conditional_order(market,'sell',trigger_price=sl,size=round(size/entry,2),type='stop',reduce_only=True,cancel=False)#
        print(f"{market} size is: {size}, {side} order opened at {entry}; tp: {tp}; sl: {stops}.")
    else:
        entry = (entry+bid+bid)/3+3*spread
        tp = (size - rr_ratio)/(size/entry)
        sl = round((size + risk)/round(size/entry,2),len(str(digits)))
        client.place_order(market,side,entry-spread,round(size/entry,2))
        # client.place_order(market,'buy',tp,round(size/entry,2))
        client.place_conditional_order(market,'buy',trigger_price=tp,size=round(size/entry,2),type='take_profit',reduce_only=True,cancel=False)#
        # client.place_conditional_order(market,'buy',type='trailing_stop',size=round(size/entry,2),trail_value=abs(sl-entry))
        client.place_conditional_order(market,'buy',trigger_price=sl,size=round(size/entry,2),type='stop',reduce_only=True,cancel=False)#
        print(f"{market} size is: {size}, {side} order opened at {entry}; tp: {tp}; sl: {stops}.")
    # except Exception as e:
    #     client.cancel_orders(market)
    #     print(f"Cancelled orders for {market} due to {e}")

def closing_machine():
    risk = .1
    rr_ratio = risk*2
    s_a = 'dayTrade'
    a_k,a_s = log_in()
    client = ftx.rest.client.FtxClient(api_key=a_k,api_secret=a_s,subaccount_name=s_a)
    closing_machine = pd.DataFrame(client.get_positions())
    closing_machine = closing_machine[(closing_machine['netSize']!=0) & (closing_machine['recentPnl']>(rr_ratio-risk/10))][['future','netSize','recentPnl']]
    if len(closing_machine)>0:
        closing_machine = closing_machine.set_index('future')
        for k in range(len(closing_machine)):
            p = closing_machine.iloc[k].name
            bid = client.get_single_market(p)['bid']
            ask = client.get_single_market(p)['ask']
            size = abs(closing_machine['netSize'].iloc[k])
            print(f"Closing {p} of size: {size}")
            if closing_machine['netSize'].iloc[k]>0:          
                client.place_order(p,'sell',price=(bid+(ask-bid)/2),size=size,reduce_only=True)
            else:
                client.place_order(p,'buy',price=(ask-(ask-bid)/2),size=size,reduce_only=True)


def get_existing_positions():
    s_a = 'dayTrade'
    a_k,a_s = log_in()
    client = ftx.rest.client.FtxClient(api_key=a_k,api_secret=a_s,subaccount_name=s_a)
    outstandings = pd.DataFrame(client.get_positions())
    if isinstance(outstandings,pd.DataFrame):
        outstandings = outstandings[outstandings['netSize']!=0]
        outstandings = outstandings[['future','netSize']].reset_index(drop=True)
    print(outstandings)

def market_close_positions():
    s_a = 'dayTrade'
    a_k,a_s = log_in()
    client = ftx.rest.client.FtxClient(api_key=a_k,api_secret=a_s,subaccount_name=s_a)
    if client.get_open_orders():
        client.cancel_orders()
    outstandings = pd.DataFrame(client.get_positions())
    if isinstance(outstandings,pd.DataFrame):
        outstandings = outstandings[outstandings['netSize']!=0]
        outstandings = outstandings[['future','netSize']].reset_index(drop=True)
    if outstandings.empty:
        print('No existing positions')
    else:
        for k in range(len(outstandings)):
            market = outstandings['future'].iloc[k]
            # market = outstandings['future'].iloc[1]
            v = float(outstandings['netSize'].iloc[k])
            digits = client.get_single_market(market)['priceIncrement']
            ask = round(client.get_single_market(market)['bid'],len(str(digits)))
            bid = round(client.get_single_market(market)['ask'],len(str(digits)))
            spread = round(ask-bid,len(str(digits)))/2
            try:
                if v >0:
                    client.place_order(market,'sell',ask-spread,abs(v))
                else:
                    client.place_order(market,'buy',bid+spread,abs(v))
            except Exception as e:
                print(e)

    