from django.contrib.auth.decorators import login_required

from django.urls import reverse
from django.shortcuts import render,redirect
from django.conf import settings

import sys,os
import pandas as pd
import datetime,time

from semutils.db_access import Access_SQL_DB, Access_SQL_Source
from sqlalchemy import select,Table, Column

from .forms import SectorIndustryForm

# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader

EnterLong = 0.6
EnterShort = 0.4
MySQL_Server = os.environ.get('MySQL_Server')

def wavg(group, avg_name, weight_name):
    """
    In rare instance, we may not have weights, so just return the mean. Customize this if your business case
    should return otherwise.
    """
    d = group[avg_name]
    w = group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return d.mean()

@login_required
def search_redirect(request):
    if request.method == 'GET':
        ticker = request.GET.get('ticker','')        
        return redirect(reverse('equities_ticker',args={ticker}))

@login_required
def under_development(request):
    if request.method == 'GET':
        return render(request, 'site_app/under_development.html')

@login_required
def equities_sector_industry_signals(request):
    # connect to sql and tables
    sql_source = Access_SQL_Source(MySQL_Server)
    sql = Access_SQL_DB(MySQL_Server,db='equity_models')
    signals = Table('signals_daily_2017_07_01', sql.META, autoload=True)

    # download sector data
    today = datetime.datetime.now() 
    signal_data_columns = ['data_date','ticker','market_cap','zacks_x_sector_desc','zacks_m_ind_desc','zacks_m_ind_code','SignalConfidence']

    if request.method=='POST':
        requested_sector_code = int(request.POST['sectors'])
        requested_benchmark = str(request.POST['benchmark']).upper()
    else:
        requested_sector_code = 10 # start with Computer and technology
        requested_benchmark = 'XLK' # start with Computer and technology

    query = select([signals.c[x] for x in signal_data_columns]).where(((signals.c.data_date >= today-datetime.timedelta(days=200)) & 
                                                                       (signals.c.data_date <= today)) &
                                                                      (signals.c.zacks_x_sector_code==requested_sector_code))

    signal_data = pd.read_sql_query(query, sql.ENGINE, index_col=None, parse_dates=['data_date']).sort_index()
    signal_data.sort_values('data_date',inplace=True)

    # filter data for industries
    if request.method=='POST':
        requested_industry_codes = request.POST.getlist('industries')
        if not isinstance(requested_industry_codes,list):
            requested_industry_codes = [requested_industry_codes]
        requested_industry_codes = [int(x) for x in requested_industry_codes]

        if signal_data.zacks_m_ind_code.astype(int).isin(requested_industry_codes).any(): # check to see if sector has changed
            signal_data = signal_data[signal_data.zacks_m_ind_code.astype(int).isin(requested_industry_codes)]
        else:
            requested_industry_codes = list(signal_data.zacks_m_ind_code.dropna().astype(int).unique())            
    else:
        requested_industry_codes = list(signal_data.zacks_m_ind_code.dropna().astype(int).unique())

    # download benchmark data
    sm = sql_source.get_sec_master()
    smf = sm[sm.ticker==requested_benchmark]
    if len(smf) !=1 :
        requested_benchmark = 'SPY' 
        benchmark_m_ticker='SPY'
    else:
        benchmark_m_ticker=smf.iloc[0].m_ticker

    benchmark_data = sql_source.get_source_eod_data(m_ticker = benchmark_m_ticker,vendor='QM')

    # set up form
    sector_industry_form = SectorIndustryForm(sector_selection=requested_sector_code,industry_selection=requested_industry_codes,
                                              benchmark_selection = requested_benchmark )


    # find current sector name
    current_sector_name = signal_data.zacks_x_sector_desc.unique()[0]
                                 
    # filter data for market cap
    #signal_data = signal_data[signal_data.market_cap >=300e6]

    # create consolidated signal for chart
    chart_data = signal_data.groupby('data_date').apply(wavg,'SignalConfidence','market_cap')


    # format signal for javascript
    chart_data.sort_index(inplace=True)
    chart_data = chart_data.to_frame()
    chart_data.reset_index(drop=False,inplace=True)
    chart_data.columns = ['date','signal']
    chart_data['benchmark'] = chart_data['date'].map(benchmark_data['adj_close'])
    chart_data['benchmark'] = (chart_data['benchmark'].pct_change().fillna(0) + 1).cumprod()-1
    chart_data['date'] = chart_data['date'].apply(lambda x: time.mktime(x.timetuple()))
    chart_data_signal = chart_data[['date','signal']].values.tolist()
    chart_data_benchmark = chart_data[['date','benchmark']].values.tolist()

    # create table data
    table_data = signal_data.copy()
    table_data['delta_1wk'] = signal_data.groupby('ticker').SignalConfidence.diff(5).round(2)
    table_data['delta_2wk'] = signal_data.groupby('ticker').SignalConfidence.diff(10).round(2)
    table_data['delta_4wk'] = signal_data.groupby('ticker').SignalConfidence.diff(20).round(2)
    table_data['SignalConfidence'] = table_data.SignalConfidence.round(2)

    table_data = table_data[table_data.data_date == table_data.data_date.max()]
    table_data.sort_values('market_cap',ascending=False,inplace=True)

    table_data = table_data[['ticker','zacks_x_sector_desc','zacks_m_ind_desc','SignalConfidence','delta_1wk','delta_2wk','delta_4wk']]
    table_data = table_data.to_dict(orient='records')

    context = {'chart_data_signal':chart_data_signal,
               'chart_data_benchmark':chart_data_benchmark,
               'table_data':table_data,
               'current_sector':current_sector_name,
               'sector_industry_selector':sector_industry_form}
    sql.close_connection()
    sql_source.close_connection()

    return render(request, 'site_app/equities_sector_industry_signals.html', context)

@login_required
def equities_latest_signals(request):
    sql = Access_SQL_DB(MySQL_Server,db='equity_models')

    signals = Table('signals_daily_2017_07_01', sql.META, autoload=True)

    today = datetime.datetime.now() 
    signal_data_columns = ['data_date','ticker','close','market_cap','zacks_x_sector_desc','zacks_m_ind_desc','SignalConfidence']

    query = select([signals.c[x] for x in signal_data_columns]).where(((signals.c.data_date >= today-datetime.timedelta(days=7)) & 
                                                                       (signals.c.data_date <= today))) 


    signal_data = pd.read_sql_query(query, sql.ENGINE, index_col=None, parse_dates=['data_date']).sort_index()

    signal_data['SignalDirection'] = signal_data.SignalConfidence.apply(lambda x: 'Long' if x >= EnterLong else 'Short' if x <= EnterShort else 'Neutral')

    signal_data = signal_data[signal_data.SignalDirection.isin(['Long','Short'])]

    signal_data.sort_values('data_date', ascending=False, inplace=True)

    signal_data = signal_data.to_dict(orient='records')

    context = {'signal_data':signal_data}
    sql.close_connection()

    return render(request, 'site_app/equities_latest_signals.html', context)

@login_required
def equities_ticker(request,ticker):
    ticker = ticker.upper()
    signal_data_columns = ['data_date','market_cap','ticker','volume','zacks_x_sector_desc','zacks_m_ind_desc','close','adj_close','SignalConfidence']

    sql = Access_SQL_DB(MySQL_Server,db='equity_models')
    signals = Table('signals_daily_2017_07_01', sql.META, autoload=True)
    query = select([signals.c[x] for x in signal_data_columns]).where(signals.c.ticker ==ticker) 

    st_df = pd.read_sql_query(query, sql.ENGINE, index_col=None, parse_dates=['data_date']).sort_index()

    ## Check if stacked signal data exists
    if (not(len(st_df))):
        template = loader.get_template('site_app/ticker_not_found.html')
        #context = RequestContext(request,{'ticker':ticker})
        context = {'ticker':ticker}
        return HttpResponse(template.render(context))

    st_df['SignalDirection'] = st_df.SignalConfidence.apply(lambda x: None if pd.isnull(x) else 'Long' if x >= EnterLong else 'Short' if x <= EnterShort else 'Neutral')
    st_df.zacks_m_ind_desc = st_df.zacks_m_ind_desc.astype(str).map(lambda x: x.title())

    ## add some info to st_df
    st_df['volume_sma30'] = pd.rolling_mean(st_df.volume,30)
    st_df['daily_average_trading_value'] = st_df['volume_sma30'] * st_df.close

    ## sort and reset index 
    st_df.sort_values('data_date', ascending=True, inplace=True)
    st_df.set_index('data_date',inplace = True) 

    ## latest signal 
    st_df_f = st_df[st_df.SignalDirection.notnull()]
    latest_signal = st_df_f.SignalDirection.iloc[-1]
    latest_signal_date = st_df_f.index[-1].strftime('%m/%d/%Y')

    st_df['data_date'] = st_df.index
    st_df.reset_index(inplace = True,drop=True)

    #convert to JSON for exchange with JS
    chart_data = st_df.to_json(orient='records', date_format='iso') 

    
    context = {'ticker':ticker,
               'latest_bar':st_df.iloc[-1].to_dict(),
               'chart_data':chart_data,
               'latest_signal':latest_signal,
               'latest_signal_date':latest_signal_date}

    sql.close_connection()
    return render(request, 'site_app/equities_ticker.html', context)


@login_required
def ticker_not_found(request):
    template = loader.get_template('site_app/ticker_not_found.html')
    context = RequestContext(request)

    return HttpResponse(template.render(context))

@login_required
def insider_transactions_latest_filings(request):
    # set up data base and tables
    sql = Access_SQL_Source(MySQL_Server)
    formsT = Table('sec_forms_ownership_source', sql.META, autoload=True)

    # download forms
    today = datetime.datetime.now() 
    forms = pd.read_sql(formsT.select().where(formsT.c.FilingDate > today - datetime.timedelta(days=7)),sql.ENGINE)

    # download securities master and merge
    sm = sql.get_sec_master() 
    forms = forms.merge(sm,left_on='IssuerCIK',right_on='comp_cik',how='left')

    #signal_data['AcceptedDate'] = pd.to_datetime(signal_data['AcceptedDate'])

    forms.sort('AcceptedDate', ascending=False, inplace=True)

    cols = ['ticker','CompanyName','zacks_x_sector_desc','zacks_x_ind_desc','URL','AcceptedDate','FilerName',
                           'InsiderTitle','Director','TransType',
                           'DollarValue','SignalDirection','SignalConfidence','SignalGenerationDate']

    forms = forms[cols]

    forms = forms.to_dict(orient='records')

    context = {'forms':forms}

    return render(request, 'site_app/insider_transactions_latest_filings.html', context)

@login_required
def insider_transactions_ticker(request,ticker):
    ticker = ticker.upper()
    ## Load insider transactions data
    mongo_conn = mongo.AccessMongo()
    a,b,processed_forms_with_features = mongo_conn.connect_transactions_db()

    ticker_data = pd.DataFrame(list(processed_forms_with_features.find({'Ticker':ticker})))
    if (not(len(ticker_data))):
        template = loader.get_template('site_app/ticker_not_found.html')
        context = RequestContext(request,{'ticker':ticker})
        return HttpResponse(template.render(context))


    ticker_data.sort('AcceptedDate', ascending=False, inplace=True)

    ticker_data_columns = ['CompanyName','zacks_x_sector_desc','zacks_x_ind_desc','URL','AcceptedDate','FilerName','InsiderTitle','Director','TenPercentOwner','TransType',
                           'DollarValue','SignalDirection','SignalConfidence','SignalGenerationDate',
                           'F_EOD_1q_abs_return','F_EOD_2q_abs_return']

    ticker_data = ticker_data[ticker_data_columns]
    ticker_data['AcceptedDate'] = pd.to_datetime(ticker_data['AcceptedDate'])
    ticker_data['SignalGenerationDate'] = pd.to_datetime(ticker_data['SignalGenerationDate'])

    ## Load price data
    sql_conn = sql.Access_SQL_Data()

    price_db_columns = ['price_date','close','adj_close', 'adj_vol',
                        'market_cap','VolSMA30','high_52wk','low_52wk']

    price_db = sql_conn.get_qm_eod_data(ticker=ticker,start_date=datetime.datetime(2002,1,1),data_list=price_db_columns)

    if (not(len(price_db))):
        template = loader.get_template('site_app/ticker_not_found.html')
        context = RequestContext(request,{'ticker':ticker})
        return HttpResponse(template.render(context))

    #calculate returns for signals
    def calculate_return(st,days,price_db):
        i = price_db.index.searchsorted(st+datetime.timedelta(days=1))
        if (i==len(price_db)):
            return(0.0)
        end = price_db.adj_close.asof(st+datetime.timedelta(days=days))
        beg = price_db.ix[i,'adj_close']
        return((end/beg)-1)
    ticker_data['inv_1q_return'] = ticker_data.AcceptedDate.apply(lambda x: calculate_return(x,90,price_db))
    ticker_data['inv_2q_return'] = ticker_data.AcceptedDate.apply(lambda x: calculate_return(x,180,price_db))
    ticker_data.inv_1q_return = ticker_data.inv_1q_return.where(ticker_data.SignalDirection=='LONG',-ticker_data.inv_1q_return)
    ticker_data.inv_2q_return = ticker_data.inv_2q_return.where(ticker_data.SignalDirection=='LONG',-ticker_data.inv_2q_return)

    # change the index of price db so that it can work with the markers
    price_db['Index'] = range(0,len(price_db))
    price_db['Date'] = price_db.index
    price_db.set_index(['Index'],inplace=True)

    #convert to JSON for exchange with JS
    chart_data = price_db.to_json(orient='records', date_format='iso') 
    table_data = ticker_data.to_json(orient='records', date_format='iso')

    # build marker data
    it_data = ticker_data.to_dict(orient='records')
    graph_marker_data = [     {
                                "index": g_index, 
                                # "value": price_db['Adj Close'][g_index],
                                "tableIndex": t_index,
                                # "tableDateTime": t_date.value, #just for sorting the table
                                "SignalConfidence": it_data[t_index]['SignalConfidence'], 
                                "inv_1q_return": it_data[t_index]['inv_1q_return'], 
                                "inv_2q_return": it_data[t_index]['inv_2q_return'], 
                                "FilerName": it_data[t_index]['FilerName'],
                                "SignalDirection": it_data[t_index]['SignalDirection']
                              } 
                                for t_index, t_val in  enumerate(it_data)
                                    for g_index, g_val in enumerate(price_db['Date'])
                                        if ((g_val.date() == t_val['AcceptedDate'].date()) & pd.notnull(t_val['SignalConfidence']))
                            ] 
    template = loader.get_template('site_app/insider_transactions_ticker.html')
    l = price_db.index[-1]
    context = RequestContext(request,{'ticker':ticker,
                                      'CompanyName':ticker_data.loc[0,'CompanyName'],
                                      'zacks_sector':ticker_data.loc[0,'zacks_x_sector_desc'],
                                      'zacks_ind':ticker_data.loc[0,'zacks_x_ind_desc'],
                                      'price_db_latest_date':price_db.loc[l,'Date'].date(),
                                       'latest_bar':price_db.iloc[-1].to_dict(),
                                       'avg_trading_vol':price_db.loc[l,'close']*price_db.loc[l,'VolSMA30'],
                                      'chart_data':chart_data,
                                      'table_data':table_data,
                                      'graph_marker_data':graph_marker_data,
                                      'it_data':it_data,
                                      'price_db':price_db}) # may have to convert price db to dict
    return HttpResponse(template.render(context))


##### note: this is a slightly less verbose way of writing the above code:
#####           it replaces RequestContext and HttpResponse with a dict and render()
    # context = {'ticker':ticker,
    #           'company_name':ticker_data.ix[0,'bb_name'],
    #           'zacks_sector':ticker_data.ix[0,'zacks_x_sector_desc'],
    #           'zacks_industry':ticker_data.ix[0,'zacks_x_ind_desc'],
    #           'price_db_latest_date':price_db.index[-1],
    #           'latest_bar':price_db.ix[-1].to_dict(),
    #           'avg_trading_vol':price_db.ix[-1,'close']*price_db.ix[-1,'VolSMA30'],
    #           'chart_data':chart_data,
    #           'it_data':it_data,
    #           'price_db':price_db} # may have to convert price db to dict
    # return render(request, 'site_app/strategy1_ticker.html', context)


@login_required
def macro_signals(request):
    SQL_ENGINE = create_engine('mysql+mysqldb://root:dodona@dodona/website')
    SQL_CONN = SQL_ENGINE.connect()
    SQL_META = MetaData(bind=SQL_ENGINE)
    signals = Table('macro_signal', SQL_META, autoload=True)

    signal_data = pd.read_sql_table('macro_signal',SQL_ENGINE)

    signal_data = signal_data[['price_date','sp_close','long_confidence','long_threshold','short_threshold']]
    signal_data.columns = ['Date','sp_close','long_confidence','long_threshold','short_threshold']

    latest_signal = 'Long' if signal_data.long_confidence.iloc[-1] >= signal_data.long_threshold.iloc[-1]/100 else 'Short' if (1-signal_data.long_confidence.iloc[-1]) >= signal_data.short_threshold.iloc[-1]/100 else 'Neutral'
    latest_signal_date = signal_data.Date.iloc[-1].strftime('%m/%d/%Y')

    signal_data = signal_data.to_json(orient='records',date_format='iso')

    context = {'chart_data':signal_data,
               'latest_signal':latest_signal,
               'latest_signal_date':latest_signal_date}

    SQL_CONN.close()
    SQL_ENGINE.dispose()

    return render(request, 'site_app/macro_signals.html', context)
