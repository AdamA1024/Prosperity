from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
'''This uses a hardcoded fair price that was determined by looking at the whole data set and finding the mean. 
   Won't work in practice because the point is that other people will trade, changing the price from the actual dataset.
   And also, one must dynamically calculate the fair price on the fly. Only returned 2.1k seashell profit.'''
class Trader:
    
    def run(self, state: TradingState):
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            print(f"position for {product} is {state.position.get(product, 0)}")
            acceptable_prices={"KELP": 2019, "RAINFOREST_RESIN": 10000}
            current_pos = state.position.get(product, 0)
            can_sell = max(0, 50 + current_pos)   
            can_buy = max(0, 50 - current_pos)
            # print("Acceptable price : " + str(acceptable_price))
            #print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
    
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if int(best_ask) < acceptable_prices[product]:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -min(best_ask_amount, can_buy)))
    
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if int(best_bid) > acceptable_prices[product]:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -min(best_bid_amount, can_sell)))
            
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1
        return result, conversions, traderData
