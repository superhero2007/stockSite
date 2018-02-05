from django.contrib.auth.decorators import login_required

from django.urls import reverse
from django.shortcuts import render,redirect
from django.conf import settings

import sys,os
import pandas as pd
import datetime,time
from pandas.tseries.offsets import BDay

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
def equity_search_redirect(request):
    if request.method == 'GET':
        ticker = request.GET.get('ticker','')        
        return redirect(reverse('equities_ticker',args={ticker}))

@login_required
def insider_search_redirect(request):
    if request.method == 'GET':
        ticker = request.GET.get('ticker','')        
        return redirect(reverse('insider_transactions_ticker',args={ticker}))

@login_required
def under_development(request):
    if request.method == 'GET':
        return render(request, 'site_app/under_development.html')

@login_required
def trading_dashboard(request):
    # connect to sql 
    sql_source = Access_SQL_Source(MySQL_Server)
    sql = Access_SQL_DB(MySQL_Server,db='semoms')

    # read account history
    ah = pd.read_sql_table('account_history',sql.ENGINE)

    # get S&P500
    sp500 = sql_source.get_source_eod_data(m_ticker = 'S&P5',vendor='EODData')
    sp500['sp500_daily_return'] = sp500.adj_close.pct_change()

    # add SP500 to account history
    ah['sp500_daily_return'] = ah.TradeDate.map(sp500['sp500_daily_return'])

    # calculate equity curves
    ah['CumPnl'] = (1+ah.CumPnl)
    ah['SP500'] = (1+ah.sp500_daily_return).cumprod()

    StartingDate = ah.TradeDate.iloc[0]
    EndingDate = ah.TradeDate.iloc[-1]
    #convert timestamp to timetuple
    ah['TradeDate'] = ah['TradeDate'].apply(lambda x: time.mktime(x.timetuple()))

    # build context
    context = {'StartingDate': StartingDate,
               'EndingDate': EndingDate,
               'StartingNAV': '${:,}'.format(int(round(ah.SOD_Nav.iloc[0],0))),
               'EndingNAV':'${:,}'.format(int(round(ah.EOD_Nav.iloc[-1],0))),
               'TimeWeightedReturn': '{:.2%}'.format(ah.CumPnl.iloc[-1]-1),
               'chart_data_strategy':ah[['TradeDate','CumPnl']].values.tolist(),
               'chart_data_benchmark':ah[['TradeDate','SP500']].values.tolist(),
               'benchmark_name': 'SP500'}

    sql.close_connection()
    sql_source.close_connection()

    return render(request, 'site_app/trading_dashboard.html', context)


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
        return (render,'site_app/ticker_not_found.html',{'ticker':ticker})


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
    forms = pd.read_sql(formsT.select().where(formsT.c.FilingDate >= today - BDay(3)),sql.ENGINE)

    # download securities master and merge
    sm = sql.get_sec_master() 
    forms = forms.merge(sm,left_on='IssuerCIK',right_on='comp_cik',how='right')
    forms = forms[forms.ticker.notnull() & forms.TransType.notnull()]
    forms = forms[~forms.TransType.isin(['LDG','HO','RB'])]
    #signal_data['AcceptedDate'] = pd.to_datetime(signal_data['AcceptedDate'])

    forms.sort_values('AcceptedDate', ascending=False, inplace=True)

    cols = ['ticker','comp_name','zacks_x_sector_desc','zacks_x_ind_desc','URL','AcceptedDate','FilerName',
                           'InsiderTitle','Director','TransType',
                           'DollarValue']

    forms = forms[cols]

    forms = forms.to_dict(orient='records')

    context = {'forms':forms}
    sql.close_connection()
    return render(request, 'site_app/insider_transactions_latest_filings.html', context)

@login_required
def insider_transactions_ticker(request,ticker):
    ticker = ticker.upper()

    ## Load insider transactions data
    sql = Access_SQL_Source(MySQL_Server)
    formsT = Table('sec_forms_ownership_source', sql.META, autoload=True)

    ## find cik
    sm = sql.get_sec_master()
    sm = sm[sm.ticker==ticker]
    if len(sm)==1:
        cik = sm.iloc[0].comp_cik
        m_ticker = sm.iloc[0].m_ticker
    else:
        return (render,'site_app/ticker_not_found.html',{'ticker':ticker})

    # download ticker forms
    forms = pd.read_sql(formsT.select().where(formsT.c.IssuerCIK ==cik),sql.ENGINE)

    if (not(len(forms))):
        return (render,'site_app/ticker_not_found.html',{'ticker':ticker})


    forms = forms.merge(sm, left_on='IssuerCIK', right_on = 'comp_cik',how='left')
    forms.sort_values('AcceptedDate', ascending=False, inplace=True)
    forms = forms[(forms.valid_purchase + forms.valid_sale)!=0]
    forms['SignalDirection'] = 'LONG'
    forms['SignalDirection'] = forms.SignalDirection.where(forms.valid_purchase,'SHORT')

    cols = ['ticker','comp_name','zacks_x_sector_desc','zacks_x_ind_desc','URL','AcceptedDate','FilerName','InsiderTitle',
            'Director','TenPercentOwner','TransType','DollarValue','SignalDirection']

    forms = forms[cols]

    #get stock prices
    prices = sql.get_source_eod_data(m_ticker=m_ticker,vendor='QM')

    if (not(len(prices))):
        return (render,'site_app/ticker_not_found.html',{'ticker':ticker})

    # change the index of prices so that it can work with the markers
    prices = prices[prices.index >= '2003-01-01']
    prices.reset_index(drop=False,inplace=True)

    #convert to JSON for exchange with JS
    chart_data = prices.to_json(orient='records', date_format='iso') 
    table_data = forms.to_json(orient='records', date_format='iso')

    # build marker data
    it_data = forms.to_dict(orient='records')
    graph_marker_data = [     {
                                "index": g_index, 
                                "tableIndex": t_index,
                                "FilerName": it_data[t_index]['FilerName'],
                                "TransType": it_data[t_index]['TransType'],
                                "DollarValue": it_data[t_index]['DollarValue'],
                                "SignalDirection": it_data[t_index]['SignalDirection'],
                              } 
                                for t_index, t_val in  enumerate(it_data)
                                    for g_index, g_val in enumerate(prices['data_date'])
                                        if ((g_val.date() == t_val['AcceptedDate'].date()) & pd.notnull(t_val['TransType'] not in ['LDG','HO','RB']))
                            ] 

    context = {'stock_info':sm.iloc[0].to_dict(),
               'chart_data':chart_data,
               'table_data':table_data,
               'graph_marker_data':graph_marker_data,
               'it_data':it_data,
               'price_db':prices} # may have to convert price db to dict

    return render(request, 'site_app/insider_transactions_ticker.html', context)


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
