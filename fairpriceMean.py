import json
from typing import Any, List
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
import math

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(
            self.to_json(
                [
                    self.compress_state(state, ""),
                    self.compress_orders(orders),
                    conversions,
                    "",
                    "",
                ]
            )
        )

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(
            self.to_json(
                [
                    self.compress_state(state, self.truncate(state.traderData, max_item_length)),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing.symbol, listing.product, listing.denomination])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append(
                    [
                        trade.symbol,
                        trade.price,
                        trade.quantity,
                        trade.buyer,
                        trade.seller,
                        trade.timestamp,
                    ]
                )

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sugarPrice,
                observation.sunlightIndex,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value

        return value[: max_length - 3] + "..."


logger = Logger()
class Trader:
    
    def run(self, state: TradingState):
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        logger.print("traderData: " + state.traderData)
        logger.print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            logger.print(f"position for {product} is {state.position.get(product, 0)}")
            acceptable_prices={"KELP": 2019, "RAINFOREST_RESIN": 10000}
            current_pos = state.position.get(product, 0)
            can_sell = max(0, 50 + current_pos)   
            can_buy = max(0, 50 - current_pos)
            currentSpreadRR=[0 , math.inf]
            # logger.print("Acceptable price : " + str(acceptable_price))
            #logger.print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
            if product=="RAINFOREST_RESIN":
                if len(order_depth.sell_orders) != 0:
                    best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                    if int(best_ask) < acceptable_prices[product]: #LOGIC TO EXECUTE ARBITRAGE BY BUYING BELOW FAIR VALUE
                        logger.print("BUY", str(-best_ask_amount) + "x", best_ask)
                        orders.append(Order(product, best_ask, -max(best_ask_amount, -can_buy))) #e.g. if bestaskamount is -20 and we can buy 10, then -max(-20, -10) = 10
                        
                    #LOGIC TO UNDERCUT THE BEST ASK (MM)    
                    elif int(best_ask)<currentSpreadRR[1] and int(best_ask)>acceptable_prices[product]+1: 
                            logger.print("SELL", str(-5) + "x", best_ask-1)
                            orders.append(Order(product, best_ask-1, -min(15, can_sell)))
                            currentSpreadRR[1]=int(best_ask-1)
                            
                if len(order_depth.buy_orders) != 0:
                    best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                    if int(best_bid) > acceptable_prices[product]: #LOGIC TO EXECUTE ARBITRAGE BY SELLING ABOVE FAIR VALUE
                        logger.print("SELL", str(best_bid_amount) + "x", best_bid)
                        orders.append(Order(product, best_bid, -min(best_bid_amount, can_sell)))
                        
                    #LOGIC TO UNDERCUT THE BEST BID (MM)
                    elif int(best_bid)>currentSpreadRR[0] and int(best_bid)<acceptable_prices[product]-1: 
                            logger.print("BUY", str(5) + "x", best_bid+1)
                            orders.append(Order(product, best_bid+1, min(15, can_buy)))
                            currentSpreadRR[0]=int(best_bid+1)  
                        
            elif product=="KELP":
                if len(order_depth.sell_orders) != 0:
                    best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                    if int(best_ask) < acceptable_prices[product]-2:
                        logger.print("BUY", str(-best_ask_amount) + "x", best_ask)
                        orders.append(Order(product, best_ask, -min(best_ask_amount, can_buy)))
                        logger.print(best_ask_amount)
        
                if len(order_depth.buy_orders) != 0:
                    best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                    if int(best_bid) > acceptable_prices[product]+2:
                        logger.print("SELL", str(best_bid_amount) + "x", best_bid)
                        orders.append(Order(product, best_bid, -min(best_bid_amount, can_sell)))
                        logger.print(best_bid_amount)
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData