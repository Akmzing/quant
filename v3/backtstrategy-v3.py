from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
from backtrader import Order
from binance.spot import Spot
import pandas as pd

def getKline(market, mUnit):
    source = client.klines(market, mUnit, limit=100)
    columnList = ['data', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume',
                  'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore']
    data = pd.DataFrame(source, columns=columnList, dtype=float)
    data['data'] = pd.to_datetime(data['data'], unit='ms')
    data.set_index('data', inplace=True)
    print(data)
    return data

def get_csv_kline(coin, date):
    columnList = ['data', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume',
                  'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore']
    df = pd.read_csv('D:\学习\区块链\\biandata\%s\%sUSDT-1m-%s.csv' % (coin, coin.upper(), date), names=columnList)
    df['data'] = pd.to_datetime(df['data'], unit='ms')
    df.set_index('data', inplace=True)
    # print(df)
    return df


rollContinueTargetTime = 2
rollContinueLowTime = 3
lastRollContinueLowTime = 3
rollContinueInvalidCount = 5
rollContinueRecoverCount = 3
emaInitContinueTime = 15
sellPricePercent = 0.02
closePricePercent = 0.02

# Create a Stratey
class TestStrategy(bt.Strategy):
    lines = ('macd', 'signal', 'histo')
    params = (
        ('maperiod', 10),
        ('emaperiod', 1800),
        ('emaperiod1', 600),
        ('em1_period', 12),
        ('em2_period', 26),
        ('signal_period', 9),
        ('rollContinueTargetTime', rollContinueTargetTime),
        ('rollContinueLowTime', rollContinueLowTime),
        ('lastRollContinueLowTime', lastRollContinueLowTime),
        ('rollContinueInvalidCount', rollContinueInvalidCount),
        ('rollContinueRecoverCount', rollContinueRecoverCount),
        ('emaInitContinueTime', emaInitContinueTime),
        ('sellPricePercent', sellPricePercent),
        ('closePricePercent', closePricePercent),
        # ('initLineRate', 0.45)
        # # 持续多少次rollContinue后，购买
        # ('rollContinueBuyTime', 3),
        # # rollContinue天数，少于均线的次数
        # ('rollContinueDay', 3),
        # # rollContinueDayInvalidDay，少于均线后，失效天数
        # ('rollContinueInvalidDay', 2),
        # # ema初始Continue天数
        # ('emaInitContinueDay', 15)
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        print('%s, %s' % (self.datas[0].datetime.date(0).isoformat() + ' ' + self.datas[0].datetime.time().isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.dataopen = self.datas[0].open
        self.datalow = self.datas[0].low

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.status = 'Init'
        self.rollContinueTime = 0
        self.curRollContinueInvalidCount = 0
        self.curRollContinueRecoverCount = 0

        self.sellPrice = 0.0
        self.closePrice = 0.0
        self.macdlist = [0.0, 0.0, 0.0]
        self.rollHighlist = [0.0, 0.0, 0.0]

        # Add a MovingAverageSimple indicator
        # self.sma = bt.indicators.SimpleMovingAverage(
        #     self.datas[0], period=self.params.maperiod)
        self.ema = bt.indicators.EMA(self.data, period=self.params.emaperiod)
        self.ema1 = bt.indicators.EMA(self.data, period=self.params.emaperiod1)

        self.macd = bt.indicators.MACD(self.data,
                                       period_me1=self.p.em1_period,
                                       period_me2=self.p.em2_period,
                                       period_signal=self.p.signal_period)

        self.rsi = bt.indicators.RSI_Safe(self.datas[0], period=6)
        self.rsi1 = bt.indicators.RSI_Safe(self.datas[0], period=12)
        self.rsi2 = bt.indicators.RSI_Safe(self.datas[0], period=24)

    def notify_order(self, order):
        global buyTime, sellTime, successTime
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f, targetSellPrice: %.2f, targetClosePrice: %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm,
                     self.sellPrice,
                     self.closePrice))
                buyTime += 1
                self.reset_judge()

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.sellPrice = order.executed.price * (1.0 - self.params.sellPricePercent)
                self.closePrice = order.executed.price * (1.0 + self.params.closePricePercent)
            else:  # Sell
                self.log(
                    'SELL EXECUTED, Price: %.4f, Cost: %.4f, Comm %.4f, macd: %.5f, signal: %.5f, histo: %.5f rsi: %.2f, ema: %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm,
                     self.macd.macd[0], self.macd.signal[0], self.macd.macd[0] - self.macd.signal[0], self.rsi[0],
                     self.ema[0]))
                # self.buyprice = order.executed.price
                # self.buycomm = order.executed.comm
                # self.sellPrice = order.executed.price * (1.0 - self.params.sellPricePercent)
                # self.closePrice = order.executed.price * (1.0 + self.params.closePricePercent)
                sellTime += 1

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        global successTime
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f\n' %
                 (trade.pnl, trade.pnlcomm))
        if trade.pnl > 0.0:
            successTime += 1

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # 可以购买
            if self.is_can_buy():
                # BUY, BUY, BUY!!! (with all possible default parameters)
                # self.log('BUY CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                size = int(50000.0 / self.dataopen[0])
                self.order = self.buy(size=size)
                self.log(
                    'SELL CREATE, macd: %.5f, signal: %.5f, histo: %.5f rsi: %.2f, %.2f, %.2f, ema: %.2f, macdlist: %s, rollHighlist: %s' %
                    (self.macd.macd[0], self.macd.signal[0], self.macd.macd[0] - self.macd.signal[0], self.rsi[0], self.rsi1[0], self.rsi2[0],
                     self.ema[0], self.macdlist, self.rollHighlist))

        else:

            if self.dataopen[0] <= self.ema1[0]:
                # 小于均线卖卖卖！
                # self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell(exectype=Order.Limit, size=self.position.size)
                # self.reset_judge()

    def is_can_buy(self):
        if self.ema[0] < self.dataopen[0]:
            return True
        else:
            return False

    def reset_judge(self):
        self.status = 'Init'
        self.rollContinueTime = 0
        self.curRollContinueInvalidCount = 0
        self.curRollContinueRecoverCount = 0
        self.sellPrice = 0.0
        self.closePrice = 0.0
        self.rollHighlist = [0.0, 0.0, 0.0]

total_profit = 0.0
buyTime = 0
sellTime = 0
successTime = 0
total_buyTime = 0
total_sellTime = 0
total_successTime = 0

def backt_strategy_run(coin, date):
    global buyTime, sellTime, successTime
    buyTime = 0
    sellTime = 0
    successTime = 0

    cerebro = bt.Cerebro()
    initCrash = 2500000.0
    crashMul = 20.0
    cerebro.broker.setcash(initCrash * crashMul)
    cerebro.addstrategy(TestStrategy)

    # Get klines of BTCUSDT at 1m interval
    # print(client.klines("APEUSDT", "1m", limit=10))
    # Get last 10 klines of BNBUSDT at 1h interval
    # print(client.klines("BNBUSDT", "1h", limit=10))

    # feed = bt.feeds.PandasData(dataname=getKline('APEUSDT', '1m'))
    feed = bt.feeds.PandasData(dataname=get_csv_kline(coin, date))
    cerebro.adddata(feed)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.0004)
    # Add a FixedSize sizer according to the stake 每次买卖的股数量
    cerebro.addsizer(bt.sizers.FixedSize, stake=200)

    # print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    print('日期：%s' % date)
    print('本金：%.2fU' % initCrash)
    print('收入：%.2fU' % (cerebro.broker.getvalue() - initCrash * crashMul))
    print("买次数：%d" % buyTime)
    print("卖次数：%d" % sellTime)
    print("成功次数：%d" % successTime)
    if buyTime != 0:
        print("成功率：%.2f%%" % (100.0 * successTime / buyTime))

    # print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    global total_profit
    total_profit += (cerebro.broker.getvalue() - initCrash * crashMul)
    print('总收益：%.2f' % total_profit)

    global total_buyTime, total_sellTime, total_successTime
    total_buyTime += buyTime
    total_sellTime += sellTime
    total_successTime += successTime

    # cerebro.plot()

if __name__ == '__main__':
    coin = 'eth'
    backt_strategy_run(coin, '2021-05')
    backt_strategy_run(coin, '2021-06')
    backt_strategy_run(coin, '2021-07')
    backt_strategy_run(coin, '2021-08')
    backt_strategy_run(coin, '2021-09')
    backt_strategy_run(coin, '2021-10')
    backt_strategy_run(coin, '2021-11')
    backt_strategy_run(coin, '2021-12')
    backt_strategy_run(coin, '2022-01')
    backt_strategy_run(coin, '2022-02')
    backt_strategy_run(coin, '2022-03')
    backt_strategy_run(coin, '2022-04')
    #
    # backt_strategy_run(coin, '2020-05')
    # backt_strategy_run(coin, '2020-06')
    # backt_strategy_run(coin, '2020-07')
    # backt_strategy_run(coin, '2020-08')
    # backt_strategy_run(coin, '2020-09')
    # backt_strategy_run(coin, '2020-10')
    # backt_strategy_run(coin, '2020-11')
    # backt_strategy_run(coin, '2020-12')
    # backt_strategy_run(coin, '2021-01')
    # backt_strategy_run(coin, '2021-02')
    # backt_strategy_run(coin, '2021-03')
    # backt_strategy_run(coin, '2021-04')

    print('\n币：' + coin)
    print("总买次数：%d" % total_buyTime)
    print("总卖次数：%d" % total_sellTime)
    print("总成功次数：%d" % total_successTime)
    total_success_rate = 0.0
    if total_buyTime != 0:
        total_success_rate = (100.0 * total_successTime / total_buyTime)
        print('总成功率: %.2f%%' % total_success_rate)

    print("%s,%s,%s,%.2f,%d,%d,%.2f%%,%d,%d,%d,%d,%d,%d,%.4f,%.4f" % (coin, '2021-05-2022-04', '高成功率类型-high差值', total_profit, total_buyTime, total_successTime,
        total_success_rate, rollContinueTargetTime, rollContinueLowTime, lastRollContinueLowTime, rollContinueInvalidCount,
        rollContinueRecoverCount, emaInitContinueTime, sellPricePercent, closePricePercent))


