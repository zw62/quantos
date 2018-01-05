
# coding: utf-8

# In[1]:


from jaqs.data.dataapi import DataApi

api = DataApi(addr='tcp://data.tushare.org:8910')
api.login('18810695562','eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MTMzMTU1MTE3MDEiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTg4MTA2OTU1NjIifQ.2qvBxyHzcIFfC4_5lP_MFkNwDGLYD2gwqxMLWMpOLw0')

df, msg = api.query(
                view="jz.instrumentInfo",
                fields="status,list_date, fullname_en, market",
                filter="inst_type=103&status=1&symbol=",
                data_format='pandas')


# In[13]:


set(df.market)

