
# coding: utf-8

# In[ ]:


我们使用JAQS的股票Alpha策略框架AlphaStrategy、回测框架AlphaBacktestInstance实现。

框架允许用户任意指定投资范围内每只股票的权重，同时对于等权重、市值权重等常用情况，JAQS已经内置了相应函数，用户无需自己实现。

我们需要设置起止时间、初始资金等回测配置backtest_props，建立策略对象AlphaStrategy，回测实例对象AlphaBacktestInstance等。
0此外还需要建立运行上下文context，用于放置一些全局变量。

backtest_props = {# start and end date of back-test
                  "start_date": dv.start_date,
                  "end_date": dv.end_date,
                  # re-balance period length
                  "period": "month",
                  # benchmark and universe
                  "benchmark": dv.benchmark,
                  "universe": dv.universe,
                  # Amount of money at the start of back-test
                  "init_balance": 1e8}

# This is our strategy
strategy = AlphaStrategy(pc_method='market_value_weight')

# BacktestInstance is in charge of running the back-test
bt = AlphaBacktestInstance()

# Public variables are stored in context. We can also store anything in it
context = model.Context(dataview=dv, instance=bt, strategy=strategy, trade_api=trade_api, pm=pm)

准备好这些对象后，即可运行回测并储存结果：

bt.init_from_config(backtest_props)
bt.run_alpha()

# After finishing back-test, we save trade results into a folder
bt.save_results(folder_path=backtest_result_folder)

回测过程中会实时输出回测进度及资金情况，如：

AlphaStrategy Initialized.

=======new day 20170103
Before 20170103 re-balance: available cash all = 1.0000e+08

=======new day 20170203
Before 20170203 re-balance: available cash all = 1.0054e+08

回测完成后，会有如下提示：

Backtest done. 240 days, 5.27e+02 trades in total.
Backtest results has been successfully saved to:
'backtest_result_folder'

即回测的结果（交易记录）和回测相关配置已成功存储在backtest_result_folder内。用户可自行查看，也可使用我们提供的分析工具进行分析，见下一节。


# In[ ]:


一、策略描述

双均线穿越策略分为两步：

    首先，确定交易标的，根据历史价格数据计算快速均线和慢速均线。在本文的回测模式中，数据周期为1天。
    当快线均值上穿慢线均值时，若此时没有持仓，则买入股票；反之当快线均值下穿慢线均值时，若此时有股票持仓，则卖出所有股票。

二、策略实现

首先向大家介绍一下事件驱动策略框架的组成部分。该框架由类DoubleMaStrategy()实现，完成了“数据采集-信号生成-发单”的整个交易逻辑。

class DoubleMaStrategy(EventDrivenStrategy):
    """"""
    def __init__(self):
        super(DoubleMaStrategy, self).__init__()
        pass

    def init_from_config(self, props):
        super(DoubleMaStrategy, self).init_from_config(props)
        pass

    def buy(self, quote, size=1):
        pass

    def sell(self, quote, size=1):
        pass
    
    def on_tick(self, quote):
        pass

    def on_bar(self, quote_dic):
        pass

    def on_trade(self, ind):
        pass

其中，

    init_from_config()负责通过props接收策略所需参数，进行策略初始化；
    buy()/sell()负责发单；
    on_tick()和on_bar()是框架核心，策略的逻辑都在其中实现，区别在于on_tick()接收单个quote变量，而on_bar()接收多个quote组成的dictionary。
    此外on_tick()是在tick级回测和实盘/仿真交易中使用，而on_bar()是在bar回测中使用；
    on_trade()负责监督发单成交情况。

1. 参数初始化

首先在函数__init__()中初始化策略所需变量

def __init__(self):
    super(DoubleMaStrategy, self).__init__()

    # 标的
    self.symbol = ''

    # 快线和慢线周期
    self.fast_ma_len = 0
    self.slow_ma_len = 0
    
    # 记录当前已经过的天数
    self.window_count = 0
    self.window = 0

    # 固定长度的价格序列
    self.price_arr = None

    # 快线和慢线均值
    self.fast_ma = 0
    self.slow_ma = 0

    # 当前仓位
    self.pos = 0

    # 下单量乘数
    self.buy_size_unit = 1
    self.output = True

该策略的关键参数有三个，交易标的（symbol），快线周期（fast_ma_len）和慢线周期（slow_ma_len），通过props字典传入。

def init_from_config(self, props):
    """
    将props中的用户设置读入
    """
    super(DoubleMaStrategy, self).init_from_config(props)
    # 标的
    self.symbol = props.get('symbol')

    # 初始资金
    self.init_balance = props.get('init_balance')

    # 快线和慢线均值
    self.fast_ma_len = props.get('fast_ma_length')
    self.slow_ma_len = props.get('slow_ma_length')
    self.window = self.slow_ma_len + 1

    # 固定长度的价格序列
    self.price_arr = np.zeros(self.window)

2. 逻辑实现

策略的日级回测在on_bar()函数中完成。在回测中，每天会有一个quote传入，主要包括open, close, high和low。下面我们以回测为例。 第一步：根据历史价格数据计算快速均线和慢速均线。 每当一个quote传入，我们计算当前的midprice并更新价格序列。

if isinstance(quote, Quote):
    # 如果是Quote类型，mid为bidprice和askprice的均值
    bid, ask = quote.bidprice1, quote.askprice1
    if bid > 0 and ask > 0:
        mid = (quote.bidprice1 + quote.askprice1) / 2.0
    else:
        # 如果当前价格达到涨停板或跌停板，系统不交易
        return
else:
    # 如果是Bar类型，mid为Bar的close
    mid = quote.close

# 将price_arr序列中的第一个值删除，并将当前mid放入序列末尾
self.price_arr[0: self.window - 1] = self.price_arr[1: self.window]
self.price_arr[-1] = mid

接着计算快速均线和慢速均线，

self.fast_ma = np.mean(self.price_arr[-self.fast_ma_len:])
self.slow_ma = np.mean(self.price_arr[-self.slow_ma_len:])

第二步：当快线向上穿越慢线且当前没有持仓，则买入100股；当快线向下穿越慢线且当前有持仓，则平仓。

if self.fast_ma > self.slow_ma:
    if self.pos == 0:
        self.buy(quote, 100)

elif self.fast_ma < self.slow_ma:
    if self.pos > 0:
        self.sell(quote, self.pos)

第三步：交易完成后，会触发on_trade()函数，通过self.ctx.pm.get_pos()函数的到最新仓位并更新self.pos

def on_trade(self, ind):
    print("\nStrategy on trade: ")
    print(ind)
    self.pos = self.ctx.pm.get_pos(self.symbol)

三、回测启动

策略启动在run_strategy()函数中完成。

def run_strategy():
    if is_backtest:
        """
        回测模式
        """
        props = {"symbol": '600519.SH',
                 "start_date": 20170101,
                 "end_date": 20171104,
                 "fast_ma_length": 5,
                 "slow_ma_length": 15,
                 "bar_type": "1d",  # '1d'
                 "init_balance": 50000}

        tapi = BacktestTradeApi()
        ins = EventBacktestInstance()
        
    else:
        """
        实盘/仿真模式
        """
        props = {'symbol': '600519.SH',
                 "fast_ma_length": 5,
                 "slow_ma_length": 15,
                 'strategy.no': 1062}
        tapi = RealTimeTradeApi(trade_config)
        ins = EventLiveTradeInstance()


# In[ ]:




from __future__ import print_function, division, unicode_literals, absolute_import

import time

import numpy as np

from jaqs.data import RemoteDataService
from jaqs.data.basic import Bar, Quote
from jaqs.trade import (model, EventLiveTradeInstance, EventBacktestInstance, RealTimeTradeApi,
                        EventDrivenStrategy, BacktestTradeApi, PortfolioManager, common)
import jaqs.trade.analyze as ana
import jaqs.util as jutil

data_config = {
  "remote.data.address": "tcp://data.tushare.org:8910",
  "remote.data.username": "YourTelephone",
  "remote.data.password": "YourToken"
}
trade_config = {
  "remote.trade.address": "tcp://gw.quantos.org:8901",
  "remote.trade.username": "YourTelephone",
  "remote.trade.password": "YourToken"
}

result_dir_path = '../../output/double_ma'
is_backtest = True


class DoubleMaStrategy(EventDrivenStrategy):
    """"""
    def __init__(self):
        super(DoubleMaStrategy, self).__init__()

        # 标的
        self.symbol = ''

        # 快线和慢线周期
        self.fast_ma_len = 0
        self.slow_ma_len = 0
        
        # 记录当前已经过的天数
        self.window_count = 0
        self.window = 0

        # 快线和慢线均值
        self.fast_ma = 0
        self.slow_ma = 0
        
        # 固定长度的价格序列
        self.price_arr = None

        # 当前仓位
        self.pos = 0

        # 下单量乘数
        self.buy_size_unit = 1
        self.output = True
    
    def init_from_config(self, props):
        """
        将props中的用户设置读入
        """
        super(DoubleMaStrategy, self).init_from_config(props)
        # 标的
        self.symbol = props.get('symbol')

        # 初始资金
        self.init_balance = props.get('init_balance')

        # 快线和慢线均值
        self.fast_ma_len = props.get('fast_ma_length')
        self.slow_ma_len = props.get('slow_ma_length')
        self.window = self.slow_ma_len + 1
        
        # 固定长度的价格序列
        self.price_arr = np.zeros(self.window)

    def buy(self, quote, size=1):
        """
        这里传入的'quote'可以是:
            - Quote类型 (在实盘/仿真交易和tick级回测中，为tick数据)
            - Bar类型 (在bar回测中，为分钟或日数据)
        我们通过isinsance()函数判断quote是Quote类型还是Bar类型
        """
        if isinstance(quote, Quote):
            # 如果是Quote类型，ref_price为bidprice和askprice的均值
            ref_price = (quote.bidprice1 + quote.askprice1) / 2.0
        else:
            # 否则为bar类型，ref_price为bar的收盘价
            ref_price = quote.close
            
        task_id, msg = self.ctx.trade_api.place_order(quote.symbol, common.ORDER_ACTION.BUY, ref_price, self.buy_size_unit * size)

        if (task_id is None) or (task_id == 0):
            print("place_order FAILED! msg = {}".format(msg))
    
    def sell(self, quote, size=1):
        if isinstance(quote, Quote):
            ref_price = (quote.bidprice1 + quote.askprice1) / 2.0
        else:
            ref_price = quote.close
    
        task_id, msg = self.ctx.trade_api.place_order(quote.symbol, common.ORDER_ACTION.SHORT, ref_price, self.buy_size_unit * size)

        if (task_id is None) or (task_id == 0):
            print("place_order FAILED! msg = {}".format(msg))
    
    """
    'on_tick' 接收单个quote变量，而'on_bar'接收多个quote组成的dictionary
    'on_tick' 是在tick级回测和实盘/仿真交易中使用，而'on_bar'是在bar回测中使用
    """
    def on_tick(self, quote):
        pass

    def on_bar(self, quote_dic):
        """
        这里传入的'quote'可以是:
            - Quote类型 (在实盘/仿真交易和tick级回测中，为tick数据)
            - Bar类型 (在bar回测中，为分钟或日数据)
        我们通过isinsance()函数判断quote是Quote类型还是Bar类型
        """
        quote = quote_dic.get(self.symbol)
        if isinstance(quote, Quote):
            # 如果是Quote类型，mid为bidprice和askprice的均值
            bid, ask = quote.bidprice1, quote.askprice1
            if bid > 0 and ask > 0:
                mid = (quote.bidprice1 + quote.askprice1) / 2.0
            else:
                # 如果当前价格达到涨停板或跌停板，系统不交易
                return
        else:
            # 如果是Bar类型，mid为Bar的close
            mid = quote.close

        # 将price_arr序列中的第一个值删除，并将当前mid放入序列末尾
        self.price_arr[0: self.window - 1] = self.price_arr[1: self.window]
        self.price_arr[-1] = mid
        self.window_count += 1

        if self.window_count <= self.window:
            return

        # 计算当前的快线/慢线均值
        self.fast_ma = np.mean(self.price_arr[-self.fast_ma_len:])
        self.slow_ma = np.mean(self.price_arr[-self.slow_ma_len:])

        print(quote)
        print("Fast MA = {:.2f}     Slow MA = {:.2f}".format(self.fast_ma, self.slow_ma))

        # 交易逻辑：当快线向上穿越慢线且当前没有持仓，则买入100股；当快线向下穿越慢线且当前有持仓，则平仓
        if self.fast_ma > self.slow_ma:
            if self.pos == 0:
                self.buy(quote, 100)

        elif self.fast_ma < self.slow_ma:
            if self.pos > 0:
                self.sell(quote, self.pos)

    def on_trade(self, ind):
        """
        交易完成后通过self.ctx.pm.get_pos得到最新仓位并更新self.pos
        """
        print("\nStrategy on trade: ")
        print(ind)
        self.pos = self.ctx.pm.get_pos(self.symbol)


def run_strategy():
    if is_backtest:
        """
        回测模式
        """
        props = {"symbol": '600519.SH',
                 "start_date": 20170101,
                 "end_date": 20171104,
                 "fast_ma_length": 5,
                 "slow_ma_length": 15,
                 "bar_type": "1d",  # '1d'
                 "init_balance": 50000}

        tapi = BacktestTradeApi()
        ins = EventBacktestInstance()
        
    else:
        """
        实盘/仿真模式
        """
        props = {'symbol': '600519.SH',
                 "fast_ma_length": 5,
                 "slow_ma_length": 15,
                 'strategy.no': 1062}
        tapi = RealTimeTradeApi(trade_config)
        ins = EventLiveTradeInstance()

    props.update(data_config)
    props.update(trade_config)
    
    ds = RemoteDataService()
    strat = DoubleMaStrategy()
    pm = PortfolioManager()
    
    context = model.Context(data_api=ds, trade_api=tapi, instance=ins,
                            strategy=strat, pm=pm)
    
    ins.init_from_config(props)
    if not is_backtest:
        ds.subscribe(props['symbol'])

    ins.run()
    if not is_backtest:
        time.sleep(9999)
    ins.save_results(folder_path=result_dir_path)


def analyze():
    ta = ana.EventAnalyzer()
    
    ds = RemoteDataService()
    ds.init_from_config(data_config)
    
    ta.initialize(data_server_=ds, file_folder=result_dir_path)
    
    ta.do_analyze(result_dir=result_dir_path, selected_sec=[])


if __name__ == "__main__":
    run_strategy()
analyze()


# In[ ]:




from __future__ import print_function
from __future__ import absolute_import
import numpy as np
import statsmodels.api as sm

from jaqs.trade import EventDrivenStrategy
from jaqs.trade import common, model

from jaqs.data import RemoteDataService
from jaqs.trade import EventBacktestInstance
from jaqs.trade import BacktestTradeApi
from jaqs.trade import PortfolioManager
import jaqs.trade.analyze as ana
import jaqs.util as jutil

from config_path import DATA_CONFIG_PATH, TRADE_CONFIG_PATH
data_config = jutil.read_json(DATA_CONFIG_PATH)
trade_config = jutil.read_json(TRADE_CONFIG_PATH)

result_dir_path = '../../output/sector_rolling'


class SectorRolling(EventDrivenStrategy):
    def __init__(self):
        super(SectorRolling, self).__init__()
        self.symbol = ''
        self.benchmark_symbol = ''
        self.quotelist = ''
        self.startdate = ''
        self.bufferSize = 0
        self.rollingWindow = 0
        self.bufferCount = 0
        self.bufferCount2 = 0
        self.closeArray = {}
        self.activeReturnArray = {}
        self.std = ''
        self.balance = ''
        self.multiplier = 1.0
        self.std_multiplier = 0.0
    
    def init_from_config(self, props):
        super(SectorRolling, self).init_from_config(props)
        self.symbol = props.get('symbol').split(',')
        self.init_balance = props.get('init_balance')
        self.startdate = props.get('start_date')
        self.std_multiplier = props.get('std multiplier')
        self.bufferSize = props.get('n')
        self.rollingWindow = props.get('m')
        self.benchmark_symbol = self.symbol[-1]
        self.balance = self.init_balance
        
        for s in self.symbol:
            self.closeArray[s] = np.zeros(self.rollingWindow)
            self.activeReturnArray[s] = np.zeros(self.bufferSize)
        
        self.output = True
    
    def on_cycle(self):
        pass
    
    def on_tick(self, quote):
        pass

    def buy(self, quote, price, size):
        self.ctx.trade_api.place_order(quote.symbol, 'Buy', price, size)

    def sell(self, quote, price, size):
        self.ctx.trade_api.place_order(quote.symbol, 'Sell', price, size)

    def on_bar(self, quote):
        # 1 is for stock, 2 is for convertible bond
        self.bufferCount += 1
        self.quotelist = []
    
        for s in self.symbol:
            self.quotelist.append(quote.get(s))
    
        for stock in self.quotelist:
            self.closeArray[stock.symbol][0:self.rollingWindow - 1] = self.closeArray[stock.symbol][1:self.rollingWindow]
            self.closeArray[stock.symbol][-1] = stock.close
    
        if self.bufferCount < self.rollingWindow:
            return
    
        elif self.bufferCount >= self.rollingWindow:
            self.bufferCount2 += 1
            # calculate active return for each stock
            benchmarkReturn = np.log(self.closeArray[self.benchmark_symbol][-1]) - np.log(self.closeArray[self.benchmark_symbol][0])
            for stock in self.quotelist:
                stockReturn = np.log(self.closeArray[stock.symbol][-1]) - np.log(self.closeArray[stock.symbol][0])
                activeReturn = stockReturn - benchmarkReturn
                self.activeReturnArray[stock.symbol][0:self.bufferSize - 1] = self.activeReturnArray[stock.symbol][1:self.bufferSize]
                self.activeReturnArray[stock.symbol][-1] = activeReturn
        
            if self.bufferCount2 < self.bufferSize:
                return
        
            elif self.bufferCount2 == self.bufferSize:
                # if it's the first date of strategy, we will buy equal value stock in the universe
                stockvalue = self.balance/len(self.symbol)
                for stock in self.quotelist:
                    if stock.symbol != self.benchmark_symbol:
                        self.buy(stock, stock.close, np.floor(stockvalue/stock.close/self.multiplier))
                return
            else:
                stockholdings = self.ctx.pm.holding_securities
                noholdings = set(self.symbol) - stockholdings
                stockvalue = self.balance/len(noholdings)
            
                for stock in list(stockholdings):
                    curRet = self.activeReturnArray[stock][-1]
                    avgRet = np.mean(self.activeReturnArray[stock][:-1])
                    stdRet = np.std(self.activeReturnArray[stock][:-1])
                    if curRet >= avgRet + self.std_multiplier * stdRet:
                        curPosition = self.ctx.pm.positions[stock].current_size
                        stock_quote = quote.get(stock)
                        self.sell(stock_quote, stock_quote.close, curPosition)
            
                for stock in list(noholdings):
                    curRet = self.activeReturnArray[stock][-1]
                    avgRet = np.mean(self.activeReturnArray[stock][:-1])
                    stdRet = np.std(self.activeReturnArray[stock][:-1])
                    if curRet < avgRet - self.std_multiplier * stdRet:
                        stock_quote = quote.get(stock)
                        self.buy(stock_quote, stock_quote.close, np.floor(stockvalue/stock_quote.close/self.multiplier))

    def on_trade(self, ind):
        print("\nStrategy on trade: ")
        print(ind)
        self.pos = self.ctx.pm.get_pos(ind.symbol)
        print(self.ctx.pm.get_trade_stat(ind.symbol))

        if common.ORDER_ACTION.is_positive(ind.entrust_action):
            self.balance -= ind.fill_price * ind.fill_size * self.multiplier
        else:
            self.balance += ind.fill_price * ind.fill_size * self.multiplier

    def on_order_status(self, ind):
        if self.output:
            print("\nStrategy on order status: ")
            print(ind)
    
    def on_task_status(self, ind):
        if self.output:
            print("\nStrategy on task ind: ")
            print(ind)


def run_strategy():

    start_date = 20150501
    end_date = 20171030
    index = '399975.SZ'
    
    ds = RemoteDataService()
    ds.init_from_config(data_config)
    symbol_list = ds.get_index_comp(index, start_date, start_date)

    # add the benchmark index to the last position of symbol_list
    symbol_list.append(index)
    props = {"symbol": ','.join(symbol_list),
             "start_date": start_date,
             "end_date": end_date,
             "bar_type": "1d",
             "init_balance": 1e7,
             "std multiplier": 1.5,
             "m": 10,
             "n": 60,
             "commission_rate": 2E-4}
    props.update(data_config)
    props.update(trade_config)

    tapi = BacktestTradeApi()
    ins = EventBacktestInstance()

    strat = SectorRolling()
    pm = PortfolioManager()

    context = model.Context(data_api=ds, trade_api=tapi, instance=ins,
                            strategy=strat, pm=pm)

    ins.init_from_config(props)
    ins.run()
    ins.save_results(folder_path=result_dir_path)

    ta = ana.EventAnalyzer()

    ta.initialize(data_server_=ds, file_folder=result_dir_path)
    df_bench, _ = ds.daily(index, start_date=start_date, end_date=end_date)
    ta.data_benchmark = df_bench.set_index('trade_date').loc[:, ['close']]

    ta.do_analyze(result_dir=result_dir_path, selected_sec=props['symbol'].split(',')[:2])


if __name__ == "__main__":
run_strategy()

