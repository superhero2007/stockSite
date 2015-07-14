
#from requests import get
import warnings
import numpy as np
import pandas as pd
from socket import gethostname
#import multiprocessing
import time
#import traceback
import sys
sys.path.append('/home/tony/projects')
import os
import datetime
from dateutil import relativedelta
import re
from sqlalchemy import *
from sqlalchemy.sql import *
#import ipdb

#from USER_PRIVATE import *


class Access_SQL_Data(object):
    def __init__(self, host=gethostname(), username='root', password=gethostname()):
        self.ENGINE = create_engine('mysql+mysqldb://'+username+':'+password+'@'+host+'/securities_master')
        self.CONN = self.ENGINE.connect()
        self.META = MetaData(bind=self.ENGINE)        

    def get_qm_eod_data (self, sec_id=None, ticker=None, start_date=None, end_date=None, data_list=['price_date','bb_ticker','securities_id','open','high','low','close','volume','adj_open','adj_high','adj_low','adj_close','adj_vol']):

        if pd.isnull(start_date) & pd.isnull(end_date):
            start_date = '1990-01-01'
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')

        elif pd.isnull(start_date) & pd.notnull(end_date):
            start_date = '1990-01-01'

        elif pd.isnull(end_date) & pd.notnull(start_date):
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')

        s_date = bindparam('start_date', start_date, DateTime)
        e_date = bindparam('end_date', end_date, DateTime)

        sec_table = Table('securities', self.META, autoload=True)
        qm_table = Table('qm_eod_eq_prices', self.META, autoload=True)
        zfa_table = Table('zacks_fund_a_data', self.META, autoload=True)
        mkt_table = Table('company_market_data', self.META, autoload=True)
        tech_table = Table('daily_qm_technicals', self.META, autoload=True)

        if pd.isnull(sec_id) & pd.isnull(ticker):
            return(pd.DataFrame())
        elif pd.isnull(sec_id):
            sec_query = select([sec_table.c.securities_id]).where(sec_table.c.bb_ticker==ticker)
            db_result =  self.CONN.execute(sec_query)
            for i in db_result: sec_id = i

            if pd.notnull(sec_id):
                sec_id = sec_id[0]
            else:
                return(pd.DataFrame())

        columns = select([sec_table.c.securities_id,
                          sec_table.c.bb_ticker,
                          sec_table.c.bb_unique_id,
                          sec_table.c.has_qm_eod_data,
                          sec_table.c.is_duplicate_cik,
                          sec_table.c.cik,
                          sec_table.c.exchange,
                          sec_table.c.z_ticker,
                          sec_table.c.z_master_ticker,
                          sec_table.c.z_name,
                          sec_table.c.instr_type,
                          sec_table.c.sic_4_code,
                          sec_table.c.sic_4_desc,
                          sec_table.c.zacks_x_sector_code,
                          sec_table.c.zacks_x_sector_desc,
                          sec_table.c.zacks_x_ind_code,
                          sec_table.c.zacks_x_ind_desc,
                          sec_table.c.zacks_m_ind_code,
                          sec_table.c.zacks_m_ind_desc,
                          sec_table.c.currency_code,
                          sec_table.c.sp500_flag,
                          sec_table.c.rua_flag,
                          sec_table.c.zacks_active_ticker_flag,
                          qm_table.c.price_date, 
                          qm_table.c.open,
                          qm_table.c.high,
                          qm_table.c.low,
                          qm_table.c.close,
                          qm_table.c.volume,
                          qm_table.c.adj_open, 
                          qm_table.c.adj_high, 
                          qm_table.c.adj_low, 
                          qm_table.c.adj_close, 
                          qm_table.c.adj_vol, 
                          mkt_table.c.market_cap,
                          mkt_table.c.mkt_cap_category,
                          mkt_table.c.book_val_per_share,
                          mkt_table.c.shares_outstanding,
                          mkt_table.c.book_market_value,
                        tech_table.c.VolSMA2,
                        tech_table.c.VolSMA10,
                        tech_table.c.VolSMA14,
                        tech_table.c.VolSMA30,
                        tech_table.c.VolSMA250,
                        tech_table.c.LiquidityDelta,
                        tech_table.c.LiquidityDelta_2_10,
                        tech_table.c.RSI_5day,
                        tech_table.c.RSI_10day,
                        tech_table.c.RSI_14day,
                        tech_table.c.AdjCloseSMA5,
                        tech_table.c.AdjCloseSMA10,
                        tech_table.c.AdjCloseSMA20,
                        tech_table.c.AdjCloseSMA50,
                        tech_table.c.AdjCloseSMA200,
                        tech_table.c.AdjCloseSMADelta,
                        tech_table.c.sma_delta_pct,
                        tech_table.c.sma_pos_crossover,
                        tech_table.c.sma_neg_crossover,
                        tech_table.c.AdjCloseSMA50_1q_gain,
                        tech_table.c.AdjCloseSMA50_2q_gain,
                        tech_table.c.AdjCloseEWMA20,
                        tech_table.c.AdjCloseEWMA20_2wk_gain,
                        tech_table.c.AdjClose_Daily_Return,
                        tech_table.c.Volatility50,
                        tech_table.c.Volatility250,
                        tech_table.c.VolatilityDelta,
                        tech_table.c.Volatility5,
                        tech_table.c.Volatility20,
                        tech_table.c.VolatilityDelta_5_20,
                        tech_table.c.MeanDailyReturn50,
                        tech_table.c.MeanDailyReturn250,
                        tech_table.c.MeanDailyReturn5,
                        tech_table.c.MeanDailyReturn20,
                        tech_table.c.high_52wk,
                        tech_table.c.low_52wk,
                        tech_table.c.high_4wk,
                        tech_table.c.low_4wk,
                        tech_table.c.vect_ceil,
                        tech_table.c.vect_floor,
                        tech_table.c.dema_20day,
                        tech_table.c.inst_trendline,
                        tech_table.c.kauf_adapt_ma_20day,
                        tech_table.c.midpoint_20day,
                        tech_table.c.midprice_20day,
                        tech_table.c.para_stop_reverse,
                        tech_table.c.norm_parabolic_sar,
                        tech_table.c.para_stop_reverse_ext,
                        tech_table.c.triple_exp_ma_20day,
                        tech_table.c.weighted_ma_20day,
                        tech_table.c.avg_true_range_5day,
                        tech_table.c.norm_avg_true_range_5day,
                        tech_table.c.true_range,
                        tech_table.c.avg_dir_move_idx_5day,
                        tech_table.c.avg_dir_move_idx_10day,
                        tech_table.c.avg_dir_move_idx_rating_5day,
                        tech_table.c.avg_dir_move_idx_rating_10day,
                        tech_table.c.avg_dir_move_idx_rating_20day,
                        tech_table.c.abs_price_osc,
                        tech_table.c.abs_price_osc_5_10,
                        tech_table.c.aroon_osc_5day,
                        tech_table.c.balance_of_power,
                        tech_table.c.balance_of_power_sma_5,
                        tech_table.c.commodity_channel_idx_5day,
                        tech_table.c.chande_mom_osc_5day,
                        tech_table.c.dir_mov_idx_5day,
                        tech_table.c.money_flow_idx_5day,
                        tech_table.c.minus_dir_ind_5day,
                        tech_table.c.minus_dir_move_5day,
                        tech_table.c.minus_dir_ind_14day,
                        tech_table.c.minus_dir_move_14day,
                        tech_table.c.momentum_5day,
                        tech_table.c.plus_dir_ind_5day,
                        tech_table.c.plus_dir_move_5day,
                        tech_table.c.plus_dir_ind_14day,
                        tech_table.c.plus_dir_move_14day,
                        tech_table.c.pct_price_osc,
                        tech_table.c.pct_price_osc_4_10,
                        tech_table.c.rate_change_5day,
                        tech_table.c.pct_rate_change_5day,
                        tech_table.c.ratio_rate_change_5day,
                        tech_table.c.roc_triple_smooth_ema_10day,
                        tech_table.c.ultimate_osc,
                        tech_table.c.williams_pctr_5day,
                        tech_table.c.dom_cycle_period,
                        tech_table.c.dom_cycle_phase,
                        tech_table.c.trend_vs_cycle,
                        tech_table.c.chaikin_ad_line,
                        tech_table.c.chaikin_ad_osc,
                        tech_table.c.on_balance_vol,
                        tech_table.c.rua_beta_1mo,
                        tech_table.c.rua_beta_3mo,
                        tech_table.c.rua_beta_6mo,
                        tech_table.c.rua_beta_1yr,
                        tech_table.c.rua_beta_2yr,
                        tech_table.c.sp_beta_1mo,
                        tech_table.c.sp_beta_3mo,
                        tech_table.c.sp_beta_6mo,
                        tech_table.c.sp_beta_1yr,
                        tech_table.c.sp_beta_2yr,
                        tech_table.c.vix_beta_1mo,
                        tech_table.c.vix_beta_3mo,
                        tech_table.c.vix_beta_6mo,
                        tech_table.c.vix_beta_1yr,
                        tech_table.c.vix_beta_2yr,
                        tech_table.c.two_crows,
                        tech_table.c.three_black_crows,
                        tech_table.c.three_inside,
                        tech_table.c.three_line_strike,
                        tech_table.c.three_outside,
                        tech_table.c.three_stars_south,
                        tech_table.c.three_white_soldiers,
                        tech_table.c.abandoned_baby,
                        tech_table.c.advance_block,
                        tech_table.c.belt_hold,
                        tech_table.c.breakaway,
                        tech_table.c.closing_marubozu,
                        tech_table.c.conceal_baby_swallow,
                        tech_table.c.counterattack,
                        tech_table.c.dark_cloud_cover,
                        tech_table.c.doji,
                        tech_table.c.doji_star,
                        tech_table.c.dragonfly_doji,
                        tech_table.c.engulfing,
                        tech_table.c.evening_doji_star,
                        tech_table.c.evening_star,
                        tech_table.c.gap_side_by_side_white,
                        tech_table.c.gravestone_doji,
                        tech_table.c.hammer,
                        tech_table.c.hanging_man,
                        tech_table.c.harami,
                        tech_table.c.harami_cross,
                        tech_table.c.high_wave,
                        tech_table.c.hikkake,
                        tech_table.c.modified_hikkake,
                        tech_table.c.homing_pigeon,
                        tech_table.c.identical_three_crows,
                        tech_table.c.in_neck,
                        tech_table.c.inverted_hammer,
                        tech_table.c.kicking,
                        tech_table.c.kicking_by_length,
                        tech_table.c.ladder_bottom,
                        tech_table.c.long_legged_doji,
                        tech_table.c.long_line,
                        tech_table.c.marubozu,
                        tech_table.c.matching_low,
                        tech_table.c.mat_hold,
                        tech_table.c.morning_star_doji,
                        tech_table.c.morning_star,
                        tech_table.c.on_neck,
                        tech_table.c.piercing,
                        tech_table.c.rickshaw_man,
                        tech_table.c.rising_falling,
                        tech_table.c.separating_lines,
                        tech_table.c.shooting_star,
                        tech_table.c.short_line,
                        tech_table.c.spinning_top,
                        tech_table.c.stalled_pattern,
                        tech_table.c.stick_sandwich,
                        tech_table.c.takuri,
                        tech_table.c.tasuki_gap,
                        tech_table.c.thrusting,
                        tech_table.c.tristar,
                        tech_table.c.unique_three_river,
                        tech_table.c.upside_gap_two_crows,
                        tech_table.c.upside_downside_gap,
                        tech_table.c.avg_price,
                        tech_table.c.median_price,
                        tech_table.c.typical_price,
                        tech_table.c.weighted_close_price,
                        tech_table.c.bband_upper,
                        tech_table.c.bband_middle,
                        tech_table.c.bband_lower,
                        tech_table.c.mesa_adaptive_ma,
                        tech_table.c.following_adaptive_ma,
                        tech_table.c.aroon_down_5,
                        tech_table.c.aroon_up_5,
                        tech_table.c.macd_5_15_5,
                        tech_table.c.macd_signal_5_15_5,
                        tech_table.c.macd_hist_5_15_5,
                        tech_table.c.macd_ext,
                        tech_table.c.macd_ext_signal,
                        tech_table.c.macd_ext_hist,
                        tech_table.c.macd_fix,
                        tech_table.c.macd_fix_signal,
                        tech_table.c.macd_fix_hist,
                        tech_table.c.stochastic_ind_k,
                        tech_table.c.stochastic_ind_d,
                        tech_table.c.stochastic_rsi_k,
                        tech_table.c.stochastic_rsi_d,
                        tech_table.c.stochastic_fast_k,
                        tech_table.c.stochastic_fast_d,
                        tech_table.c.phasor_phase,
                        tech_table.c.phasor_quadrature,
                        tech_table.c.ht_sine,
                        tech_table.c.ht_lead_sine])
        get_data = columns.select_from(sec_table.join(qm_table, (sec_table.c.securities_id==qm_table.c.securities_id) & (sec_table.c.securities_id==sec_id) & (qm_table.c.price_date.between(s_date, e_date))).outerjoin(mkt_table, (sec_table.c.securities_id==mkt_table.c.securities_id) & (qm_table.c.price_date==mkt_table.c.price_date)).outerjoin(tech_table, (qm_table.c.securities_id==tech_table.c.securities_id) & (qm_table.c.price_date==tech_table.c.price_date)))

        db_result = self.CONN.execute(get_data)
        df = pd.DataFrame(db_result.fetchall())

        if len(df):
            df.columns = db_result.keys()
            df.dropna(subset=['open','high','low','close','volume','adj_open','adj_high','adj_low','adj_close','adj_vol'], axis=0, how='all', inplace=True)
            j = df.columns.isin(data_list)
            df = df.loc[:,j]
        
            df.set_index('price_date', inplace=True)
            df.sort(inplace=True)

            return(df)

        else:
            return(pd.DataFrame())



    def get_zfa_data (self, sec_id=None, ticker=None, start_date=None, end_date=None, per_type='Q', data_list=[]):

        if pd.isnull(start_date) & pd.isnull(end_date):
            start_date = '1990-01-01'
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')

        elif pd.isnull(start_date) & pd.notnull(end_date):
            start_date = '1990-01-01'

        elif pd.isnull(end_date) & pd.notnull(start_date):
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')
        
        s_date = bindparam('start_date', start_date, DateTime)
        e_date = bindparam('end_date', end_date, DateTime)

        sec_table = Table('securities', self.META, autoload=True)
        zfa_table = Table('zacks_fund_a_data', self.META, autoload=True)

        if pd.isnull(sec_id) & pd.isnull(ticker):
            return(pd.DataFrame())
        elif pd.isnull(sec_id):
            sec_query = select([sec_table.c.securities_id]).where(sec_table.c.bb_ticker==ticker)
            db_result =  self.CONN.execute(sec_query)
            for i in db_result: sec_id = i
            sec_id = sec_id[0]

        columns = select([sec_table.c.bb_ticker,
                          sec_table.c.bb_unique_id,
                          sec_table.c.has_qm_eod_data,
                          sec_table.c.is_duplicate_cik,
                          sec_table.c.cik,
                          sec_table.c.exchange,
                          sec_table.c.z_ticker,
                          sec_table.c.z_master_ticker,
                          sec_table.c.z_name,
                          sec_table.c.instr_type,
                          sec_table.c.sic_4_code,
                          sec_table.c.sic_4_desc,
                          sec_table.c.zacks_x_sector_code,
                          sec_table.c.zacks_x_sector_desc,
                          sec_table.c.zacks_x_ind_code,
                          sec_table.c.zacks_x_ind_desc,
                          sec_table.c.zacks_m_ind_code,
                          sec_table.c.zacks_m_ind_desc,
                          sec_table.c.currency_code,
                          sec_table.c.sp500_flag,
                          sec_table.c.rua_flag,
                          sec_table.c.zacks_active_ticker_flag,
                        zfa_table.c.comp_name,
                        zfa_table.c.comp_name_2,
                        zfa_table.c.exchange,
                        zfa_table.c.currency_code,
                        zfa_table.c.per_end_date,
                        zfa_table.c.per_type,
                        zfa_table.c.per_code,
                        zfa_table.c.per_fisc_year,
                        zfa_table.c.per_fisc_qtr,
                        zfa_table.c.per_cal_year,
                        zfa_table.c.per_cal_qtr,
                        zfa_table.c.data_type_ind,
                        zfa_table.c.filing_type,
                        zfa_table.c.qtr_nbr,
                        zfa_table.c.fye_month,
                        zfa_table.c.comp_cik,
                        zfa_table.c.per_len,
                        zfa_table.c.sic_code,
                        zfa_table.c.filing_date,
                        zfa_table.c.last_changed_date,
                        zfa_table.c.state_incorp_name,
                        zfa_table.c.bus_address_line_1,
                        zfa_table.c.bus_city,
                        zfa_table.c.bus_state_name,
                        zfa_table.c.bus_post_code,
                        zfa_table.c.bus_phone_nbr,
                        zfa_table.c.bus_fax_nbr,
                        zfa_table.c.mail_address_line_1,
                        zfa_table.c.mail_city,
                        zfa_table.c.mail_state_name,
                        zfa_table.c.mail_post_code,
                        zfa_table.c.country_name,
                        zfa_table.c.country_code,
                        zfa_table.c.home_exchange_name,
                        zfa_table.c.emp_cnt,
                        zfa_table.c.comp_url,
                        zfa_table.c.email_addr,
                        zfa_table.c.nbr_shares_out,
                        zfa_table.c.shares_out_date,
                        zfa_table.c.officer_name_1,
                        zfa_table.c.officer_title_1,
                        zfa_table.c.officer_name_2,
                        zfa_table.c.officer_title_2,
                        zfa_table.c.officer_name_3,
                        zfa_table.c.officer_title_3,
                        zfa_table.c.officer_name_4,
                        zfa_table.c.officer_title_4,
                        zfa_table.c.officer_name_5,
                        zfa_table.c.officer_title_5,
                        zfa_table.c.tot_revnu,
                        zfa_table.c.cost_good_sold,
                        zfa_table.c.gross_profit,
                        zfa_table.c.tot_oper_exp,
                        zfa_table.c.oper_income,
                        zfa_table.c.tot_non_oper_income_exp,
                        zfa_table.c.pre_tax_income,
                        zfa_table.c.income_aft_tax,
                        zfa_table.c.income_cont_oper,
                        zfa_table.c.consol_net_income_loss,
                        zfa_table.c.net_income_loss_share_holder,
                        zfa_table.c.eps_basic_cont_oper,
                        zfa_table.c.eps_basic_consol,
                        zfa_table.c.basic_net_eps,
                        zfa_table.c.eps_diluted_cont_oper,
                        zfa_table.c.eps_diluted_consol,
                        zfa_table.c.diluted_net_eps,
                        zfa_table.c.dilution_factor,
                        zfa_table.c.avg_d_shares,
                        zfa_table.c.avg_b_shares,
                        zfa_table.c.norm_pre_tax_income,
                        zfa_table.c.norm_aft_tax_income,
                        zfa_table.c.ebitda,
                        zfa_table.c.ebit,
                        zfa_table.c.tot_curr_asset,
                        zfa_table.c.net_prop_plant_equip,
                        zfa_table.c.tot_lterm_asset,
                        zfa_table.c.tot_asset,
                        zfa_table.c.tot_curr_liab,
                        zfa_table.c.tot_lterm_debt,
                        zfa_table.c.tot_lterm_liab,
                        zfa_table.c.tot_liab,
                        zfa_table.c.tot_comm_equity,
                        zfa_table.c.tot_share_holder_equity,
                        zfa_table.c.tot_liab_share_holder_equity,
                        zfa_table.c.comm_shares_out,
                        zfa_table.c.tang_stock_holder_equity,
                        zfa_table.c.cash_flow_oper_activity,
                        zfa_table.c.cash_flow_invst_activity,
                        zfa_table.c.cash_flow_fin_activity,
                        zfa_table.c.incr_decr_cash,
                        zfa_table.c.beg_cash,
                        zfa_table.c.end_cash,
                        zfa_table.c.stock_based_compsn,
                        zfa_table.c.comm_stock_div_paid,
                        zfa_table.c.pref_stock_div_paid,
                        zfa_table.c.tot_deprec_amort_qd,
                        zfa_table.c.stock_based_compsn_qd,
                        zfa_table.c.cash_flow_oper_activity_qd,
                        zfa_table.c.net_change_prop_plant_equip_qd,
                        zfa_table.c.comm_stock_div_paid_qd,
                        zfa_table.c.pref_stock_div_paid_qd,
                        zfa_table.c.tot_comm_pref_stock_div_qd,
                        zfa_table.c.curr_ratio,
                        zfa_table.c.non_perform_asset_tot_loan,
                        zfa_table.c.loan_loss_reserve,
                        zfa_table.c.lterm_debt_cap,
                        zfa_table.c.tot_debt_tot_equity,
                        zfa_table.c.gross_margin,
                        zfa_table.c.oper_profit_margin,
                        zfa_table.c.ebit_margin,
                        zfa_table.c.ebitda_margin,
                        zfa_table.c.pretax_profit_margin,
                        zfa_table.c.profit_margin,
                        zfa_table.c.free_cash_flow,
                        zfa_table.c.loss_ratio,
                        zfa_table.c.exp_ratio,
                        zfa_table.c.comb_ratio,
                        zfa_table.c.asset_turn,
                        zfa_table.c.invty_turn,
                        zfa_table.c.rcv_turn,
                        zfa_table.c.day_sale_rcv,
                        zfa_table.c.ret_equity,
                        zfa_table.c.ret_tang_equity,
                        zfa_table.c.ret_asset,
                        zfa_table.c.ret_invst,
                        zfa_table.c.free_cash_flow_per_share,
                        zfa_table.c.book_val_per_share,
                        zfa_table.c.oper_cash_flow_per_share,
                        zfa_table.c.m_ticker,
                        zfa_table.c.wavg_shares_out,
                        zfa_table.c.wavg_shares_out_diluted])
        get_data = columns.select_from(sec_table.join(zfa_table, (sec_table.c.securities_id==zfa_table.c.securities_id) & (sec_table.c.securities_id==sec_id) & (zfa_table.c.per_end_date.between(s_date, e_date) & (zfa_table.c.per_type==per_type))))

        db_result = self.CONN.execute(get_data)
        df = pd.DataFrame(db_result.fetchall())
        
        if len(df):
            df.columns = db_result.keys()

            if len(data_list):
                j = df.columns.isin(data_list)
                df = df.loc[:,j]
                df.set_index('per_end_date', inplace=True)
                df.sort(inplace=True)
                return(df)

            else:
                df.set_index('per_end_date', inplace=True)
                df.sort(inplace=True)
                return(df)

        else:
            return(pd.DataFrame())



    def get_short_interest_data (self, sec_id=None, ticker=None, start_date=None, end_date=None, data_list=[]):

        if pd.isnull(start_date) & pd.isnull(end_date):
            start_date = '1990-01-01'
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')

        elif pd.isnull(start_date) & pd.notnull(end_date):
            start_date = '1990-01-01'

        elif pd.isnull(end_date) & pd.notnull(start_date):
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')
        
        s_date = bindparam('start_date', start_date, DateTime)
        e_date = bindparam('end_date', end_date, DateTime)

        sec_table = Table('securities', self.META, autoload=True)
        short_table = Table('short_interest_markit', self.META, autoload=True)

        if pd.isnull(sec_id) & pd.isnull(ticker):
            return(pd.DataFrame())
        elif pd.isnull(sec_id):
            sec_query = select([sec_table.c.securities_id]).where(sec_table.c.bb_ticker==ticker)
            db_result =  self.CONN.execute(sec_query)
            for i in db_result: sec_id = i
            sec_id = sec_id[0]

        columns = select([sec_table.c.bb_ticker,
                          sec_table.c.bb_unique_id,
                          sec_table.c.has_qm_eod_data,
                          sec_table.c.is_duplicate_cik,
                          sec_table.c.cik,
                          sec_table.c.exchange,
                          sec_table.c.z_ticker,
                          sec_table.c.z_master_ticker,
                          sec_table.c.z_name,
                          sec_table.c.instr_type,
                          sec_table.c.sic_4_code,
                          sec_table.c.sic_4_desc,
                          sec_table.c.zacks_x_sector_code,
                          sec_table.c.zacks_x_sector_desc,
                          sec_table.c.zacks_x_ind_code,
                          sec_table.c.zacks_x_ind_desc,
                          sec_table.c.zacks_m_ind_code,
                          sec_table.c.zacks_m_ind_desc,
                          sec_table.c.currency_code,
                          sec_table.c.sp500_flag,
                          sec_table.c.rua_flag,
                          sec_table.c.zacks_active_ticker_flag,
                        short_table.c.data_date,
                        short_table.c.Indicators_DIMV,
                        short_table.c.Indicators_DIPS,
                        short_table.c.Indicators_DNS,
                        short_table.c.Indicators_DPS,
                        short_table.c.Indicators_DSS,
                        short_table.c.MarketColour_DaysToCover,
                        short_table.c.MarketColour_DaysToCoverQuantity,
                        short_table.c.MarketColour_DCBS,
                        short_table.c.MarketColour_IndicativeFee,
                        short_table.c.MarketColour_IndicativeRebate,
                        short_table.c.MarketColour_MarketCap,
                        short_table.c.MarketColour_PcFreeFloatQuantityOnLoan,
                        short_table.c.MarketColour_PcFreeFloatValueOnLoan,
                        short_table.c.MarketColour_PcMarketCapOnLoan,
                        short_table.c.MarketColour_PcSharesOutstandingOnLoan,
                        short_table.c.MarketColour_Price,
                        short_table.c.MarketColour_PriceCurrency,
                        short_table.c.MarketColour_SharesOutstanding,
                        short_table.c.MarketColour_ShortLoanQuantity,
                        short_table.c.MarketColour_ShortLoanValue,
                        short_table.c.MarketColour_VolumeTraded,
                        short_table.c.MarketColour_NextDividendDate,
                        short_table.c.MarketColour_LastDividendDate,
                        short_table.c.ActiveInventory_ActiveAvailableQuantity,
                        short_table.c.ActiveInventory_ActiveAvailableValue,
                        short_table.c.ActiveInventory_ActiveLendableQuantity,
                        short_table.c.ActiveInventory_ActiveLendableValue,
                        short_table.c.ActiveInventory_ActiveUtilisation_x,
                        short_table.c.ActiveInventory_ActiveUtilisationByQuantity_x,
                        short_table.c.Trading_ActiveUtilisation_x,
                        short_table.c.Trading_ActiveUtilisationByQuantity_x,
                        short_table.c.ActiveInventory_ActiveAvailableRatio,
                        short_table.c.ActiveInventory_ActiveLendableAsPcFreeFloatQuantity,
                        short_table.c.ActiveInventory_ActiveLendableAsPcFreeFloatValue,
                        short_table.c.ActiveInventory_ActiveLendableAsPcMarketCap,
                        short_table.c.ActiveInventory_ActiveLendableAsPcSharesOutstanding,
                        short_table.c.ActiveInventory_ActiveUtilisation_y,
                        short_table.c.ActiveInventory_ActiveUtilisationByQuantity_y,
                        short_table.c.Inventory_Utilisation_x,
                        short_table.c.Inventory_UtilisationByQuantity_x,
                        short_table.c.Trading_ActiveUtilisation_y,
                        short_table.c.Trading_ActiveUtilisationByQuantity_y,
                        short_table.c.Trading_BorrowerConcentration,
                        short_table.c.Trading_LenderConcentration,
                        short_table.c.Trading_Utilisation_x,
                        short_table.c.Trading_UtilisationByQuantity_x,
                        short_table.c.Trading_Date,
                        short_table.c.Trading_Index1_BorrowerMarketShare,
                        short_table.c.Trading_Index1_LenderMarketShare,
                        short_table.c.Trading_NewLoanQuantity,
                        short_table.c.Trading_NewLoanValue,
                        short_table.c.Trading_Quantity,
                        short_table.c.Trading_QuantityOnLoan,
                        short_table.c.Trading_TransactionCount,
                        short_table.c.Trading_ValueOnLoan,
                        short_table.c.Trading_ValueOnLoanVsCash,
                        short_table.c.Inventory_AvailableQuantity,
                        short_table.c.Inventory_AvailableValue,
                        short_table.c.Inventory_Index1_InventoryMarketShare,
                        short_table.c.Inventory_InventoryConcentration,
                        short_table.c.Inventory_LendableQuantity,
                        short_table.c.Inventory_LendableValue,
                        short_table.c.Inventory_Utilisation_y,
                        short_table.c.Inventory_UtilisationByQuantity_y,
                        short_table.c.Trading_Utilisation_y,
                        short_table.c.Trading_UtilisationByQuantity_y,
                        short_table.c.Inventory_LenderQuantity,
                        short_table.c.Inventory_LenderQuantityOnLoan,
                        short_table.c.Inventory_LenderValue,
                        short_table.c.Inventory_LenderValueOnLoan])
        get_data = columns.select_from(sec_table.join(short_table, (sec_table.c.securities_id==short_table.c.securities_id) & (sec_table.c.securities_id==sec_id) & (short_table.c.data_date.between(s_date, e_date))))

        db_result = self.CONN.execute(get_data)
        df = pd.DataFrame(db_result.fetchall())
        
        if len(df):
            df.columns = db_result.keys()

            if len(data_list):
                j = df.columns.isin(data_list)
                df = df.loc[:,j]
                df.set_index('data_date', inplace=True)
                df.sort(inplace=True)
                return(df)

            else:
                df.set_index('data_date', inplace=True)
                df.sort(inplace=True)              
                return(df)

        else:
            return(pd.DataFrame())



    def get_securities_table(self, hasEOD=True, hasCIK=True, dupCIK=False):
        sec_df = pd.io.sql.read_sql_table('securities', self.ENGINE)
        
        if hasCIK==True:
            cik_filter= ['000000None','0000000nan',None]
            output = sec_df[(sec_df.has_qm_eod_data==hasEOD) & (~sec_df.cik.isin(cik_filter)) & (sec_df.is_duplicate_cik==dupCIK)]
            return(output)
        else:
            cik_filter= ['000000None','0000000nan',None]
            output = sec_df[(sec_df.has_qm_eod_data==hasEOD) & (sec_df.cik.isin(cik_filter)) & (sec_df.is_duplicate_cik==dupCIK)]
            return(output)



    def get_market_indices(self, ticker, start_date=None, end_date=None, data_list=['price_date','ticker','open','high','low','close','volume','adj_close']):

        if pd.isnull(start_date) & pd.isnull(end_date):
            start_date = '1900-01-01'
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')

        elif pd.isnull(start_date) & pd.notnull(end_date):
            start_date = '1900-01-01'

        elif pd.isnull(end_date) & pd.notnull(start_date):
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')
        
        s_date = bindparam('start_date', start_date, DateTime)
        e_date = bindparam('end_date', end_date, DateTime)

        ind_table = Table('market_indices', self.META, autoload=True)

        get_data = select([ind_table.c.price_date, ind_table.c.ticker, ind_table.c.open, ind_table.c.high, ind_table.c.low, ind_table.c.close, ind_table.c.adj_close]).where(ind_table.c.ticker==ticker).where(ind_table.c.price_date.between(s_date, e_date))
        db_result2 = self.CONN.execute(get_data)
        df = pd.DataFrame(db_result2.fetchall())

        if (not(len(df))):
            return(pd.DataFrame())

        df.columns = db_result2.keys()
        j = df.columns.isin(data_list)
        df = df.loc[:,j]

        df.set_index('price_date', inplace=True)
        df.sort(inplace=True)

        return(df)


    def get_earnings_calendar (self, sec_id=None, ticker=None):

        earn_table = Table('earnings_calendar', self.META, autoload=True)
        sec_table = Table('securities', self.META, autoload=True)

        if pd.isnull(sec_id) & pd.isnull(ticker):
            return(pd.DataFrame())
        elif pd.isnull(sec_id):
            sec_query = select([sec_table.c.securities_id]).where(sec_table.c.bb_ticker==ticker)
            db_result =  self.CONN.execute(sec_query)
            for i in db_result: sec_id = i
            sec_id = sec_id[0]

        get_data = select([earn_table.c.cik, earn_table.c.securities_id, earn_table.c.FormType, earn_table.c.QuarterEnding]).where(earn_table.c.securities_id==sec_id)

        db_result = self.CONN.execute(get_data)
        df = pd.DataFrame(db_result.fetchall())

        if (not(len(df))):
            return(pd.DataFrame())

        df.columns = db_result.keys()
        df['QuarterEnding'] = df['QuarterEnding'].apply(lambda x: pd.to_datetime(x, coerce=True))
        df.dropna(subset=['QuarterEnding'], axis=0, inplace=True)
        df = df[df['QuarterEnding']<datetime.datetime.today()]
        df.set_index('QuarterEnding', inplace=True)
        df.sort(inplace=True)

        return(df)




    def get_us_treasury_data(self, start_date=None, end_date=None, data_list=['price_date','YR_1']):

        if pd.isnull(start_date) & pd.isnull(end_date):
            start_date = '1900-01-01'
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')

        elif pd.isnull(start_date) & pd.notnull(end_date):
            start_date = '1900-01-01'

        elif pd.isnull(end_date) & pd.notnull(start_date):
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')

        s_date = bindparam('start_date', start_date, DateTime)
        e_date = bindparam('end_date', end_date, DateTime)

        treas_table = Table('us_treasury_rates', self.META, autoload=True)
        get_data = select([treas_table.c.price_date,treas_table.c.MO_1, treas_table.c.MO_3, treas_table.c.MO_6, treas_table.c.YR_1, 
                           treas_table.c.YR_2,treas_table.c.YR_3, treas_table.c.YR_5, treas_table.c.YR_7, treas_table.c.YR_10, 
                           treas_table.c.YR_20, treas_table.c.YR_30]).where(treas_table.c.price_date.between(s_date, e_date))
        db_result = self.CONN.execute(get_data)
        df = pd.DataFrame(db_result.fetchall())

        if (not(len(df))):
            return(pd.DataFrame())

        df.columns = db_result.keys()
        
        j = df.columns.isin(data_list)
        df = df.loc[:,j]
        
        df.set_index('price_date', inplace=True)
        df.sort(inplace=True)

        return(df)



    def get_sec_table(self, isActive=True, hasCIK=True):
        sec_df = pd.io.sql.read_sql_table('securities2', self.ENGINE)
        
        if hasCIK==True:
            cik_filter= ['000000None','0000000nan',None]
            output = sec_df[(sec_df.active==isActive) & (~sec_df.cik.isin(cik_filter))]
            return(output)
        else:
            cik_filter= ['000000None','0000000nan',None]
            output = sec_df[(sec_df.active==isActive) & (sec_df.cik.isin(cik_filter))]
            return(output)


    def get_tech_signals_table (self, sec_id=[], ticker=[], start_date=None, end_date=None, data_list=[]):

        if pd.isnull(start_date) & pd.isnull(end_date):
            start_date = '1990-01-01'
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')

        elif pd.isnull(start_date) & pd.notnull(end_date):
            start_date = '1990-01-01'

        elif pd.isnull(end_date) & pd.notnull(start_date):
            end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')
        
        s_date = bindparam('start_date', start_date, DateTime)
        e_date = bindparam('end_date', end_date, DateTime)

        signal_table = Table('technical_signals_qm', self.META, autoload=True)
        sec_table = Table('securities', self.META, autoload=True)

        if (not sec_id) & (not ticker):
            return(pd.DataFrame())
        elif not sec_id:
            sec_query = select([sec_table.c.securities_id]).where(sec_table.c.bb_ticker.in_(ticker))
            db_result =  self.CONN.execute(sec_query)
            sec_id  = pd.DataFrame(db_result.fetchall())
            sec_id = sec_id[0].tolist()

        get_data = select([signal_table.c.securities_id,
                           signal_table.c.price_date,
                           signal_table.c.bb_ticker,
                           signal_table.c.sic_4_code,
                           signal_table.c.adj_open,
                           signal_table.c.adj_high,
                           signal_table.c.adj_low,
                           signal_table.c.adj_close,
                           signal_table.c.adj_vol,
                           signal_table.c.mkt_cap_category,
                           signal_table.c.VolSMA2,
                           signal_table.c.VolSMA14,
                           signal_table.c.VolSMA30,
                           signal_table.c.VolSMA250,
                           signal_table.c.LiquidityDelta,
                           signal_table.c.RSI_14day,
                           signal_table.c.AdjCloseSMA5,
                           signal_table.c.AdjCloseSMA10,
                           signal_table.c.AdjCloseSMA20,
                           signal_table.c.AdjCloseSMA50,
                           signal_table.c.AdjCloseSMA200,
                           signal_table.c.AdjCloseSMADelta,
                           signal_table.c.sma_delta_pct,
                           signal_table.c.sma_pos_crossover,
                           signal_table.c.sma_neg_crossover,
                           signal_table.c.AdjCloseSMA50_1q_gain,
                           signal_table.c.AdjCloseSMA50_2q_gain,
                           signal_table.c.AdjCloseEWMA20,
                           signal_table.c.AdjCloseEWMA20_2wk_gain,
                           signal_table.c.AdjClose_Daily_Return,
                           signal_table.c.Volatility50,
                           signal_table.c.Volatility250,
                           signal_table.c.VolatilityDelta,
                           signal_table.c.high_52wk,
                           signal_table.c.low_52wk,
                           signal_table.c.MeanDailyReturn50,
                           signal_table.c.MeanDailyReturn250,
                           signal_table.c.vect_ceil,
                           signal_table.c.vect_floor,
                           signal_table.c.dema_20day,
                           signal_table.c.inst_trendline,
                           signal_table.c.kauf_adapt_ma_20day,
                           signal_table.c.midpoint_20day,
                           signal_table.c.midprice_20day,
                           signal_table.c.para_stop_reverse,
                           signal_table.c.para_stop_reverse_ext,
                           signal_table.c.triple_exp_ma_20day,
                           signal_table.c.weighted_ma_20day,
                           signal_table.c.avg_true_range_20day,
                           signal_table.c.norm_avg_true_range_20day,
                           signal_table.c.true_range,
                           signal_table.c.avg_dir_move_idx_14day,
                           signal_table.c.avg_dir_move_idx_20day,
                           signal_table.c.avg_dir_move_idx_rating_20day,
                           signal_table.c.abs_price_osc,
                           signal_table.c.aroon_osc_20day,
                           signal_table.c.balance_of_power,
                           signal_table.c.commodity_channel_idx_20day,
                           signal_table.c.chande_mom_osc_20day,
                           signal_table.c.dir_mov_idx_20day,
                           signal_table.c.money_flow_idx_20day,
                           signal_table.c.minus_dir_ind_20day,
                           signal_table.c.minus_dir_move_20day,
                           signal_table.c.momentum_20day,
                           signal_table.c.plus_dir_ind_20day,
                           signal_table.c.plus_dir_move_20day,
                           signal_table.c.pct_price_osc,
                           signal_table.c.rate_change_20day,
                           signal_table.c.pct_rate_change_20day,
                           signal_table.c.ratio_rate_change_20day,
                           signal_table.c.roc_triple_smooth_ema_20day,
                           signal_table.c.ultimate_osc,
                           signal_table.c.williams_pctr_20day,
                           signal_table.c.dom_cycle_period,
                           signal_table.c.dom_cycle_phase,
                           signal_table.c.trend_vs_cycle,
                           signal_table.c.chaikin_ad_line,
                           signal_table.c.chaikin_ad_osc,
                           signal_table.c.on_balance_vol,
                           signal_table.c.avg_price,
                           signal_table.c.median_price,
                           signal_table.c.typical_price,
                           signal_table.c.weighted_close_price,
                           signal_table.c.bband_upper,
                           signal_table.c.bband_middle,
                           signal_table.c.bband_lower,
                           signal_table.c.mesa_adaptive_ma,
                           signal_table.c.following_adaptive_ma,
                           signal_table.c.aroon_down,
                           signal_table.c.aroon_up,
                           signal_table.c.ma_converge_diverge,
                           signal_table.c.macd_signal,
                           signal_table.c.macd_hist,
                           signal_table.c.macd_ext,
                           signal_table.c.macd_ext_signal,
                           signal_table.c.macd_ext_hist,
                           signal_table.c.macd_fix,
                           signal_table.c.macd_fix_signal,
                           signal_table.c.macd_fix_hist,
                           signal_table.c.stochastic_ind_k,
                           signal_table.c.stochastic_ind_d,
                           signal_table.c.stochastic_rsi_k,
                           signal_table.c.stochastic_rsi_d,
                           signal_table.c.stochastic_fast_k,
                           signal_table.c.stochastic_fast_d,
                           signal_table.c.phasor_phase,
                           signal_table.c.phasor_quadrature,
                           signal_table.c.ht_sine,
                           signal_table.c.ht_lead_sine,
                           signal_table.c.signal_year,
                           signal_table.c.signal_qtr,
                           signal_table.c.year_qtr,
                           signal_table.c.day_week,
                           signal_table.c.days_end_qt,
                           signal_table.c.created_date,
                           signal_table.c.ret_1day,
                           signal_table.c.ret_2day,
                           signal_table.c.ret_3day,
                           signal_table.c.ret_4day,
                           signal_table.c.ret_5day,
                           signal_table.c.ret_7day,
                           signal_table.c.ret_10day,
                           signal_table.c.ret_15day,
                           signal_table.c.ret_20day,
                           signal_table.c.trend_ind_3day,
                           signal_table.c.trend_ind_5day,
                           signal_table.c.trend_ind_10day,
                           signal_table.c.trend_ind_15day,
                           signal_table.c.trend_ind_20day,
                           signal_table.c.trend_ind_40day,
                           signal_table.c.trend_ind_60day,
                           signal_table.c.trend_ind_80day,
                           signal_table.c.trend_ind_100day,
                           signal_table.c.trend_ind_120day,
                           signal_table.c.hammer_str_3,
                           signal_table.c.hammer_str_5,
                           signal_table.c.hammer_str_10,
                           signal_table.c.hammer_str_15,
                           signal_table.c.hammer_str_20,
                           signal_table.c.hammer_str_40,
                           signal_table.c.hammer_str_60,
                           signal_table.c.hammer_str_80,
                           signal_table.c.hammer_str_100,
                           signal_table.c.hammer_str_120,
                           signal_table.c.engulf_bull_str_3,
                           signal_table.c.engulf_bull_str_5,
                           signal_table.c.engulf_bull_str_10,
                           signal_table.c.engulf_bull_str_15,
                           signal_table.c.engulf_bull_str_20,
                           signal_table.c.engulf_bull_str_40,
                           signal_table.c.engulf_bull_str_60,
                           signal_table.c.engulf_bull_str_80,
                           signal_table.c.engulf_bull_str_100,
                           signal_table.c.engulf_bull_str_120,
                           signal_table.c.three_sldr_str_3,
                           signal_table.c.three_sldr_str_5,
                           signal_table.c.three_sldr_str_10,
                           signal_table.c.three_sldr_str_15,
                           signal_table.c.three_sldr_str_20,
                           signal_table.c.three_sldr_str_40,
                           signal_table.c.three_sldr_str_60,
                           signal_table.c.three_sldr_str_80,
                           signal_table.c.three_sldr_str_100,
                           signal_table.c.three_sldr_str_120,
                           signal_table.c.morning_star_str_3,
                           signal_table.c.morning_star_str_5,
                           signal_table.c.morning_star_str_10,
                           signal_table.c.morning_star_str_15,
                           signal_table.c.morning_star_str_20,
                           signal_table.c.morning_star_str_40,
                           signal_table.c.morning_star_str_60,
                           signal_table.c.morning_star_str_80,
                           signal_table.c.morning_star_str_100,
                           signal_table.c.morning_star_str_120,
                           signal_table.c.three_ins_bull_str_3,
                           signal_table.c.three_ins_bull_str_5,
                           signal_table.c.three_ins_bull_str_10,
                           signal_table.c.three_ins_bull_str_15,
                           signal_table.c.three_ins_bull_str_20,
                           signal_table.c.three_ins_bull_str_40,
                           signal_table.c.three_ins_bull_str_60,
                           signal_table.c.three_ins_bull_str_80,
                           signal_table.c.three_ins_bull_str_100,
                           signal_table.c.three_ins_bull_str_120,
                           signal_table.c.three_out_bull_str_3,
                           signal_table.c.three_out_bull_str_5,
                           signal_table.c.three_out_bull_str_10,
                           signal_table.c.three_out_bull_str_15,
                           signal_table.c.three_out_bull_str_20,
                           signal_table.c.three_out_bull_str_40,
                           signal_table.c.three_out_bull_str_60,
                           signal_table.c.three_out_bull_str_80,
                           signal_table.c.three_out_bull_str_100,
                           signal_table.c.three_out_bull_str_120,
                           signal_table.c.belt_bull_str_3,
                           signal_table.c.belt_bull_str_5,
                           signal_table.c.belt_bull_str_10,
                           signal_table.c.belt_bull_str_15,
                           signal_table.c.belt_bull_str_20,
                           signal_table.c.belt_bull_str_40,
                           signal_table.c.belt_bull_str_60,
                           signal_table.c.belt_bull_str_80,
                           signal_table.c.belt_bull_str_100,
                           signal_table.c.belt_bull_str_120,
                           signal_table.c.harami_bull_str_3,
                           signal_table.c.harami_bull_str_5,
                           signal_table.c.harami_bull_str_10,
                           signal_table.c.harami_bull_str_15,
                           signal_table.c.harami_bull_str_20,
                           signal_table.c.harami_bull_str_40,
                           signal_table.c.harami_bull_str_60,
                           signal_table.c.harami_bull_str_80,
                           signal_table.c.harami_bull_str_100,
                           signal_table.c.harami_bull_str_120,
                           signal_table.c.harami_cross_bull_str_3,
                           signal_table.c.harami_cross_bull_str_5,
                           signal_table.c.harami_cross_bull_str_10,
                           signal_table.c.harami_cross_bull_str_15,
                           signal_table.c.harami_cross_bull_str_20,
                           signal_table.c.harami_cross_bull_str_40,
                           signal_table.c.harami_cross_bull_str_60,
                           signal_table.c.harami_cross_bull_str_80,
                           signal_table.c.harami_cross_bull_str_100,
                           signal_table.c.harami_cross_bull_str_120,
                           signal_table.c.inv_hammer_str_3,
                           signal_table.c.inv_hammer_str_5,
                           signal_table.c.inv_hammer_str_10,
                           signal_table.c.inv_hammer_str_15,
                           signal_table.c.inv_hammer_str_20,
                           signal_table.c.inv_hammer_str_40,
                           signal_table.c.inv_hammer_str_60,
                           signal_table.c.inv_hammer_str_80,
                           signal_table.c.inv_hammer_str_100,
                           signal_table.c.inv_hammer_str_120,
                           signal_table.c.piercing_line_str_3,
                           signal_table.c.piercing_line_str_5,
                           signal_table.c.piercing_line_str_10,
                           signal_table.c.piercing_line_str_15,
                           signal_table.c.piercing_line_str_20,
                           signal_table.c.piercing_line_str_40,
                           signal_table.c.piercing_line_str_60,
                           signal_table.c.piercing_line_str_80,
                           signal_table.c.piercing_line_str_100,
                           signal_table.c.piercing_line_str_120,
                           signal_table.c.doji_star_bull_str_3,
                           signal_table.c.doji_star_bull_str_5,
                           signal_table.c.doji_star_bull_str_10,
                           signal_table.c.doji_star_bull_str_15,
                           signal_table.c.doji_star_bull_str_20,
                           signal_table.c.doji_star_bull_str_40,
                           signal_table.c.doji_star_bull_str_60,
                           signal_table.c.doji_star_bull_str_80,
                           signal_table.c.doji_star_bull_str_100,
                           signal_table.c.doji_star_bull_str_120,
                           signal_table.c.homing_pigeon_str_3,
                           signal_table.c.homing_pigeon_str_5,
                           signal_table.c.homing_pigeon_str_10,
                           signal_table.c.homing_pigeon_str_15,
                           signal_table.c.homing_pigeon_str_20,
                           signal_table.c.homing_pigeon_str_40,
                           signal_table.c.homing_pigeon_str_60,
                           signal_table.c.homing_pigeon_str_80,
                           signal_table.c.homing_pigeon_str_100,
                           signal_table.c.homing_pigeon_str_120,
                           signal_table.c.kicking_bull_str_3,
                           signal_table.c.kicking_bull_str_5,
                           signal_table.c.kicking_bull_str_10,
                           signal_table.c.kicking_bull_str_15,
                           signal_table.c.kicking_bull_str_20,
                           signal_table.c.kicking_bull_str_40,
                           signal_table.c.kicking_bull_str_60,
                           signal_table.c.kicking_bull_str_80,
                           signal_table.c.kicking_bull_str_100,
                           signal_table.c.kicking_bull_str_120,
                           signal_table.c.hangman_str_3,
                           signal_table.c.hangman_str_5,
                           signal_table.c.hangman_str_10,
                           signal_table.c.hangman_str_15,
                           signal_table.c.hangman_str_20,
                           signal_table.c.hangman_str_40,
                           signal_table.c.hangman_str_60,
                           signal_table.c.hangman_str_80,
                           signal_table.c.hangman_str_100,
                           signal_table.c.hangman_str_120,
                           signal_table.c.engulf_bear_str_3,
                           signal_table.c.engulf_bear_str_5,
                           signal_table.c.engulf_bear_str_10,
                           signal_table.c.engulf_bear_str_15,
                           signal_table.c.engulf_bear_str_20,
                           signal_table.c.engulf_bear_str_40,
                           signal_table.c.engulf_bear_str_60,
                           signal_table.c.engulf_bear_str_80,
                           signal_table.c.engulf_bear_str_100,
                           signal_table.c.engulf_bear_str_120,
                           signal_table.c.three_crows_str_3,
                           signal_table.c.three_crows_str_5,
                           signal_table.c.three_crows_str_10,
                           signal_table.c.three_crows_str_15,
                           signal_table.c.three_crows_str_20,
                           signal_table.c.three_crows_str_40,
                           signal_table.c.three_crows_str_60,
                           signal_table.c.three_crows_str_80,
                           signal_table.c.three_crows_str_100,
                           signal_table.c.three_crows_str_120,
                           signal_table.c.evening_star_str_3,
                           signal_table.c.evening_star_str_5,
                           signal_table.c.evening_star_str_10,
                           signal_table.c.evening_star_str_15,
                           signal_table.c.evening_star_str_20,
                           signal_table.c.evening_star_str_40,
                           signal_table.c.evening_star_str_60,
                           signal_table.c.evening_star_str_80,
                           signal_table.c.evening_star_str_100,
                           signal_table.c.evening_star_str_120,
                           signal_table.c.three_ins_bear_str_3,
                           signal_table.c.three_ins_bear_str_5,
                           signal_table.c.three_ins_bear_str_10,
                           signal_table.c.three_ins_bear_str_15,
                           signal_table.c.three_ins_bear_str_20,
                           signal_table.c.three_ins_bear_str_40,
                           signal_table.c.three_ins_bear_str_60,
                           signal_table.c.three_ins_bear_str_80,
                           signal_table.c.three_ins_bear_str_100,
                           signal_table.c.three_ins_bear_str_120,
                           signal_table.c.three_out_bear_str_3,
                           signal_table.c.three_out_bear_str_5,
                           signal_table.c.three_out_bear_str_10,
                           signal_table.c.three_out_bear_str_15,
                           signal_table.c.three_out_bear_str_20,
                           signal_table.c.three_out_bear_str_40,
                           signal_table.c.three_out_bear_str_60,
                           signal_table.c.three_out_bear_str_80,
                           signal_table.c.three_out_bear_str_100,
                           signal_table.c.three_out_bear_str_120,
                           signal_table.c.belt_bear_str_3,
                           signal_table.c.belt_bear_str_5,
                           signal_table.c.belt_bear_str_10,
                           signal_table.c.belt_bear_str_15,
                           signal_table.c.belt_bear_str_20,
                           signal_table.c.belt_bear_str_40,
                           signal_table.c.belt_bear_str_60,
                           signal_table.c.belt_bear_str_80,
                           signal_table.c.belt_bear_str_100,
                           signal_table.c.belt_bear_str_120,
                           signal_table.c.harami_bear_str_3,
                           signal_table.c.harami_bear_str_5,
                           signal_table.c.harami_bear_str_10,
                           signal_table.c.harami_bear_str_15,
                           signal_table.c.harami_bear_str_20,
                           signal_table.c.harami_bear_str_40,
                           signal_table.c.harami_bear_str_60,
                           signal_table.c.harami_bear_str_80,
                           signal_table.c.harami_bear_str_100,
                           signal_table.c.harami_bear_str_120,
                           signal_table.c.harami_cross_bear_str_3,
                           signal_table.c.harami_cross_bear_str_5,
                           signal_table.c.harami_cross_bear_str_10,
                           signal_table.c.harami_cross_bear_str_15,
                           signal_table.c.harami_cross_bear_str_20,
                           signal_table.c.harami_cross_bear_str_40,
                           signal_table.c.harami_cross_bear_str_60,
                           signal_table.c.harami_cross_bear_str_80,
                           signal_table.c.harami_cross_bear_str_100,
                           signal_table.c.harami_cross_bear_str_120,
                           signal_table.c.shooting_star_str_3,
                           signal_table.c.shooting_star_str_5,
                           signal_table.c.shooting_star_str_10,
                           signal_table.c.shooting_star_str_15,
                           signal_table.c.shooting_star_str_20,
                           signal_table.c.shooting_star_str_40,
                           signal_table.c.shooting_star_str_60,
                           signal_table.c.shooting_star_str_80,
                           signal_table.c.shooting_star_str_100,
                           signal_table.c.shooting_star_str_120,
                           signal_table.c.dark_cloud_str_3,
                           signal_table.c.dark_cloud_str_5,
                           signal_table.c.dark_cloud_str_10,
                           signal_table.c.dark_cloud_str_15,
                           signal_table.c.dark_cloud_str_20,
                           signal_table.c.dark_cloud_str_40,
                           signal_table.c.dark_cloud_str_60,
                           signal_table.c.dark_cloud_str_80,
                           signal_table.c.dark_cloud_str_100,
                           signal_table.c.dark_cloud_str_120,
                           signal_table.c.doji_star_bear_str_3,
                           signal_table.c.doji_star_bear_str_5,
                           signal_table.c.doji_star_bear_str_10,
                           signal_table.c.doji_star_bear_str_15,
                           signal_table.c.doji_star_bear_str_20,
                           signal_table.c.doji_star_bear_str_40,
                           signal_table.c.doji_star_bear_str_60,
                           signal_table.c.doji_star_bear_str_80,
                           signal_table.c.doji_star_bear_str_100,
                           signal_table.c.doji_star_bear_str_120,
                           signal_table.c.sma_pos_5_20,
                           signal_table.c.sma_neg_5_20,
                           signal_table.c.sma_cross_5_20_delta,
                           signal_table.c.sma_pos_20_50,
                           signal_table.c.sma_neg_20_50,
                           signal_table.c.sma_cross_20_50_delta,
                           signal_table.c.volume_crossover,
                           signal_table.c.vol_delta,
                           signal_table.c.ADX_14day,
                           signal_table.c.stoch_cross_20,
                           signal_table.c.stoch_cross_80,
                           signal_table.c.stoch_cross_delta]).where(signal_table.c.securities_id.in_(sec_id)).where(signal_table.c.price_date.between(s_date, e_date))

        db_result = self.CONN.execute(get_data)
        df = pd.DataFrame(db_result.fetchall())
        
        if len(df):
            df.columns = db_result.keys()

            if len(data_list):
                j = df.columns.isin(data_list)
                df = df.loc[:,j]
                df.set_index('price_date', inplace=True)
                df.sort(inplace=True)
                return(df)

            else:
                df.set_index('price_date', inplace=True)
                df.sort(inplace=True)              
                return(df)

        else:
            return(pd.DataFrame())
