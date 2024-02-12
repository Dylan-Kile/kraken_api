import unittest
from kraken_api.model.candle import Candle
from trader.trade_finder import bullish_engulfing, hammer


class TestTradeFinder(unittest.TestCase):
    def test_bullish_engulfing_succeeds(self):
        candle_one = Candle(1, 100, 120, 35, 50, 0, 0, 0)
        candle_two = Candle(2, 45, 150, 40, 120, 0, 0, 0)

        self.assertTrue(bullish_engulfing([candle_one, candle_two, None]))

    def test_bullish_engulfing_fails_if_second_opens_above(self):
        candle_one = Candle(1, 100, 120, 35, 50, 0, 0, 0)
        candle_two = Candle(2, 55, 150, 40, 120, 0, 0, 0)

        self.assertFalse(bullish_engulfing([candle_one, candle_two, None]))

    def test_bullish_engulfing_fails_if_not_increasing(self):
        candle_one = Candle(1, 100, 120, 35, 50, 0, 0, 0)
        candle_two = Candle(2, 55, 150, 40, 120, 0, 0, 0)

        self.assertFalse(bullish_engulfing([candle_two, candle_one, None]))

    def test_hammer_for_pair_that_isnt_hammer(self):
        candle = Candle(1, 2.792, 2.801, 2.775, 2.788, 0, 0, 0)

        self.assertFalse(hammer([candle, None]))


if __name__ == "__main__":
    unittest.main()
