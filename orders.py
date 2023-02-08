
### get open orders
def get_open_order(market):
    method = "GET"
    get_req = f"/orders?market={market}"
    return method,get_req

def get_open_trigger_orders(market):
    method = "GET"
    get_req = f"/conditional_orders?market={market}"
    return method,get_req

### cancel all orders ### need to change this to POST

def place_order():
    method = "POST"
    get_req = f"/orders"

    return method,get_req