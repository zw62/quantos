
# coding: utf-8

# In[2]:


import pandas as pd
import numpy as np


# In[3]:


from jaqs.data.dataapi import DataApi

api = DataApi(addr='tcp://data.tushare.org:8910')
api.login('18810695562','eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MTMzMTU1MTE3MDEiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTg4MTA2OTU1NjIifQ.2qvBxyHzcIFfC4_5lP_MFkNwDGLYD2gwqxMLWMpOLw0')


# In[4]:


df,msg = api.quote("000001.SH, cu1802.SHF", fields="open,high,low,last,volume")


# In[5]:


df


# In[5]:


df1, msg1 = api.query(
                view="jz.secTradeCal", 
                fields="date,market", 
                filter="start_date=20170901&end_date=20171101", 
                data_format='pandas')


# In[6]:


df1

