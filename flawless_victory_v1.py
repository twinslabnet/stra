# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import math

import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame

from freqtrade.strategy import IStrategy

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import IntParameter


def optimize(space: str):
    def fn(val: int):
        perc = 0.5

        low = math.floor(val * (1 - perc))
        high = math.floor(val * (1 + perc))

        return IntParameter(default=val, low=low, high=high, space=space,
                            optimize=True, load=True)

    return fn


# This strategy is based on https://www.tradingview.com/script/i3Uc79fF-Flawless-Victory-Strategy-15min-BTC-Machine-Learning-Strategy/
# Author of the original Pinescript strategy: Robert Roman (https://github.com/TreborNamor)
class FlawlessVictory(IStrategy):
    buyOptimize = optimize('buy')
    sellOptimize = optimize('sell')

    buy_rsi_length = buyOptimize(14)
    buy_bb_window = buyOptimize(20)
    buy_rsi_lower = buyOptimize(43)

    sell_rsi_length = sellOptimize(14)
    sell_bb_window = sellOptimize(20)
    sell_rsi_upper = sellOptimize(70)

    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 2

    stoploss = -999999

    # Optimal timeframe for the strategy.
    timeframe = '15m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 50

    # Optional order type mapping.
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }

    plot_config = {
        'main_plot': {
            'bb_upperband': {'color': 'blue'},
            'bb_lowerband': {'color': 'blue'}
        },
        'subplots': {
            "RSI": {
                'rsi': {'color': 'purple'},
                'rsi_lower': {'color': 'black'},
                'rsi_upper': {'color': 'black'}
            }
        }
    }

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe['close'], int(self.buy_rsi_length.value))

        dataframe['rsi_lower'] = int(self.buy_rsi_lower.value)

        bollinger = qtpylib.bollinger_bands(
            dataframe['close'], window=int(self.buy_bb_window.value), stds=1
        )

        dataframe['bb_lowerband'] = bollinger['lower']

        bb_long = dataframe['close'] < dataframe['bb_lowerband']
        rsi_long = dataframe['rsi'] > dataframe['rsi_lower']

        dataframe['buy'] = bb_long & rsi_long
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe['close'], int(self.sell_rsi_length.value))

        dataframe['rsi_upper'] = int(self.sell_rsi_upper.value)

        bollinger = qtpylib.bollinger_bands(
            dataframe['close'], window=int(self.sell_bb_window.value), stds=1
        )

        dataframe['bb_upperband'] = bollinger['upper']

        bb_short = dataframe['close'] > dataframe['bb_upperband']
        rsi_short = dataframe['rsi'] > dataframe['rsi_upper']

        dataframe['sell'] = bb_short & rsi_short
        return dataframe
