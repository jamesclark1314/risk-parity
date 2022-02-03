# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 23:54:25 2022

@author: James Clark
"""

import pandas as pd
import math
import matplotlib.pyplot as plt

pd.set_option('display.max_columns', None)

treasury = pd.read_csv('CRSP_TreasuriesIndex_Monthly.csv')
stock_index = pd.read_csv('CRSP_StockIndex_Monthly.csv')
ff3factor = pd.read_csv('FF3Factors_Monthly-1.csv')

# Set a Datetime Index & Change Date Format to Include Only Year & Month
stock_index['Datetime'] = pd.to_datetime(stock_index['Date']).apply(
    lambda x: x.strftime('%Y-%m'))
stock_index = stock_index.set_index(['Datetime'])

treasury['Datetime'] = pd.to_datetime(treasury['Date']).apply(
    lambda x: x.strftime('%Y-%m'))
treasury = treasury.set_index(['Datetime'])

ff3factor['Datetime'] = pd.to_datetime(ff3factor['Date']).apply(
    lambda x: x.strftime('%Y-%m'))
ff3factor = ff3factor.set_index(['Datetime'])

# Drop Dates
del stock_index['Date']
del treasury['Date']
del ff3factor['Date']

ff3factor = ff3factor.div(100)

# Merge the Dataframes
dataframe = stock_index.merge(treasury, how = 'left', 
                                  left_index = True, right_index = True)
dataframe = dataframe.merge(ff3factor, how = 'left', 
                                  left_index = True, right_index = True)

dataframe.columns = ['Stocks', 'Bonds', 'Mkt-RF', 'SMB', 'HML', 'RF']

# Drop Rows Before 1927-01
dataframe = dataframe.drop(dataframe.index[range(12)])

dataframe['ER Stock'] = dataframe['Stocks'] - dataframe['RF']
dataframe['ER Bond'] = dataframe['Bonds'] - dataframe['RF']

# Standard Deviation of Stock & Bond Indices
dataframe['Stdev Stock'] = dataframe['ER Stock'].shift(1).rolling(
    window = 36).std() * math.sqrt(12)
dataframe['Stdev Bond'] = dataframe['ER Bond'].shift(1).rolling(
    window = 36).std() * math.sqrt(12)

# 3- Benchmark

# Calculate 60/40 Portfolio
weight_stock = 0.6
weight_bond = 0.4

dataframe['60/40 Rets'] = dataframe['ER Stock'].loc[
    '1930-01':] * weight_stock + dataframe['ER Bond'].loc['1930-01':] * weight_bond

# 4- Risk Parity Portfolios

# Unlevered RP Portfolio
Kt = 1/((1/dataframe['Stdev Stock']) + (1/dataframe['Stdev Bond']))
percent_stock = (1/dataframe['Stdev Stock']) * Kt
percent_bond = (1/dataframe['Stdev Bond']) * Kt

Kt = Kt.rename('Kt')
percent_stock = percent_stock.rename('percent_stock')
percent_bond = percent_bond.rename('percent_bond')

unlevered = Kt.to_frame().join(percent_stock)
unlevered = unlevered.merge(percent_bond, how = 'left', 
                                  left_index = True, right_index = True)

unlevered['Excess Rets'] = (unlevered['percent_stock'] * dataframe[
    'ER Stock']) + (unlevered['percent_bond'] * dataframe['ER Bond'])

# Levered RP Portfolio 1
k1 = dataframe['ER Stock'].loc['1930-01':].std() * math.sqrt(12)

k1_kt = k1/unlevered['Kt']
percent_stock1 = k1 * (1/dataframe['Stdev Stock'])
percent_bond1 = k1 * (1/dataframe['Stdev Bond'])

k1_kt = k1_kt.rename('k1/Kt')
percent_stock1 = percent_stock1.rename('percent_stock1')
percent_bond1 = percent_bond1.rename('percent_bond1')

levered1 = k1_kt.to_frame().join(percent_stock1)
levered1 = levered1.merge(percent_bond1, how = 'left', 
                                  left_index = True, right_index = True)

levered1['Excess Rets 1'] = levered1['percent_stock1'] * dataframe[
    'ER Stock'] + levered1['percent_bond1'] * dataframe['ER Bond']

# Levered RP Portfolio 2
k2 = dataframe['60/40 Rets'].loc['1930-01':].std() * math.sqrt(12)
k2_kt = k2/unlevered['Kt']
percent_stock2 = k2 * (1/dataframe['Stdev Stock'])
percent_bond2 = k2 * (1/dataframe['Stdev Bond'])

k2_kt = k2_kt.rename('k2/Kt')
percent_stock2 = percent_stock2.rename('percent_stock2')
percent_bond2 = percent_bond2.rename('percent_bond2')

levered2 = k2_kt.to_frame().join(percent_stock2)
levered2 = levered2.merge(percent_bond2, how = 'left', 
                                  left_index = True, right_index = True)

levered2['Excess Rets 2'] = levered2['percent_stock2'] * dataframe[
    'ER Stock'] + levered2['percent_bond2'] * dataframe['ER Bond']

# 6

merged = dataframe.merge(unlevered, how = 'left', 
                                  left_index = True, right_index = True)
merged = merged.merge(levered1, how = 'left', 
                                  left_index = True, right_index = True)
merged = merged.merge(levered2, how = 'left', 
                                  left_index = True, right_index = True)

# Function that slices the data by date
def thing(start, end):
    frame = merged[start:end]
    
    # Means
    sxty_fty_mean = frame['60/40 Rets'].mean() * 12
    all_stock_mean = frame['ER Stock'].mean() * 12
    unlevered_mean = frame['Excess Rets'].mean() * 12
    levered1_mean = frame['Excess Rets 1'].mean() * 12
    levered2_mean = frame['Excess Rets 2'].mean() * 12
    
    # Stdev
    sxty_fty_stdev = frame['60/40 Rets'].std() * math.sqrt(12)
    all_stock_stdev = frame['ER Stock'].std() * math.sqrt(12)
    unlevered_stdev = frame['Excess Rets'].std() * math.sqrt(12)
    levered1_stdev = frame['Excess Rets 1'].std() * math.sqrt(12)
    levered2_stdev = frame['Excess Rets 2'].std() * math.sqrt(12)
    
    # Average Stock Allocation
    unlevered_wt_s = frame['percent_stock'].mean()
    levered1_wt_s = frame['percent_stock1'].mean()
    levered2_wt_s = frame['percent_stock2'].mean()
    
    # Average Bond Allocation
    unlevered_wt_b = frame['percent_bond'].mean()
    levered1_wt_b = frame['percent_bond1'].mean()
    levered2_wt_b = frame['percent_bond2'].mean()
    
    # Dataframe
    data = {'Mean':[sxty_fty_mean, all_stock_mean, unlevered_mean, levered1_mean, levered2_mean],
             'Stdev':[sxty_fty_stdev, all_stock_stdev, unlevered_stdev, levered1_stdev, levered2_stdev],
             'Sharpe':[sxty_fty_mean/sxty_fty_stdev, 
                       all_stock_mean/all_stock_stdev,
                       unlevered_mean/unlevered_stdev,
                       levered1_mean/levered1_stdev,
                       levered2_mean/levered2_stdev],
             'Avg Stock Wt':[weight_stock, 1, unlevered_wt_s, levered1_wt_s, levered2_wt_s],
             'Avg Bond Wt':[weight_bond, 0, unlevered_wt_b, levered1_wt_b, levered2_wt_b]}
    
    global stats_period_x
    
    stats_period_x = pd.DataFrame(data, index = ['60/40 ' + start + ' - ' + end,
                                         'All Stock ' + start + ' - ' + end,
                                         'Unlevered ' + start + ' - ' + end,
                                         'Levered1 ' + start + ' - ' + end,
                                         'Levered2 ' + start + ' - ' + end,])
    
    # Plotted Sharpe Ratios
    stats_period_x.plot.bar(y = 'Sharpe')
    plt.title('Sharpe Ratios ' + start + ' to ' + end)
    plt.show()

    return stats_period_x

print('')
print('                     Statistics for Designated Period')
print('')
print(thing('1930-01', '2019-12'))

# Output to CSV Files
dataframe.to_csv('Data and 60-40 Portfolio.csv')
unlevered.to_csv('Unlevered Portfolio.csv')
levered1.to_csv('Levered RP 1 Portfolio.csv')
levered2.to_csv('Levered RP 2 Portfolio.csv')
merged.to_csv('Full Merged Dataframe.csv')











