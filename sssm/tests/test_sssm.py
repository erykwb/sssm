# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import MagicMock as MMock
from datetime import datetime, timedelta
import sssm

FIVE_MINUTES = (60*5)

class TestStock(TestCase):
    def test_01_create_stock(self):
        stock = sssm.Stock('TEST', last_dividend=0, par_value=100)
        self.assertEqual('TEST', stock.symbol)
        self.assertEqual(0, stock.last_dividend)
        self.assertEqual(100, stock.par_value)
        self.assertIsNone(stock.fixed_dividend)

    def test_02_verify_symbol_coerced_to_uppercase(self):
        stock = sssm.Stock('test', last_dividend=0, par_value=100)
        self.assertEqual('TEST', stock.symbol)

    def test_03_stock_dividend_yield_not_implemented(self):
        stock = sssm.Stock('TEST', last_dividend=0, par_value=100)
        with self.assertRaises(NotImplementedError):
            stock.dividend_yield(price=100)

    def test_04_common_dividend_yield(self):
        stock = sssm.CommonStock('POP', last_dividend=8, par_value=100)
        self.assertEqual(0.08, stock.dividend_yield(price=100))

    def test_05_common_zero_dividend_yield(self):
        stock = sssm.CommonStock('TEA', last_dividend=0, par_value=100)
        self.assertEqual(0.00, stock.dividend_yield(price=100))        

    def test_06_common_negative_dividend_yield(self):
        stock = sssm.CommonStock('TEA', last_dividend=-8, par_value=100)
        self.assertEqual(-0.08, stock.dividend_yield(price=100)) 

    def test_07_preferred_dividend_yield(self):
        stock = sssm.PreferredStock('GIN', last_dividend=8, fixed_dividend=0.02, par_value=100)
        self.assertEqual(0.02, stock.dividend_yield(price=100))

    def test_08_preferred_zero_dividend_yield(self):
        stock = sssm.PreferredStock('GIN', last_dividend=8, fixed_dividend=0.00, par_value=100)
        self.assertEqual(0.00, stock.dividend_yield(price=100))        

    def test_09_common_pe_ratio(self):
        stock = sssm.CommonStock('POP', last_dividend=8, par_value=100)
        self.assertEqual(12.5, stock.pe_ratio(price=100))

    def test_10_preferred_pe_ratio(self):
        stock = sssm.PreferredStock('GIN', last_dividend=8, fixed_dividend=0.02, par_value=100)
        self.assertEqual(50, stock.pe_ratio(price=100))


class TestTrade(TestCase):
    def test_01_create_buy_trade(self):
        stock = MMock()
        trade = sssm.Trade(stock=stock, quantity=64, action=sssm.TradeType.buy, price=100)
        self.assertEqual(stock, trade.stock)
        self.assertEqual(64, trade.quantity)
        self.assertEqual(sssm.TradeType.buy, trade.action)
        self.assertEqual(100, trade.price)        
        self.assertLessEqual((trade.timestamp - datetime.utcnow()).total_seconds(), 0.1)

    def test_02_create_sell_trade(self):
        stock = MMock()
        trade = sssm.Trade(stock=stock, quantity=32, action=sssm.TradeType.sell, price=100)
        self.assertEqual(sssm.TradeType.sell, trade.action)

    def test_03_volume_weighted_price(self):
        stock = MMock()
        trades = [
            sssm.Trade(stock=stock, quantity=16, action=sssm.TradeType.buy, price=100),
            sssm.Trade(stock=stock, quantity=8, action=sssm.TradeType.buy, price=50)
        ]
        self.assertAlmostEqual(83.3333333, sssm.Trade.volume_weighted_price(trades))


class TestExchange(TestCase):
    def test_01_create_exchange(self):
        exchange = sssm.Exchange()
        # Test that the Exchange is initialised empty
        self.assertEqual(0, len(exchange.trades))

    def test_02_record_trade(self):
        exchange = sssm.Exchange()
        trade = MMock()
        exchange.record_trade(trade)
        # Test that the last trade is appended to the end of list type class
        self.assertEqual(trade, exchange.trades[-1])

    def test_04_record_multiple_trades(self):
        exchange = sssm.Exchange()
        trades = [MMock(), MMock(), MMock(), MMock(), MMock()]
        for trade in trades:
            exchange.record_trade(trade)
        # Test that trades are recorded
        self.assertEqual(5, len(exchange.trades))
        # Test append order preserved
        self.assertEqual(trades[4], exchange.trades[-1])
        self.assertEqual(trades[0], exchange.trades[0])

    def test_05_volume_weighted_price_by_stock(self):
        exchange = sssm.Exchange()
        stock = MMock(symbol='TEST')
        exchange.trades = [
            sssm.Trade(stock=stock, quantity=16, action=sssm.TradeType.buy, price=100),
            sssm.Trade(stock=stock, quantity=32, action=sssm.TradeType.buy, price=50)
        ]
        self.assertAlmostEqual(66.666666666, exchange.price_by_stock('TEST', duration=5*60))

    def test_06_none_volume_weighted_price_by_stock(self):
        exchange = sssm.Exchange()
        self.assertIsNone(exchange.price_by_stock('TEST', duration=5*60))

    def test_07_volume_weighted_price_by_stock_duration(self):
        exchange = sssm.Exchange()
        stock = MMock(symbol='TEST')
        exchange.trades = [
            sssm.Trade(stock=stock, quantity=16, action=sssm.TradeType.buy, price=100),
            sssm.Trade(stock=stock, quantity=32, action=sssm.TradeType.buy, price=50),
            sssm.Trade(stock=stock, quantity=64, action=sssm.TradeType.buy, price=100)            
        ]
        # Move trade out of specified time interval
        exchange.trades[0].timestamp = (datetime.utcnow() - timedelta(seconds=FIVE_MINUTES+10))
        self.assertAlmostEqual(83.3333333, exchange.price_by_stock('TEST', duration=FIVE_MINUTES))

    def test_08_all_share_index(self):
        exchange = sssm.Exchange()
        exchange.trades = [
            sssm.Trade(stock=MMock(symbol='TEA'), quantity=16, action=sssm.TradeType.buy, price=100),
            sssm.Trade(stock=MMock(symbol='POP'), quantity=32, action=sssm.TradeType.buy, price=50),
            sssm.Trade(stock=MMock(symbol='POP'), quantity=64, action=sssm.TradeType.buy, price=100)            
        ]
        self.assertAlmostEqual(91.2870929, exchange.all_share_index(duration=FIVE_MINUTES))

    def test_09_all_share_index_none(self):
        exchange = sssm.Exchange()
        # No trades added so the share index is None/NULL rather than Zero/0
        self.assertIsNone(exchange.all_share_index(duration=FIVE_MINUTES))
