import jsonpickle
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
    def computeMA(self, order_depth: OrderDepth, filterOrder: int, traderObject: dict) -> float:
        if len(order_depth.buy_orders)!=0 and len(order_depth.sell_orders)!=0:
            midprice = (min(order_depth.sell_orders.keys()) + max(order_depth.buy_orders.keys()))/2
            if f"{filterOrder}MA" not in traderObject:
                traderObject[f"{filterOrder}MA"] = midprice
                traderObject[f"{filterOrder}Mps"]= []
                traderObject[f"{filterOrder}Mps"].append(midprice)

            elif len(traderObject[f"{filterOrder}Mps"])<=(filterOrder-1):
                traderObject[f"{filterOrder}Mps"].append(midprice)
                traderObject[f"{filterOrder}MA"] = sum(traderObject[f"{filterOrder}Mps"])/len(traderObject[f"{filterOrder}Mps"])
            else:
                traderObject[f"{filterOrder}Mps"].append(midprice)
                traderObject[f"{filterOrder}MA"] = sum(traderObject[f"{filterOrder}Mps"])/len(traderObject[f"{filterOrder}Mps"])
                traderObject[f"{filterOrder}Mps"].pop(0)
            
            return traderObject[f"{filterOrder}MA"]
        else:
            return 0


    
    def run(self, state: TradingState):
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        logger.print("traderData: " + state.traderData)
        logger.print("Observations: " + str(state.observations))
        traderObject = {}
        if state.traderData != None and state.traderData != "":
            traderObject = jsonpickle.decode(state.traderData)
    
        result = {}

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            logger.print(f"position for {product} is {state.position.get(product, 0)}")
            acceptable_prices={"KELP": 2019, "RAINFOREST_RESIN": 10000}
            current_pos = state.position.get(product, 0)
            can_sell = max(0, 50 + current_pos)   
            can_buy = max(0, 50 - current_pos)

            if product=="RAINFOREST_RESIN":
                # Filter out any bid asks within 1 tick of fair value. 
                asks_above_fair = [
                    price
                    for price in order_depth.sell_orders.keys()
                    if price > 10000 + 1
                ]
                bids_below_fair = [
                    price
                    for price in order_depth.buy_orders.keys()
                    if price < 10000 - 1
                ]
                
                best_ask_above_fair = min(asks_above_fair) if len(asks_above_fair) > 0 else None
                best_bid_below_fair = max(bids_below_fair) if len(bids_below_fair) > 0 else None

                if len(order_depth.sell_orders) != 0:
                    best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                    if int(best_ask) < acceptable_prices[product]: #LOGIC TO EXECUTE ARBITRAGE BY BUYING BELOW FAIR VALUE
                        logger.print("BUY", str(-best_ask_amount) + "x", best_ask)
                        orders.append(Order(product, best_ask, -max(best_ask_amount, -can_buy))) #e.g. if bestaskamount is -20 and we can buy 10, then -max(-20, -10) = 10

                    #LOGIC TO MM THE BEST ASK    
                    if int(best_ask_above_fair)-acceptable_prices[product]==2:
                        #This is a case like 10002 where we may as well just join onto that order rather than try and undercut it.
                        logger.print("SELL", str(-15) + "x", best_ask_above_fair)
                        orders.append(Order(product, best_ask_above_fair, -min(15, can_sell)))
                    else: 
                        #This is a case like 10003 or higher where we can undercut the best ask by 1.
                        logger.print("SELL", str(-15) + "x", best_ask_above_fair-1)
                        orders.append(Order(product, best_ask_above_fair-1, -min(15, can_sell)))
                            
                if len(order_depth.buy_orders) != 0:
                    best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                    if int(best_bid) > acceptable_prices[product]: #LOGIC TO EXECUTE ARBITRAGE BY SELLING ABOVE FAIR VALUE
                        logger.print("SELL", str(best_bid_amount) + "x", best_bid)
                        orders.append(Order(product, best_bid, -min(best_bid_amount, can_sell)))
                        
                    #LOGIC TO MM THE BEST BID 
                    if acceptable_prices[product]-int(best_bid_below_fair)==2:
                        #This is a case like 9998 where we may as well just join onto that order rather than try and undercut it.
                        logger.print("BUY", str(15) + "x", best_bid_below_fair)
                        orders.append(Order(product, best_bid_below_fair, min(15, can_buy)))
                    else:
                        #This is a case like 9997 or lower where we can improve the best bid by 1.
                        logger.print("BUY", str(15) + "x", best_bid_below_fair+1)
                        orders.append(Order(product, best_bid_below_fair+1, min(15, can_buy)))
                        
            elif product=="KELP":        
                logger.print(self.computeMA(order_depth, 5, traderObject))
                self.computeMA(order_depth, 10, traderObject)
                best_ask= None
                best_bid= None
                if len(order_depth.sell_orders) != 0:
                    best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                    if int(best_ask) < acceptable_prices[product]-2: #LOGIC TO EXECUTE ARBITRAGE BY BUYING BELOW FAIR VALUE
                        logger.print("BUY", str(-best_ask_amount) + "x", best_ask)
                        orders.append(Order(product, best_ask, -min(best_ask_amount, can_buy)))
                        logger.print(best_ask_amount)

                if len(order_depth.buy_orders) != 0:
                    best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                    if int(best_bid) > acceptable_prices[product]+2: #LOGIC TO EXECUTE ARBITRAGE BY SELLING ABOVE FAIR VALUE
                        logger.print("SELL", str(best_bid_amount) + "x", best_bid)
                        orders.append(Order(product, best_bid, -min(best_bid_amount, can_sell)))
                        logger.print(best_bid_amount)
                
                spread=best_ask-best_bid
                if spread !=None:
                    if spread==1 or spread==2:
                        #This is a case where we may as well join volume rather than try and undercut it.
                        logger.print("BUY", str(5) + "x", best_bid)
                        orders.append(Order(product, best_bid, min(20, can_buy)))
                        logger.print("SELL", str(-5) + "x", best_ask)
                        orders.append(Order(product, best_ask, -min(20, can_sell)))
                    elif spread>2:
                        #This is a case where we can improve the best bid by 1.
                        logger.print("BUY", str(5) + "x", best_bid+1)
                        orders.append(Order(product, best_bid+1, min(20, can_buy)))
                        logger.print("SELL", str(-5) + "x", best_ask-1)
                        orders.append(Order(product, best_ask-1, -min(20, can_sell)))



            result[product] = orders
    
    
        traderData = jsonpickle.encode(traderObject)

        conversions = 1
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData