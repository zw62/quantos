
# coding: utf-8

# In[8]:


from jaqs.data.dataservice import RemoteDataService
from jaqs.data.dataview import DataView


# In[28]:


data_config = {
    "remote.data.address": "tcp://data.tushare.org:8910",
    "remote.data.username": "18810695562",
    "remote.data.password": "eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MTMzMTU1MTE3MDEiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTg4MTA2OTU1NjIifQ.2qvBxyHzcIFfC4_5lP_MFkNwDGLYD2gwqxMLWMpOLw0"
}
trade_config = {
    "remote.trade.address": "tcp://192.168.1.117:8901",
    "remote.trade.username": "18",
    "remote.trade.password": "18"
}


# In[31]:


UNIVERSE = '000807.SH'


# In[36]:


dataview_props = {# Start and end date of back-test
                      'start_date': 20171228, 'end_date': 20171229,
                      # Investment universe and performance benchmark
                      'universe': UNIVERSE, 
                      # Data fields that we need
                      'fields': 'close',
                      # freq = 1 means we use daily data. Please do not change this.
                      'freq': 1}

# RemoteDataService communicates with a remote server to fetch data
ds = RemoteDataService()
# Use username and password in data_config to login
ds.init_from_config(data_config)

# DataView utilizes RemoteDataService to get various data and store them
dv = DataView()
dv.init_from_config(dataview_props, ds)
dv.prepare_data()


# In[35]:


type(dv)


# In[ ]:


props = {'start_date': 20150101, 'end_date': 20170901, 'universe': '000300.SH',
         'fields': ('open,high,low,close,vwap,volume,turnover,eps_basic,roe,sw2'
                    ),
         'freq': 1}
dv.init_from_config(props,ds)


# In[12]:


dv.prepare_data()

dv.save_dataview('save_folder')

