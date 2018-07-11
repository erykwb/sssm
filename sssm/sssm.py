# -*- coding: utf-8 -*-

"""
Super Simple Stock Market.

Requested by David Morrow (2018-06-22) re. Mphasis re. J.P. Morgan.

Contains the following core classes:

    * Exchange: records trades for Global Beverage Corporation (GBC)
    * TradeType: a buy or sell transaction
    * Stock: base stock class with shared functionality
    * CommonStock: subclass of ``Stock`` supporting last dividend calculation
    * PreferredStock: subclass of ``Stock`` supporting fixed dividend calculation

To perform static type checking:
    >>> pip install mypy
    >>> mypy sssm.py

To run unit and integration tests:
    >>> python -m unittest
"""

from enum import Enum, unique
from datetime import datetime, timedelta
from operator import attrgetter, mul
from functools import reduce
from itertools import groupby
from typing import Union, Sequence
import collections

class Stock(object):
    """
    Base class for stock that can be traded on the Global Beverage Corporation Exchange (GBCE).  

    ``dividend_yield()`` is logically abstract and must be overridden by descendants. The rest
    of the functionality is common to both stock types, hence this not a full abstract base class (ABC).

    Args:
        symbol: Human readable stock identifier (e.g. ``TEA``), coerced to uppercase.
        last_dividend: in pence.
        par_value: same units as ``last_dividend``.
        fixed_dividend: percentage.

    Todo:
        In reality this would probably use the ``attrs`` library:
        http://www.attrs.org/en/stable/

        to automate standardised generation of dunder (double underscore) functions 
        however for this example only standard library facilities are used.
    """

    def __init__(self, symbol: str, last_dividend: int, par_value: int, fixed_dividend: Union[int, float, None] = None) -> None:
        self.symbol = symbol.upper()
        self.last_dividend = last_dividend
        self.par_value = par_value
        self.fixed_dividend = fixed_dividend

    def __repr__(self):
        #: PEP 498 string interpolation not used to maintain Python 3.5 compatibility.
        return "<Stock object `{}`>".format(self.symbol)

    def dividend_yield(self, price: int) -> float:
        """
        Calculate the dividend yield for a given price

        Args:
            price: in pence.

        Returns:
            The dividend yield
        """        
        raise NotImplementedError()

    def pe_ratio(self, price: int) -> float:
        """
        Calculate the P/E ratio for a given price

        Args:
            price: in pence.

        Returns:
            P/E ratio expressed as ``price / dividend``
        """
        return 1 / self.dividend_yield(price)


class CommonStock(Stock):
    """A common stock"""

    def __repr__(self):
        return "<CommonStock object `{}`>".format(self.symbol)

    def dividend_yield(self, price: Union[int, float]) -> float:
        """Calculate the yield for a given price based on ``last_dividend``"""
        return self.last_dividend / price


class PreferredStock(Stock):
    """A preferred stock"""

    def __repr__(self):
        return "<PreferredStock object `{}`>".format(self.symbol)

    def dividend_yield(self, price: Union[int, float]) -> float:
        """Calculate the yield for a given price based on ``fixed_dividend``"""
        if self.fixed_dividend is not None:
            return (self.fixed_dividend * self.par_value) / price
        else:
            #: Necessary to satisfy static type analysis with the current class structure
            return 0

@unique
class TradeType(Enum):
    """Direction of the trade"""
    buy = 1
    sell = -1

class Trade(object):
    """
    An instance of a trade on the exchange
    
    Args:
        stock: :class:`sssm.Stock` object or associated symbol (str)
        quantity: The number of stocks traded
        action: :class:`sssm.TradeType` `sssm.TradeType.buy`` or `sssm.TradeType.sell`
        price: self explanatory
    """

    def __init__(self, stock: str, quantity: int, action: TradeType, price: Union[int, float]) -> None:
        self.stock = stock
        self.quantity = quantity
        self.action = action
        self.price = price
        #: Date/time of trade, automatically set to UTC.
        #: This exists to support integration test 2b as specified (i.e. disregarding obvious issues with
        #: time/trade synchronisation and clock validation).
        self.timestamp = datetime.utcnow()

    def __repr__(self):
        return "<Trade object: {} {} of stock `{}`>".format(self.action, self.quantity,
                                                            self.stock.symbol)

    @staticmethod
    def volume_weighted_price(trades: Sequence) -> float:
        """Return the volume weighted price for a sequence of trades"""
        return (sum(trade.price * trade.quantity for trade in trades) /
                sum(trade.quantity for trade in trades))


class Exchange(object):
    """A stock exchange"""

    def __init__(self):
        #: More efficient than a ``list``
        self.trades = collections.deque()

    def __repr__(self):
        return "<Exchange object: {} trades>".format(len(self.trades))

    def record_trade(self, trade: Trade) -> None:
        """Record a trade on the stock exchange"""
        self.trades.append(trade)

    def price_by_stock(self, symbol: str, duration: int) -> Union[float, None]:
        """
        Return the volume weighted average price of a stock over the last ``duration`` seconds.
        Five minutes is therefore ``duration=300`` (integration test 2.a.4)

        Returns:
            The volume weighted average trading price or ``None`` if there are no trades for this stock
        """
        trades = [trade for trade in self.trades 
                  if trade.stock.symbol == symbol.upper() and 
                  trade.timestamp >= datetime.utcnow() - timedelta(seconds=duration)]
        if trades:
            return Trade.volume_weighted_price(trades)
        else:
            return None

    def all_share_index(self, duration: Union[int, None]) -> Union[float, None]:
        """
        Return the All Share Index using the geometric mean of the Volume Weighted Stock Price for all stocks        
        over the last ``duration`` seconds or for all time if ``duration`` is zero or ``None``.

        Returns:
            The All Share Index or ``None`` if there are no trades in the relevant timeframe.
        """     
        # Could be re-framed to use a lambda function, but that creates an unnecessary closure/stack frame  
        def include(trade: Trade) -> bool:
            if duration:
                return trade.timestamp >= datetime.utcnow() - timedelta(seconds=duration)
            else:
                return True

        # `groupby` requires a sorted list
        trades = sorted([trade for trade in self.trades                         
                         if include(trade)], key=attrgetter('stock.symbol'))
        if trades:
            groups = groupby(trades, key=attrgetter('stock.symbol'))
            prices = [Trade.volume_weighted_price(list(trades))
                      for symbol, trades in groups]
            return reduce(mul, prices) ** (1 / len(prices))
        else:
            return None
