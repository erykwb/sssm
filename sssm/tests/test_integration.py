# -*- coding: utf-8 -*-

import unittest
from datetime import datetime, timedelta
from sssm import Exchange, CommonStock, PreferredStock, Trade, TradeType


class TestIntegration(unittest.TestCase):
    def test_01_all_acceptance_tests(self):
        exchange = Exchange()
        stocks = {
            'TEA': CommonStock('TEA', last_dividend=0, par_value=100),
            'POP': CommonStock('POP', last_dividend=8, par_value=100),
            'ALE': CommonStock('ALE', last_dividend=23, par_value=60),
            'GIN': PreferredStock('GIN', last_dividend=8, fixed_dividend=0.02, par_value=100),
            'JOE': CommonStock('JOE', last_dividend=13, par_value=250)
        }
        # Requrement 2.a - For a given stock
        # i. Given any price as input, calculate the dividend yield 
        common_dividend_yield = stocks['POP'].dividend_yield(price=100)
        self.assertEqual(0.08, common_dividend_yield)

        preferred_dividend_yield = stocks['GIN'].dividend_yield(price=100)
        self.assertEqual(0.02, preferred_dividend_yield)

        # ii. Given any price as input,  calculate the P/E Ratio 
        pe_ratio = stocks['POP'].pe_ratio(price=100)
        self.assertEqual(12.5, pe_ratio)      

        with self.assertRaises(ZeroDivisionError):
            pe_ratio = stocks['TEA'].pe_ratio(price=100)

        # iii. Record a trade, with timestamp, quantity, buy or sell indicator and price 
        exchange.record_trade(Trade(stocks['TEA'], 42, TradeType.buy, 32))
        exchange.record_trade(Trade(stocks['POP'], 420, TradeType.buy, 8))
        exchange.record_trade(Trade(stocks['POP'], 420, TradeType.buy, 16))        
        exchange.record_trade(Trade(stocks['GIN'], 1000, TradeType.buy, 512))
        exchange.record_trade(Trade(stocks['GIN'], 1000, TradeType.buy, 256))
        exchange.record_trade(Trade(stocks['GIN'], 2000, TradeType.buy, 128))        
        self.assertEqual(6, len(exchange.trades))
        self.assertTrue(all(trade.timestamp >= datetime.utcnow() - timedelta(seconds=0.1)
                            for trade in exchange.trades))

        # iv. Calculate Volume Weighted Stock Price based on trades in past 5 minutes 
        price = exchange.price_by_stock('TEA', duration=5*60)
        self.assertAlmostEqual(32, price)

        price = exchange.price_by_stock('POP', duration=5*60)
        self.assertAlmostEqual(12, price)

        price = exchange.price_by_stock('GIN', duration=5*60)
        self.assertAlmostEqual(256, price)

        # Requirement 2.b - Calculate the GBCE All Share Index using the geometric mean
        # of the Volume Weighted Stock Price for all stocks
        index = exchange.all_share_index(duration=5*60)
        self.assertAlmostEqual(46.1519862, index)
