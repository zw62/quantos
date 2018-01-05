
# coding: utf-8

# In[1]:


from jaqs.data.dataapi import DataApi


# In[2]:


api = DataApi(addr="tcp://192.168.1.117:8910") # 根据本地实际情况修改
api.login("25","25")


# In[3]:


symbol = 'rb1805.SHF'
fields = 'open,high,low,last,volume'

# 获取实时行情
df, msg = api.quote(symbol=symbol, fields=fields)
print(df)
print(msg)


# In[14]:


df, msg = api.daily(
                symbol="rb1805.SHF", 
                start_date=20171228,
                end_date=20171228, 
                fields="", 
                adjust_mode="post")
print(df)


# In[13]:


df,msg = api.bar(
            symbol="rb1805.SHF", 
            trade_date=20171228, 
            freq="30M",
            start_time=90000,
            end_time=160000,
            fields="")
print(df)


# In[7]:


df,msg = api.bar(
            symbol="rb1805.SHF", 
            trade_date=20171228, 
            freq="5M",
            start_time=90000,
            end_time=160000,
            fields="")
print(df)


# In[ ]:


df,msg = api.bar_quote(
                    symbol="000001.SH,cu1709.SHF",  
                    start_time = 95600, 
                    end_time=135600, 
                    trade_date=20170823, 
                    freq= "5M",
                    fields="open,high,low,last,volume")


# In[7]:


def on_bar(k,v):
    print v['symbol'] #//标的代码
    print v['last'] #// 最新成交价
    print v['time'] #// 最新成交时间

subs_list,msg = api.subscribe("000001.SH, cu1709.SHF",func=on_bar,fields="symbol,last,time,volume")


# In[8]:


subs_list


# In[9]:


df, msg = api.quote(
                symbol="000001.SH, cu1709.SHF", 
                fields="open,high,low,last,volume")


# In[10]:


df


# In[21]:


df, msg = api.query(
                view="lb.secDailyIndicator",
                fields='pb,net_assets,ncf,price_level',
                filter='symbol=rb.SHF&start_date=20171229&end_date=20170701')


# In[10]:


print(msg)


# In[11]:


df, msg = api.query(view="jz.instrumentInfo", 
                 fields="list_date,delist_date,symbol,market", 
                 filter="inst_type=1&trade_date=20171219")


# In[13]:


print(df)


# In[13]:


df, msg = api.query(
                view="jz.secTradeCal",
                fields="date,istradeday,isweekday,isholiday",
                filter="start_date=20171229&end_date=20180102",
                data_format='pandas')


# In[14]:


print(df)

