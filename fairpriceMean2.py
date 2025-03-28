from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import json

class Trader:    
    def run(self, state: TradingState):
        # Print some debug info (optional)
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        # Hardcoded fair prices
        acceptable_prices = {
            "KELP": 2019,
            "RAINFOREST_RESIN": 10000
        }

        # For each product, we will place buy and/or sell orders
        result = {}

        # Maximum net position we allow for each product
        MAX_POSITION = 50

        for product, order_depth in state.order_depths.items():
            orders: List[Order] = []

            # Current net position in this product
            current_pos = state.position.get(product, 0)

            # Remaining capacity to buy (until we reach +50)
            can_buy = max(0, MAX_POSITION - current_pos)

            # Remaining capacity to sell (until we reach -50, i.e. current_pos = -50)
            # Another way to think about it: if your position is +10, you can sell up to 60 before hitting -50
            can_sell = max(0, MAX_POSITION + current_pos)

            # ------------------------------------------------
            # 1) Check for a good ask to buy
            # ------------------------------------------------
            if len(order_depth.sell_orders) > 0:
                # The best ask is the LOWEST sell price
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]


                # Only buy if best_ask < our acceptable/fair price
                if best_ask < acceptable_prices[product]:
                    # We want to buy up to can_buy, but cannot exceed what's actually offered
                    # best_ask_volume is how many are offered at best_ask
                    volume_to_buy = min(best_ask_amount, can_buy)

                    # If volume_to_buy > 0, place the buy order
                    if volume_to_buy > 0:
                        orders.append(Order(symbol=product, price=best_ask, quantity=volume_to_buy))

            # ------------------------------------------------
            # 2) Check for a good bid to sell
            # ------------------------------------------------
            if len(order_depth.buy_orders) > 0:
                # The best bid is the HIGHEST buy price
                best_bid = max(order_depth.buy_orders.keys())
                best_bid_volume = order_depth.buy_orders[best_bid]  # typically positive, meaning volume for buy

                # Only sell if best_bid > our acceptable/fair price
                if best_bid > acceptable_prices[product]:
                    # We want to sell up to can_sell, but cannot exceed what's actually bid
                    volume_to_sell = min(best_bid_volume, can_sell)

                    # If volume_to_sell > 0, place the sell order (negative quantity)
                    if volume_to_sell > 0:
                        orders.append(Order(symbol=product, price=best_bid, quantity=-volume_to_sell))

            # Collect the orders for this product
            result[product] = orders

        # Sample of how you can store persistent data between runs, if you need it
        # (Here we are just storing an empty JSON or "SAMPLE", but you can expand as needed)
        traderData = "SAMPLE"

        conversions = 1
        return result, conversions, traderData
