from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"
    BLOCK = "block"
    STOP_LIMIT = "stop_limit"
    LOC = "loc"   # Limit-on-Close: participates only in the closing auction
    MOC = "moc"   # Market-on-Close: participates only in the closing auction


class TimeInForce(str, Enum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class Action(str, Enum):
    NEW = "NEW"
    CANCEL = "CANCEL"
    AMEND = "AMEND"
    CLOSE = "CLOSE"  # Triggers the closing auction for a specific asset


@dataclass
class Order:
    id: str
    side: Side
    price: float
    quantity: float
    asset: str = "default"
    order_type: OrderType = OrderType.LIMIT
    min_quantity: Optional[float] = None  # used for block orders
    time_in_force: TimeInForce = TimeInForce.GTC
    action: Action = Action.NEW
    visible_quantity: Optional[float] = None
    stop_price: Optional[float] = None
    trader_id: Optional[str] = None

    def __post_init__(self) -> None:
        if isinstance(self.side, str):
            self.side = Side(self.side)
        if isinstance(self.order_type, str):
            self.order_type = OrderType(self.order_type)
        if isinstance(self.time_in_force, str):
            self.time_in_force = TimeInForce(self.time_in_force)
        if isinstance(self.action, str):
            self.action = Action(self.action)


@dataclass
class BookSide:
    side: Side
    orders: List[Order] = field(default_factory=list)

    def add(self, order: Order) -> None:
        self.orders.append(order)

    def best(self) -> Optional[Order]:
        return self.orders[0] if self.orders else None


@dataclass
class OrderBook:
    bids: BookSide = field(default_factory=lambda: BookSide(side=Side.BUY))
    asks: BookSide = field(default_factory=lambda: BookSide(side=Side.SELL))

    def snapshot(self) -> dict:
        return {
            "bids": [order_to_dict(o) for o in self.bids.orders],
            "asks": [order_to_dict(o) for o in self.asks.orders],
        }


@dataclass
class MultiBook:
    books: Dict[str, OrderBook] = field(default_factory=dict)

    def get_or_create(self, asset: str) -> OrderBook:
        if asset not in self.books:
            self.books[asset] = OrderBook()
        return self.books[asset]

    def snapshot(self) -> dict:
        return {asset: book.snapshot() for asset, book in self.books.items()}


def order_to_dict(order: Order) -> dict:
    d = {
        "id": order.id,
        "side": order.side.value if isinstance(order.side, Side) else order.side,
        "price": order.price,
        "quantity": order.quantity,
        "asset": order.asset,
        "order_type": order.order_type.value
        if isinstance(order.order_type, OrderType)
        else order.order_type,
        "min_quantity": order.min_quantity,
    }
    # Conditional serialization: only include new fields when non-default
    if order.time_in_force != TimeInForce.GTC:
        d["time_in_force"] = order.time_in_force.value
    if order.action != Action.NEW:
        d["action"] = order.action.value
    if order.visible_quantity is not None:
        d["visible_quantity"] = order.visible_quantity
    if order.stop_price is not None:
        d["stop_price"] = order.stop_price
    if order.trader_id is not None:
        d["trader_id"] = order.trader_id
    return d
