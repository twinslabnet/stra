import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy as np
import talib.abstract as ta
from freqtrade.persistence import Trade
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
from datetime import datetime, timedelta
from freqtrade.strategy import merge_informative_pair, CategoricalParameter, DecimalParameter, IntParameter
from functools import reduce



class BcmbigzV1(IStrategy):
    INTERFACE_VERSION = 2

    minimal_roi = {
        "0": 0.038,         # I feel lucky!
        "10": 0.028,
        "40": 0.015,
        "180": 0.018,        # We're going up?
    }


    stoploss = -0.99 # effectively disabled.

    timeframe = '5m'
    inf_1h = '1h'

    # Sell signal
    use_sell_signal = True
    sell_profit_only = False
    sell_profit_offset = 0.001 # it doesn't meant anything, just to guarantee there is a minimal profit.
    ignore_roi_if_buy_signal = False

    # Trailing stoploss
    trailing_stop = False
    trailing_only_offset_is_reached = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.025

    # Custom stoploss
    use_custom_stoploss = True

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 200

    # Optional order type mapping.
    order_types = {
        'buy': 'market',
        'sell': 'market',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    buy_params = {
        #############
        # Enable/Disable conditions
        "bzv7_buy_condition_0_enable": True,
        "bzv7_buy_condition_1_enable": True,
        "bzv7_buy_condition_2_enable": True,
        "bzv7_buy_condition_3_enable": True,
        "bzv7_buy_condition_4_enable": True,
        "bzv7_buy_condition_5_enable": True,
        "bzv7_buy_condition_6_enable": True,
        "bzv7_buy_condition_7_enable": True,
        "bzv7_buy_condition_8_enable": True,
        "bzv7_buy_condition_9_enable": True,
        "bzv7_buy_condition_10_enable": True,
        "bzv7_buy_condition_11_enable": True,
        "bzv7_buy_condition_12_enable": True,
        "bzv7_buy_condition_13_enable": True,
    }

    ############################################################################

    # BigZ07 Strategy Buy HyperParam

    bzv7_buy_condition_0_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_1_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_2_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_3_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_4_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_5_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_6_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_7_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_8_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_9_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_10_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_11_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_12_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)
    bzv7_buy_condition_13_enable = CategoricalParameter([True, False], default=True, space='buy', optimize=False, load=True)

    bzv7_buy_bb20_close_bblowerband_safe_1 = DecimalParameter(0.7, 1.1, default=0.989, space='buy', optimize=False, load=True)
    bzv7_buy_bb20_close_bblowerband_safe_2 = DecimalParameter(0.7, 1.1, default=0.982, space='buy', optimize=False, load=True)

    bzv7_buy_volume_pump_1 = DecimalParameter(0.1, 0.9, default=0.4, space='buy', decimals=1, optimize=False, load=True)
    bzv7_buy_volume_drop_1 = DecimalParameter(1, 10, default=3.8, space='buy', decimals=1, optimize=False, load=True)
    bzv7_buy_volume_drop_2 = DecimalParameter(1, 10, default=3, space='buy', decimals=1, optimize=False, load=True)
    bzv7_buy_volume_drop_3 = DecimalParameter(1, 10, default=2.7, space='buy', decimals=1, optimize=False, load=True)

    bzv7_buy_rsi_1h_1 = DecimalParameter(10.0, 40.0, default=16.5, space='buy', decimals=1, optimize=False, load=True)
    bzv7_buy_rsi_1h_2 = DecimalParameter(10.0, 40.0, default=15.0, space='buy', decimals=1, optimize=False, load=True)
    bzv7_buy_rsi_1h_3 = DecimalParameter(10.0, 40.0, default=20.0, space='buy', decimals=1, optimize=False, load=True)
    bzv7_buy_rsi_1h_4 = DecimalParameter(10.0, 40.0, default=35.0, space='buy', decimals=1, optimize=False, load=True)
    bzv7_buy_rsi_1h_5 = DecimalParameter(10.0, 60.0, default=39.0, space='buy', decimals=1, optimize=False, load=True)

    bzv7_buy_rsi_1 = DecimalParameter(10.0, 40.0, default=28.0, space='buy', decimals=1, optimize=False, load=True)
    bzv7_buy_rsi_2 = DecimalParameter(7.0, 40.0, default=10.0, space='buy', decimals=1, optimize=False, load=True)
    bzv7_buy_rsi_3 = DecimalParameter(7.0, 40.0, default=14.2, space='buy', decimals=1, optimize=False, load=True)

    bzv7_buy_macd_1 = DecimalParameter(0.01, 0.09, default=0.02, space='buy', decimals=2, optimize=False, load=True)
    bzv7_buy_macd_2 = DecimalParameter(0.01, 0.09, default=0.03, space='buy', decimals=2, optimize=False, load=True)

    def confirm_trade_exit(self, pair: str, trade: Trade, order_type: str, amount: float,
                           rate: float, time_in_force: str, sell_reason: str, **kwargs) -> bool:


        return True

        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()
        last_candle_1 = dataframe.iloc[-2].squeeze()

        if (sell_reason == 'roi'):
            # Looks like we can get a little have more
            if (last_candle['cmf'] < -0.1) & (last_candle['close'] > last_candle['ema_200_1h']):
                return False

        return True


    def custom_sell(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):

        return False

        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()
        last_candle_2 = dataframe.iloc[-2].squeeze()

        if (last_candle is not None):
            if (last_candle['high'] > last_candle['bb_upperband']) & (last_candle['volume'] > (last_candle_2['volume'] * 1.5)):
                return 'sell_signal_1'

        return False


    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        # Manage losing trades and open room for better ones.

        if (current_profit > 0):
            return 0.99
        else:
            trade_time_50 = trade.open_date_utc + timedelta(minutes=50)

            # Trade open more then 60 minutes. For this strategy it's means -> loss
            # Let's try to minimize the loss

            if (current_time > trade_time_50):

                try:
                    number_of_candle_shift = int((current_time - trade_time_50).total_seconds() / 300)
                    dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
                    candle = dataframe.iloc[-number_of_candle_shift].squeeze()

                    # We are at bottom. Wait...
                    if candle['rsi_1h'] < 40:
                        return 0.99
 
                    if candle['open_1h'] > candle['ema_200_1h']:
                            return 0.1

                    # Are we still sinking?
                    if current_rate * 1.025 < candle['open']:
                        return 0.01

                except IndexError as error:

                    # Whoops, set stoploss at 10%
                    return 0.1

        return 0.99

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, '1h') for pair in pairs]
        return informative_pairs

    def informative_1h_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        assert self.dp, "DataProvider is required for multiple timeframes."
        # Get the informative pair
        informative_1h = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=self.inf_1h)
        # EMA
        informative_1h['ema_50'] = ta.EMA(informative_1h, timeperiod=50)
        informative_1h['ema_200'] = ta.EMA(informative_1h, timeperiod=200)
        # RSI
        informative_1h['rsi'] = ta.RSI(informative_1h, timeperiod=14)

        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        informative_1h['bb_lowerband'] = bollinger['lower']
        informative_1h['bb_middleband'] = bollinger['mid']
        informative_1h['bb_upperband'] = bollinger['upper']

        return informative_1h

    def normal_tf_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['bb_upperband'] = bollinger['upper']

        dataframe['volume_mean_slow'] = dataframe['volume'].rolling(window=48).mean()

        # EMA
        dataframe['ema_200'] = ta.EMA(dataframe, timeperiod=200)

        dataframe['ema_26'] = ta.EMA(dataframe, timeperiod=26)
        dataframe['ema_12'] = ta.EMA(dataframe, timeperiod=12)

        # MACD 
        dataframe['macd'], dataframe['signal'], dataframe['hist'] = ta.MACD(dataframe['close'], fastperiod=12, slowperiod=26, signalperiod=9)

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        # Chaikin A/D Oscillator
        dataframe['mfv'] = MFV(dataframe)
        dataframe['cmf'] = dataframe['mfv'].rolling(20).sum()/dataframe['volume'].rolling(20).sum()

        return dataframe


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # The indicators for the 1h informative timeframe
        informative_1h = self.informative_1h_indicators(dataframe, metadata)
        dataframe = merge_informative_pair(dataframe, informative_1h, self.timeframe, self.inf_1h, ffill=True)

        # The indicators for the normal (5m) timeframe
        dataframe = self.normal_tf_indicators(dataframe, metadata)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions = []

        conditions.append(
            (
                self.bzv7_buy_condition_13_enable.value &

                (dataframe['close'] > dataframe['ema_200_1h']) &

                (dataframe['cmf'] < -0.435) &
                (dataframe['rsi'] < 22) &

                (dataframe['volume_mean_slow'] > dataframe['volume_mean_slow'].shift(48) * self.bzv7_buy_volume_pump_1.value) &
                (dataframe['volume_mean_slow'] * self.bzv7_buy_volume_pump_1.value < dataframe['volume_mean_slow'].shift(48)) &
                (dataframe['volume'] > 0)
            )
        )


        conditions.append(
            (
                self.bzv7_buy_condition_12_enable.value &

                (dataframe['close'] > dataframe['ema_200']) &
                (dataframe['close'] > dataframe['ema_200_1h']) &

                (dataframe['close'] < dataframe['bb_lowerband'] * 0.993) &
                (dataframe['low'] < dataframe['bb_lowerband'] * 0.985) &
                (dataframe['close'].shift() > dataframe['bb_lowerband']) &
                (dataframe['rsi_1h'] < 72.8) &
                (dataframe['open'] > dataframe['close']) &
                
                (dataframe['volume_mean_slow'] > dataframe['volume_mean_slow'].shift(48) * self.bzv7_buy_volume_pump_1.value) &
                (dataframe['volume_mean_slow'] * self.bzv7_buy_volume_pump_1.value < dataframe['volume_mean_slow'].shift(48)) &
                (dataframe['volume'] < (dataframe['volume'].shift() * self.bzv7_buy_volume_drop_1.value)) &
                ((dataframe['open'] - dataframe['close']) < dataframe['bb_upperband'].shift(2) - dataframe['bb_lowerband'].shift(2)) &

                (dataframe['volume'] > 0)
            )
        )

        conditions.append(
            (
                self.bzv7_buy_condition_11_enable.value &

                (dataframe['close'] > dataframe['ema_200']) &

                (dataframe['hist'] > 0) &
                (dataframe['hist'].shift() > 0) &
                (dataframe['hist'].shift(2) > 0) &
                (dataframe['hist'].shift(3) > 0) &
                (dataframe['hist'].shift(5) > 0) &

                (dataframe['bb_middleband'] - dataframe['bb_middleband'].shift(5) > dataframe['close']/200) &
                (dataframe['bb_middleband'] - dataframe['bb_middleband'].shift(10) > dataframe['close']/100) &
                ((dataframe['bb_upperband'] - dataframe['bb_lowerband']) < (dataframe['close']*0.1)) &
                ((dataframe['open'].shift() - dataframe['close'].shift()) < (dataframe['close'] * 0.018)) &
                (dataframe['rsi'] > 51) &

                (dataframe['open'] < dataframe['close']) &
                (dataframe['open'].shift() > dataframe['close'].shift()) &

                (dataframe['close'] > dataframe['bb_middleband']) &
                (dataframe['close'].shift() < dataframe['bb_middleband'].shift()) &
                (dataframe['low'].shift(2) > dataframe['bb_middleband'].shift(2)) &

                (dataframe['volume'] > 0) # Make sure Volume is not 0
            )
        )

        conditions.append(
            (
                self.bzv7_buy_condition_0_enable.value &

                (dataframe['close'] > dataframe['ema_200']) &

                (dataframe['rsi'] < 30) &
                (dataframe['close'] * 1.024 < dataframe['open'].shift(3)) &
                (dataframe['rsi_1h'] < 71) &

                (dataframe['volume_mean_slow'] > dataframe['volume_mean_slow'].shift(48) * self.bzv7_buy_volume_pump_1.value) &
                (dataframe['volume_mean_slow'] * self.bzv7_buy_volume_pump_1.value < dataframe['volume_mean_slow'].shift(48)) &
                (dataframe['volume'] > 0) # Make sure Volume is not 0
            )
        )

        conditions.append(
            (
                self.bzv7_buy_condition_1_enable.value &

                (dataframe['close'] > dataframe['ema_200']) &
                (dataframe['close'] > dataframe['ema_200_1h']) &

                (dataframe['close'] <  dataframe['bb_lowerband'] * self.bzv7_buy_bb20_close_bblowerband_safe_1.value) &
                (dataframe['rsi_1h'] < 69) &
                (dataframe['open'] > dataframe['close']) &
                
                (dataframe['volume_mean_slow'] > dataframe['volume_mean_slow'].shift(48) * self.bzv7_buy_volume_pump_1.value) &
                (dataframe['volume_mean_slow'] * self.bzv7_buy_volume_pump_1.value < dataframe['volume_mean_slow'].shift(48)) &
                (dataframe['volume'] < (dataframe['volume'].shift() * self.bzv7_buy_volume_drop_1.value)) &
                ((dataframe['open'] - dataframe['close']) < dataframe['bb_upperband'].shift(2) - dataframe['bb_lowerband'].shift(2)) &

                (dataframe['volume'] > 0)
            )
        )

        conditions.append(
            (
                self.bzv7_buy_condition_2_enable.value &

                (dataframe['close'] > dataframe['ema_200']) &

                (dataframe['close'] < dataframe['bb_lowerband'] *  self.bzv7_buy_bb20_close_bblowerband_safe_2.value) &

                (dataframe['volume_mean_slow'] > dataframe['volume_mean_slow'].shift(48) * self.bzv7_buy_volume_pump_1.value) &
                (dataframe['volume_mean_slow'] * self.bzv7_buy_volume_pump_1.value < dataframe['volume_mean_slow'].shift(48)) &
                (dataframe['volume'] < (dataframe['volume'].shift() * self.bzv7_buy_volume_drop_1.value)) &
                (dataframe['open'] - dataframe['close'] < dataframe['bb_upperband'].shift(2) - dataframe['bb_lowerband'].shift(2)) &
                (dataframe['volume'] > 0)
            )
        )

        conditions.append(
            (
                self.bzv7_buy_condition_3_enable.value &

                (dataframe['close'] > dataframe['ema_200_1h']) &

                (dataframe['close'] < dataframe['bb_lowerband']) &
                (dataframe['rsi'] < self.bzv7_buy_rsi_3.value) &

                (dataframe['volume_mean_slow'] > dataframe['volume_mean_slow'].shift(48) * self.bzv7_buy_volume_pump_1.value) &
                (dataframe['volume_mean_slow'] * self.bzv7_buy_volume_pump_1.value < dataframe['volume_mean_slow'].shift(48)) &
                (dataframe['volume'] < (dataframe['volume'].shift() * self.bzv7_buy_volume_drop_3.value)) &

                (dataframe['volume'] > 0)
            )
        )

        conditions.append(
            (
                self.bzv7_buy_condition_4_enable.value &

                (dataframe['rsi_1h'] < self.bzv7_buy_rsi_1h_1.value) &

                (dataframe['close'] < dataframe['bb_lowerband']) &

                (dataframe['volume_mean_slow'] > dataframe['volume_mean_slow'].shift(48) * self.bzv7_buy_volume_pump_1.value) &
                (dataframe['volume_mean_slow'] * self.bzv7_buy_volume_pump_1.value < dataframe['volume_mean_slow'].shift(48)) &
                (dataframe['volume'] < (dataframe['volume'].shift() * self.bzv7_buy_volume_drop_1.value)) &
                (dataframe['volume'] > 0)
            )
        )

        conditions.append(
            (
                self.bzv7_buy_condition_5_enable.value &

                (dataframe['close'] > dataframe['ema_200']) &
                (dataframe['close'] > dataframe['ema_200_1h']) &

                (dataframe['ema_26'] > dataframe['ema_12']) &
                ((dataframe['ema_26'] - dataframe['ema_12']) > (dataframe['open'] * self.bzv7_buy_macd_1.value)) &
                ((dataframe['ema_26'].shift() - dataframe['ema_12'].shift()) > (dataframe['open']/100)) &
                (dataframe['close'] < (dataframe['bb_lowerband'])) &

                (dataframe['volume'] < (dataframe['volume'].shift() * self.bzv7_buy_volume_drop_1.value)) &
                (dataframe['volume_mean_slow'] > dataframe['volume_mean_slow'].shift(48) * self.bzv7_buy_volume_pump_1.value) &
                (dataframe['volume_mean_slow'] * self.bzv7_buy_volume_pump_1.value < dataframe['volume_mean_slow'].shift(48)) &
                (dataframe['volume'] > 0) # Make sure Volume is not 0
            )
        )

        conditions.append(
            (
                self.bzv7_buy_condition_6_enable.value &

                (dataframe['rsi_1h'] < self.bzv7_buy_rsi_1h_5.value) &

                (dataframe['ema_26'] > dataframe['ema_12']) &
                ((dataframe['ema_26'] - dataframe['ema_12']) > (dataframe['open'] * self.bzv7_buy_macd_2.value)) &
                ((dataframe['ema_26'].shift() - dataframe['ema_12'].shift()) > (dataframe['open']/100)) &
                (dataframe['close'] < (dataframe['bb_lowerband'])) &

                (dataframe['volume_mean_slow'] > dataframe['volume_mean_slow'].shift(48) * self.bzv7_buy_volume_pump_1.value) &
                (dataframe['volume_mean_slow'] * self.bzv7_buy_volume_pump_1.value < dataframe['volume_mean_slow'].shift(48)) &
                (dataframe['volume'] < (dataframe['volume'].shift() * self.bzv7_buy_volume_drop_1.value)) &
                (dataframe['volume'] > 0)
            )
        )

        conditions.append(
            (
                self.bzv7_buy_condition_7_enable.value &

                (dataframe['rsi_1h'] < self.bzv7_buy_rsi_1h_2.value) &
                
                (dataframe['ema_26'] > dataframe['ema_12']) &
                ((dataframe['ema_26'] - dataframe['ema_12']) > (dataframe['open'] * self.bzv7_buy_macd_1.value)) &
                ((dataframe['ema_26'].shift() - dataframe['ema_12'].shift()) > (dataframe['open']/100)) &
                
                (dataframe['volume'] < (dataframe['volume'].shift() * self.bzv7_buy_volume_drop_1.value)) &
                (dataframe['volume_mean_slow'] > dataframe['volume_mean_slow'].shift(48) * self.bzv7_buy_volume_pump_1.value) &
                (dataframe['volume_mean_slow'] * self.bzv7_buy_volume_pump_1.value < dataframe['volume_mean_slow'].shift(48)) &
                (dataframe['volume'] > 0)
            )
        )


        conditions.append(
            (

                self.bzv7_buy_condition_8_enable.value &

                (dataframe['rsi_1h'] < self.bzv7_buy_rsi_1h_3.value) &
                (dataframe['rsi'] < self.bzv7_buy_rsi_1.value) &
                
                (dataframe['volume'] < (dataframe['volume'].shift() * self.bzv7_buy_volume_drop_1.value)) &

                (dataframe['volume'] > 0)
            )
        )

        conditions.append(
            (

                self.bzv7_buy_condition_9_enable.value &

                (dataframe['rsi_1h'] < self.bzv7_buy_rsi_1h_4.value) &
                (dataframe['rsi'] < self.bzv7_buy_rsi_2.value) &
                
                (dataframe['volume'] < (dataframe['volume'].shift() * self.bzv7_buy_volume_drop_1.value)) &
                (dataframe['volume_mean_slow'] > dataframe['volume_mean_slow'].shift(48) * self.bzv7_buy_volume_pump_1.value) &
                (dataframe['volume_mean_slow'] * self.bzv7_buy_volume_pump_1.value < dataframe['volume_mean_slow'].shift(48)) &
                (dataframe['volume'] > 0)
            )
        )

        conditions.append(
            (

                self.bzv7_buy_condition_10_enable.value &

                (dataframe['rsi_1h'] < self.bzv7_buy_rsi_1h_4.value) &
                (dataframe['close_1h'] < dataframe['bb_lowerband_1h']) &

                (dataframe['hist'] > 0) &
                (dataframe['hist'].shift(2) < 0) &
                (dataframe['rsi'] < 40.5) &
                (dataframe['hist'] > dataframe['close'] * 0.0012) &
                (dataframe['open'] < dataframe['close']) &
                
                (dataframe['volume'] > 0)
            )
        )

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'buy'
            ] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['bb_middleband'] * 1.01) &                  # Don't be gready, sell fast
                (dataframe['volume'] > 0) # Make sure Volume is not 0
            )
            ,
            'sell'
        ] = 0
        return dataframe

# Chaikin Money Flow Volume
def MFV(dataframe):
    df = dataframe.copy()
    N = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
    M = N * df['volume']
    return M