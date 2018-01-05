
# coding: utf-8

# In[15]:




from __future__ import absolute_import
from __future__ import print_function

import jaqs.trade.analyze as ana
import numpy as np
from jaqs.data import RemoteDataService
from jaqs.trade import BacktestTradeApi
from jaqs.trade import EventBacktestInstance
from jaqs.trade import EventDrivenStrategy
from jaqs.trade import PortfolioManager
from jaqs.trade import model

data_config = {
'remote.data.address'  : 'tcp://data.tushare.org:8910',
'remote.data.username' : '18810695562',
'remote.data.password' : 'eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MTMzMTU1MTE3MDEiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTg4MTA2OTU1NjIifQ.2qvBxyHzcIFfC4_5lP_MFkNwDGLYD2gwqxMLWMpOLw0'
}
trade_config = {
'remote.trade.address'  : 'tcp://gw.quantos.org:8901',
'remote.trade.username' : '18810695562',
'remote.trade.password' : 'eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MTMzMTU1MTE3MDEiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTg4MTA2OTU1NjIifQ.2qvBxyHzcIFfC4_5lP_MFkNwDGLYD2gwqxMLWMpOLw0'
}

result_dir_path = '../../output/double_ma_D'


# In[29]:


class DoubleMA(EventDrivenStrategy):
    def __init__(self):
        super(DoubleMA, self).__init__()
        self.symbol = ''
        self.quote = None
        self.bufferCount = 0
        self.bufferSize = 0
        self.high_list = []
        self.close_list = []
        self.low_list = []
        self.open_list = []
        self.k1 = 0.0
        self.k2 = 0.0
        self.pos = 0
        self.Upper = 0.0
        self.Lower = 0.0
        self.output = False
        
    def init_from_config(self, props):
        super(DoubleMA, self).init_from_config(props)
        self.symbol = props.get('symbol')
        self.init_balance = props.get('init_balance')
        self.bufferSize = props.get('buffersize')
        self.fastlen = props.get('fastlen')
        self.slowlen = props.get('slowlen')
        self.HHlen = props.get('HHlen')
        self.LLlen = props.get('LLlen')
        self.k1 = props.get('k1')                  #突破几倍atr入场
        self.k2 = props.get('k2')                 #方向变动几倍atr出场

        self.high_list = np.zeros(self.bufferSize)
        self.close_list = np.zeros(self.bufferSize)
        self.low_list = np.zeros(self.bufferSize)
        self.open_list = np.zeros(self.bufferSize)

        self.tick_size = props.get('tick_size', 1.0)

    def initialize(self):
        self.bufferCount += 1
        td = self.ctx.trade_date
        ds = self.ctx.data_api
        df, msg = ds.daily(symbol=self.symbol, start_date=td, end_date=td)

        self.open_list[0:self.bufferSize - 1] = self.open_list[1:self.bufferSize]
        self.open_list[-1] = df.open
        self.high_list[0:self.bufferSize - 1] = self.high_list[1:self.bufferSize]
        self.high_list[-1] = df.high
        self.close_list[0:self.bufferSize - 1] = self.close_list[1:self.bufferSize]
        self.close_list[-1] = df.close
        self.low_list[0:self.bufferSize - 1] = self.low_list[1:self.bufferSize]
        self.low_list[-1] = df.low

        HH = max(self.high_list[-self.HHlen:])
        HC = max(self.close_list[-self.HHlen:])
        LC = min(self.close_list[-self.LLlen:])
        LL = min(self.low_list[-self.LLlen:])

    def on_cycle(self):
        pass
    
    def on_tick(self, quote):
        pass

    def buy(self, quote, price, size):
        self.ctx.trade_api.place_order(quote.symbol, 'Buy', price, size)

    def sell(self, quote, price, size):
        self.ctx.trade_api.place_order(quote.symbol, 'Sell', price, size)

    def on_bar(self, quote):
        if self.bufferCount <= self.bufferSize:
            return
        self.quote = quote.get(self.symbol)
        if self.quote.close < 1e-3:
            return

        self.fast_ma = np.mean(self.close_list[-self.fastlen:])
        self.slow_ma = np.mean(self.close_list[-self.slowlen:])
        print(quote)
        print("Fast MA = {:.2f}     Slow MA = {:.2f}".format(self.fast_ma, self.slow_ma))

        # 交易逻辑：当快线向上穿越慢线且当前没有持仓，则买入100股；当快线向下穿越慢线且当前有持仓，则平仓

        if self.quote.time > 90100 and self.quote.time <= 142800:
            if self.pos == 0:
                if self.fast_ma > self.slow_ma:
                    self.buy(self.quote, self.quote.close, 1)
                elif self.fast_ma < self.slow_ma:
                    self.sell(self.quote, self.quote.close, 1)

            elif self.pos < 0:
                if self.fast_ma > self.slow_ma:
                    self.buy(self.quote, self.quote.close, 2)

            else:
                if self.fast_ma < self.slow_ma:
                    self.sell(self.quote, self.quote.close, 2)
        elif self.quote.time > 142800:
            pass
            # self.cancel_all_orders()
            # self.liquidate(self.quote, 3, tick_size=self.tick_size, pos=self.pos)
    
    def on_trade(self, ind):
        print("\nStrategy on trade: ")
        print(ind)
        self.pos = self.ctx.pm.get_pos(ind.symbol)
        print(self.ctx.pm.get_trade_stat(ind.symbol))

    def on_order_status(self, ind):
        if self.output:
            print("\nStrategy on order status: ")
            print(ind)
        
    def on_task_rsp(self, rsp):
        if self.output:
            print("\nStrategy on task rsp: ")
            print(rsp)

    def on_order_rsp(self, rsp):
        if self.output:
            print("\nStrategy on order rsp: ")
            print(rsp)
    
    def on_task_status(self, ind):
        if self.output:
            print("\nStrategy on task ind: ")
            print(ind)


# In[32]:


props = {
    "symbol": "rb1801.SHF",
    "start_date": 20170901,
    "end_date": 20171102,
    "buffersize": 25,
    "fastlen": 3,
    "slowlen": 25,
    "HHlen": 3,
    "LLlen": 3,
    "k1": 0.2,
    "k2": 0.2,
    "bar_type": "15M",
    "init_balance": 3e4,
    "commission_rate": 0.0
}
props.update(data_config)
props.update(trade_config)


# In[7]:


def run_strategy():
    tapi = BacktestTradeApi()
    ins = EventBacktestInstance()

    ds = RemoteDataService()
    strat = DoubleMA()
    pm = PortfolioManager()

    context = model.Context(data_api=ds, trade_api=tapi, instance=ins,
                            strategy=strat, pm=pm)

    ins.init_from_config(props)
    ins.run()
    ins.save_results(folder_path=result_dir_path)


# In[8]:


def analyze():
    ta = ana.EventAnalyzer()
    
    ds = RemoteDataService()
    ds.init_from_config(data_config)
    
    ta.initialize(data_server_=ds, file_folder=result_dir_path)
    
    ta.do_analyze(result_dir=result_dir_path, selected_sec=props['symbol'].split(','))


# In[33]:


if __name__ == "__main__":
    run_strategy()
    analyze()


