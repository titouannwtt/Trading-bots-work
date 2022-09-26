import pandas as pd
import math
from datetime import datetime
import matplotlib.pyplot as plt
import random
import numpy as np
import seaborn as sns
import datetime

class Backtesting():

    def simple_spot_backtest_analys(self, dfTrades, dfTest, pairSymbol, timeframe):
        # -- BackTest Analyses --
        dfTrades = dfTrades.set_index(dfTrades['date'])
        dfTrades.index = pd.to_datetime(dfTrades.index)
        dfTrades['resultat'] = dfTrades['wallet'].diff()
        dfTrades['resultat%'] = dfTrades['wallet'].pct_change()*100
        dfTrades.loc[dfTrades['position'] == 'Buy', 'resultat'] = None
        dfTrades.loc[dfTrades['position'] == 'Buy', 'resultat%'] = None

        dfTrades['tradeIs'] = ''
        dfTrades.loc[dfTrades['resultat'] > 0, 'tradeIs'] = 'Good'
        dfTrades.loc[dfTrades['resultat'] <= 0, 'tradeIs'] = 'Bad'

        dfTrades['walletAth'] = dfTrades['wallet'].cummax()
        dfTrades['drawDown'] = dfTrades['walletAth'] - dfTrades['wallet']
        dfTrades['drawDownPct'] = dfTrades['drawDown'] / dfTrades['walletAth']

        wallet = dfTrades.iloc[-1]['wallet']
        iniClose = dfTest.iloc[0]['close']
        lastClose = dfTest.iloc[len(dfTest)-1]['close']
        holdPercentage = ((lastClose - iniClose)/iniClose) * 100
        initalWallet = dfTrades.iloc[0]['wallet']
        algoPercentage = ((wallet - initalWallet)/initalWallet) * 100
        holdFinalWallet = initalWallet + initalWallet*(holdPercentage/100)
        vsHoldPercentage = ((wallet/holdFinalWallet)-1)*100

        try:
            tradesPerformance = round(dfTrades.loc[(dfTrades['tradeIs'] == 'Good') | (dfTrades['tradeIs'] == 'Bad'), 'resultat%'].sum()
                                      / dfTrades.loc[(dfTrades['tradeIs'] == 'Good') | (dfTrades['tradeIs'] == 'Bad'), 'resultat%'].count(), 2)
        except:
            tradesPerformance = 0
            print(
                "/!\ There is no Good or Bad Trades in your BackTest, maybe a problem...")

        try:
            totalGoodTrades = len(dfTrades.loc[dfTrades['tradeIs'] == 'Good'])
            AveragePercentagePositivTrades = round(dfTrades.loc[dfTrades['tradeIs'] == 'Good', 'resultat%'].sum()
                                                    / totalGoodTrades, 2)
            idbest = dfTrades.loc[dfTrades['tradeIs']
                                    == 'Good', 'resultat%'].idxmax()
            bestTrade = str(
                round(dfTrades.loc[dfTrades['tradeIs'] == 'Good', 'resultat%'].max(), 2))
        except:
            totalGoodTrades = 0
            AveragePercentagePositivTrades = 0
            idbest = ''
            bestTrade = 0
            print("/!\ There is no Good Trades in your BackTest, maybe a problem...")

        try:
            totalBadTrades = len(dfTrades.loc[dfTrades['tradeIs'] == 'Bad'])
            AveragePercentageNegativTrades = round(dfTrades.loc[dfTrades['tradeIs'] == 'Bad', 'resultat%'].sum()
                                                    / totalBadTrades, 2)
            idworst = dfTrades.loc[dfTrades['tradeIs']
                                    == 'Bad', 'resultat%'].idxmin()
            worstTrade = round(
                dfTrades.loc[dfTrades['tradeIs'] == 'Bad', 'resultat%'].min(), 2)
        except:
            totalBadTrades = 0
            AveragePercentageNegativTrades = 0
            idworst = ''
            worstTrade = 0
            print("/!\ There is no Bad Trades in your BackTest, maybe a problem...")

        totalTrades = totalBadTrades + totalGoodTrades
        winRateRatio = (totalGoodTrades/totalTrades) * 100

        try:
            dfTrades['timeDeltaTrade'] = dfTrades["timeSince"]
            dfTrades['timeDeltaNoTrade'] = dfTrades['timeDeltaTrade']
            dfTrades.loc[dfTrades['position'] ==
                         'Buy', 'timeDeltaTrade'] = None
            dfTrades.loc[dfTrades['position'] ==
                         'Sell', 'timeDeltaNoTrade'] = None
        except:
            print("/!\ Error in time delta")
            dfTrades['timeDeltaTrade'] = 0
            dfTrades['timeDeltaNoTrade'] = 0

        reasons = dfTrades['reason'].unique()

        print("Pair Symbol :", pairSymbol, '| Timeframe :', timeframe)
        print("Period : [" + str(dfTest.index[0]) + "] -> [" +
              str(dfTest.index[len(dfTest)-1]) + "]")
        print("Starting balance :", initalWallet, "$")

        print("\n----- General Informations -----")
        print("Final balance :", round(wallet, 2), "$")
        print("Performance vs US Dollar :", round(algoPercentage, 2), "%")
        print("Buy and Hold Performence :", round(holdPercentage, 2), "%")
        print("Performance vs Buy and Hold :", round(vsHoldPercentage, 2), "%")
        print("Best trade : +"+bestTrade, "%, the", idbest)
        print("Worst trade :", worstTrade, "%, the", idworst)
        print("Worst drawDown : -", str(
            round(100*dfTrades['drawDownPct'].max(), 2)), "%")
        print("Total fees : ", round(dfTrades['frais'].sum(), 2), "$")

        print("\n----- Trades Informations -----")
        print("Total trades on period :", totalTrades)
        print("Number of positive trades :", totalGoodTrades)
        print("Number of negative trades : ", totalBadTrades)
        print("Trades win rate ratio :", round(winRateRatio, 2), '%')
        print("Average trades performance :", tradesPerformance, "%")
        print("Average positive trades :", AveragePercentagePositivTrades, "%")
        print("Average negative trades :", AveragePercentageNegativTrades, "%")

        print("\n----- Time Informations -----")
        print("Average time duration for a trade :", round(
            dfTrades['timeDeltaTrade'].mean(skipna=True), 2), "periods")
        print("Maximum time duration for a trade :",
              dfTrades['timeDeltaTrade'].max(skipna=True), "periods")
        print("Minimum time duration for a trade :",
              dfTrades['timeDeltaTrade'].min(skipna=True), "periods")
        print("Average time duration between two trades :", round(
            dfTrades['timeDeltaNoTrade'].mean(skipna=True), 2), "periods")
        print("Maximum time duration between two trades :",
              dfTrades['timeDeltaNoTrade'].max(skipna=True), "periods")
        print("Minimum time duration between two trades :",
              dfTrades['timeDeltaNoTrade'].min(skipna=True), "periods")

        print("\n----- Trades Reasons -----")
        reasons = dfTrades['reason'].unique()
        for r in reasons:
            print(r+" number :", dfTrades.groupby('reason')
                  ['date'].nunique()[r])

        return dfTrades

    def multi_spot_backtest_analys(self, dfTrades, dfTest, pairList, timeframe):
        # -- BackTest Analyses --
        dfTrades = dfTrades.set_index(dfTrades['date'])
        dfTrades.index = pd.to_datetime(dfTrades.index)
        dfTrades['resultat'] = dfTrades['wallet'].diff()
        dfTrades['resultat%'] = dfTrades['wallet'].pct_change()*100
        dfTrades.loc[dfTrades['position'] == 'Buy', 'resultat'] = None
        dfTrades.loc[dfTrades['position'] == 'Buy', 'resultat%'] = None

        dfTrades['tradeIs'] = ''
        dfTrades.loc[dfTrades['resultat'] > 0, 'tradeIs'] = 'Good'
        dfTrades.loc[dfTrades['resultat'] <= 0, 'tradeIs'] = 'Bad'

        dfTrades['walletAth'] = dfTrades['wallet'].cummax()
        dfTrades['drawDown'] = dfTrades['walletAth'] - dfTrades['wallet']
        dfTrades['drawDownPct'] = dfTrades['drawDown'] / dfTrades['walletAth']

        wallet = dfTrades.iloc[-1]['wallet']
        iniClose = dfTest.iloc[0]['close']
        lastClose = dfTest.iloc[len(dfTest)-1]['close']
        holdPercentage = ((lastClose - iniClose)/iniClose) * 100
        initalWallet = dfTrades.iloc[0]['wallet']
        algoPercentage = ((wallet - initalWallet)/initalWallet) * 100
        holdFinalWallet = initalWallet + initalWallet*(holdPercentage/100)
        vsHoldPercentage = ((wallet/holdFinalWallet)-1)*100

        try:
            tradesPerformance = round(dfTrades.loc[(dfTrades['tradeIs'] == 'Good') | (dfTrades['tradeIs'] == 'Bad'), 'resultat%'].sum()
                                        / dfTrades.loc[(dfTrades['tradeIs'] == 'Good') | (dfTrades['tradeIs'] == 'Bad'), 'resultat%'].count(), 2)
        except:
            tradesPerformance = 0
            print(
                "/!\ There is no Good or Bad Trades in your BackTest, maybe a problem...")

        try:
            totalGoodTrades = len(dfTrades.loc[dfTrades['tradeIs'] == 'Good'])
            AveragePercentagePositivTrades = round(dfTrades.loc[dfTrades['tradeIs'] == 'Good', 'resultat%'].sum()
                                                    / totalGoodTrades, 2)
            idbest = dfTrades.loc[dfTrades['tradeIs']
                                    == 'Good', 'resultat%'].idxmax()
            bestTrade = str(
                round(dfTrades.loc[dfTrades['tradeIs'] == 'Good', 'resultat%'].max(), 2))
        except:
            totalGoodTrades = 0
            AveragePercentagePositivTrades = 0
            idbest = ''
            bestTrade = 0
            print("/!\ There is no Good Trades in your BackTest, maybe a problem...")

        try:
            totalBadTrades = len(dfTrades.loc[dfTrades['tradeIs'] == 'Bad'])
            AveragePercentageNegativTrades = round(dfTrades.loc[dfTrades['tradeIs'] == 'Bad', 'resultat%'].sum()
                                                    / totalBadTrades, 2)
            idworst = dfTrades.loc[dfTrades['tradeIs']
                                    == 'Bad', 'resultat%'].idxmin()
            worstTrade = round(
                dfTrades.loc[dfTrades['tradeIs'] == 'Bad', 'resultat%'].min(), 2)
        except:
            totalBadTrades = 0
            AveragePercentageNegativTrades = 0
            idworst = ''
            worstTrade = 0
            print("/!\ There is no Bad Trades in your BackTest, maybe a problem...")

        totalTrades = totalBadTrades + totalGoodTrades
        winRateRatio = (totalGoodTrades/totalTrades) * 100


        print("Trading Bot on :", len(pairList), 'coins | Timeframe :', timeframe)
        print("Period : [" + str(dfTest.index[0]) + "] -> [" +
                str(dfTest.index[len(dfTest)-1]) + "]")
        print("Starting balance :", initalWallet, "$")

        print("\n----- General Informations -----")
        print("Final balance :", round(wallet, 2), "$")
        print("Performance vs US Dollar :", round(algoPercentage, 2), "%")
        print("Bitcoin Buy and Hold Performence :", round(holdPercentage, 2), "%")
        print("Performance vs Buy and Hold :", round(vsHoldPercentage, 2), "%")
        print("Best trade : +"+bestTrade, "%, the", idbest)
        print("Worst trade :", worstTrade, "%, the", idworst)
        print("Worst drawDown : -", str(
            round(100*dfTrades['drawDownPct'].max(), 2)), "%")
        print("Total fees : ", round(dfTrades['frais'].sum(), 2), "$")

        print("\n----- Trades Informations -----")
        print("Total trades on period :", totalTrades)
        print("Number of positive trades :", totalGoodTrades)
        print("Number of negative trades : ", totalBadTrades)
        print("Trades win rate ratio :", round(winRateRatio, 2), '%')
        print("Average trades performance :", tradesPerformance, "%")
        print("Average positive trades :", AveragePercentagePositivTrades, "%")
        print("Average negative trades :", AveragePercentageNegativTrades, "%")

        print("\n----- Trades Reasons -----")
        print(dfTrades['reason'].value_counts())

        print("\n----- Pair Result -----")
        dash = '-' * 95
        print(dash)
        print('{:<6s}{:>10s}{:>15s}{:>15s}{:>15s}{:>15s}{:>15s}'.format(
            "Trades","Pair","Sum-result","Mean-trade","Worst-trade","Best-trade","Win-rate"
            ))
        print(dash)
        for pair in pairList:
            try:
                dfPairLoc = dfTrades.loc[dfTrades['symbol'] == pair, 'resultat%']
                pairGoodTrade = len(dfTrades.loc[(dfTrades['symbol'] == pair) & (dfTrades['resultat%'] > 0)])
                pairTotalTrade = int(len(dfPairLoc)/2)
                pairResult = str(round(dfPairLoc.sum(),2))+' %'
                pairAverage = str(round(dfPairLoc.mean(),2))+' %'
                pairMin = str(round(dfPairLoc.min(),2))+' %'
                pairMax = str(round(dfPairLoc.max(),2))+' %'
                pairWinRate = str(round(100*(pairGoodTrade/pairTotalTrade),2))+' %'
                print('{:<6d}{:>10s}{:>15s}{:>15s}{:>15s}{:>15s}{:>15s}'.format(
                    pairTotalTrade,pair,pairResult,pairAverage,pairMin,pairMax,pairWinRate
                ))
            except:
                pass

        return dfTrades

    def get_result_by_month(self, dfTrades):
        lastMonth = int(dfTrades.iloc[-1]['date'].month)
        lastYear = int(dfTrades.iloc[-1]['date'].year)
        dfTrades = dfTrades.set_index(dfTrades['date'])
        dfTrades.index = pd.to_datetime(dfTrades.index)
        myMonth = int(dfTrades.iloc[0]['date'].month)
        myYear = int(dfTrades.iloc[0]['date'].year)
        while myYear != lastYear or myMonth != lastMonth:
            myString = str(myYear) + "-" + str(myMonth)
            try:
                myResult = (dfTrades.loc[myString].iloc[-1]['wallet'] -
                            dfTrades.loc[myString].iloc[0]['wallet'])/dfTrades.loc[myString].iloc[0]['wallet']
            except:
                myResult = 0
            print(myYear, myMonth, round(myResult*100, 2), "%")
            if myMonth < 12:
                myMonth += 1
            else:
                myMonth = 1
                myYear += 1

        myString = str(lastYear) + "-" + str(lastMonth)
        try:
            myResult = (dfTrades.loc[myString].iloc[-1]['wallet'] -
                        dfTrades.loc[myString].iloc[0]['wallet'])/dfTrades.loc[myString].iloc[0]['wallet']
        except:
            myResult = 0
        print(lastYear, lastMonth, round(myResult*100, 2), "%")

    def get_n_columns(df, columns, n=1):
        dt = df.copy()
        for col in columns:
            dt["n"+str(n)+"_"+col] = dt[col].shift(n)
        return dt


    def plot_wallet_vs_price(self, dfTrades):
        dfTrades = dfTrades.set_index(dfTrades['date'])
        dfTrades.index = pd.to_datetime(dfTrades.index)
        dfTrades[['wallet', 'price']].plot(subplots=True, figsize=(20, 10))
        print("\n----- Plot -----")

    def plot_wallet_evolution(self, dfTrades):
        dfTrades = dfTrades.set_index(dfTrades['date'])
        dfTrades.index = pd.to_datetime(dfTrades.index)
        dfTrades['wallet'].plot(figsize=(20, 10))
        print("\n----- Plot -----")

    def plot_bar_by_month(self, dfTrades):
        sns.set(rc={'figure.figsize':(11.7,8.27)})
        lastMonth = int(dfTrades.iloc[-1]['date'].month)
        lastYear = int(dfTrades.iloc[-1]['date'].year)
        dfTrades = dfTrades.set_index(dfTrades['date'])
        dfTrades.index = pd.to_datetime(dfTrades.index)
        myMonth = int(dfTrades.iloc[0]['date'].month)
        myYear = int(dfTrades.iloc[0]['date'].year)
        custom_palette = {}
        dfTemp = pd.DataFrame([])
        while myYear != lastYear or myMonth != lastMonth:
            myString = str(myYear) + "-" + str(myMonth)
            try:
                myResult = (dfTrades.loc[myString].iloc[-1]['wallet'] -
                            dfTrades.loc[myString].iloc[0]['wallet'])/dfTrades.loc[myString].iloc[0]['wallet']
            except:
                myResult = 0
            myrow = {
                'date': str(datetime.date(1900, myMonth, 1).strftime('%B')),
                'result': round(myResult*100)
            }
            dfTemp = dfTemp.append(myrow, ignore_index=True)
            if myResult >= 0:
                custom_palette[str(datetime.date(1900, myMonth, 1).strftime('%B'))] = 'g'
            else:
                custom_palette[str(datetime.date(1900, myMonth, 1).strftime('%B'))] = 'r'
            # print(myYear, myMonth, round(myResult*100, 2), "%")
            if myMonth < 12:
                myMonth += 1
            else:
                g = sns.barplot(data=dfTemp,x='date',y='result', palette=custom_palette)
                for index, row in dfTemp.iterrows():
                    if row.result >= 0:
                        g.text(row.name,row.result, '+'+str(round(row.result))+'%', color='black', ha="center", va="bottom")
                    else:
                        g.text(row.name,row.result, '-'+str(round(row.result))+'%', color='black', ha="center", va="top")
                g.set_title(str(myYear) + ' performance in %')
                g.set(xlabel=myYear, ylabel='performance %')
                yearResult = (dfTrades.loc[str(myYear)].iloc[-1]['wallet'] -
                            dfTrades.loc[str(myYear)].iloc[0]['wallet'])/dfTrades.loc[str(myYear)].iloc[0]['wallet']
                print("----- " + str(myYear) +" Performances: " + str(round(yearResult*100,2)) + "% -----")
                plt.show()
                dfTemp = pd.DataFrame([])
                myMonth = 1
                myYear += 1

        myString = str(lastYear) + "-" + str(lastMonth)
        try:
            myResult = (dfTrades.loc[myString].iloc[-1]['wallet'] -
                        dfTrades.loc[myString].iloc[0]['wallet'])/dfTrades.loc[myString].iloc[0]['wallet']
        except:
            myResult = 0
        g = sns.barplot(data=dfTemp,x='date',y='result', palette=custom_palette)
        for index, row in dfTemp.iterrows():
            if row.result >= 0:
                g.text(row.name,row.result, '+'+str(round(row.result))+'%', color='black', ha="center", va="bottom")
            else:
                g.text(row.name,row.result, '-'+str(round(row.result))+'%', color='black', ha="center", va="top")
        g.set_title(str(myYear) + ' performance in %')
        g.set(xlabel=myYear, ylabel='performance %')
        yearResult = (dfTrades.loc[str(myYear)].iloc[-1]['wallet'] -
                dfTrades.loc[str(myYear)].iloc[0]['wallet'])/dfTrades.loc[str(myYear)].iloc[0]['wallet']
        print("----- " + str(myYear) +" Performances: " + str(round(yearResult*100,2)) + "% -----")
        plt.show()

    def past_simulation(
            self, 
            dfTrades, 
            numberOfSimulation = 100,
            lastTrainDate = "2021-06",
            firstPlottedDate = "2021-07",
            firstSimulationDate = "2021-07-15",
            trainMultiplier = 1
        ):
        dfTrades = dfTrades.set_index(dfTrades['date'])
        dfTrades.index = pd.to_datetime(dfTrades.index)
        dfTrades['resultat'] = dfTrades['wallet'].diff()
        dfTrades['resultat%'] = dfTrades['wallet'].pct_change()
        dfTrades = dfTrades.loc[dfTrades['position']=='Sell','resultat%']
        dfTrades = dfTrades + 1

        suimulationResult = []
        trainSeries = dfTrades.loc[:lastTrainDate]
        startedPlottedDate = firstPlottedDate
        startedSimulationDate = firstSimulationDate
        commonPlot = dfTrades.copy().loc[startedPlottedDate:startedSimulationDate]
        simulatedTradesLength = len(dfTrades.loc[startedSimulationDate:])
        for i in range(numberOfSimulation):
            dfTemp = dfTrades.copy().loc[startedPlottedDate:]
            newTrades = random.sample(list(trainSeries)*trainMultiplier, simulatedTradesLength)
            dfTemp.iloc[-simulatedTradesLength:] = newTrades
            dfTemp = dfTemp.cumprod()
            dfTemp.plot(figsize=(20, 10))
            suimulationResult.append(dfTemp.iloc[-1])

        dfTemp = dfTrades.copy().loc[startedPlottedDate:]
        dfTemp = dfTemp.cumprod()
        dfTemp.plot(figsize=(20, 10), linewidth=8)
        trueResult = dfTemp.iloc[-1]
        suimulationResult.append(trueResult)
        suimulationResult.sort()
        resultPosition = suimulationResult.index(trueResult)
        resultPlacePct = round((resultPosition/len(suimulationResult))*100,2)
        maxSimulationResult = round((max(suimulationResult)-1)*100,2)
        minSimulationResult = round((min(suimulationResult)-1)*100,2)
        avgSimulationResult = round(((sum(suimulationResult)/len(suimulationResult))-1)*100,2)
        initialStrategyResult = round((trueResult-1)*100,2)

        print("Train data informations :",len(trainSeries),"trades on period [" + str(trainSeries.index[0]) + "] -> [" +
              str(trainSeries.index[len(trainSeries)-1]) + "]")
        print("The strategy is placed at",resultPlacePct,"% of all simulations")
        print("You strategy make +",initialStrategyResult,"%")
        print("The average simulation was at +",avgSimulationResult,"%")
        print("The best simulation was at +",maxSimulationResult,"%")
        print("The worst simulation was at +",minSimulationResult,"%")
        print("--- PLOT ---")

    def get_metrics(self, df_trades, df_days):
        df_days_copy = df_days.copy()
        df_days_copy['evolution'] = df_days_copy['wallet'].diff()
        df_days_copy['daily_return'] = df_days_copy['evolution']/df_days_copy['wallet'].shift(1)
        sharpe_ratio = (365**0.5)*(df_days_copy['daily_return'].mean()/df_days_copy['daily_return'].std())
        
        df_days_copy['wallet_ath'] = df_days_copy['wallet'].cummax()
        df_days_copy['drawdown'] = df_days_copy['wallet_ath'] - df_days_copy['wallet']
        df_days_copy['drawdown_pct'] = df_days_copy['drawdown'] / df_days_copy['wallet_ath']
        max_drawdown = -df_days_copy['drawdown_pct'].max() * 100
        
        df_trades_copy = df_trades.copy()
        df_trades_copy['trade_result'] = df_trades_copy["close_trade_size"] - df_trades_copy["open_trade_size"] - df_trades_copy["open_fee"] - df_trades_copy["close_fee"]
        df_trades_copy['trade_result_pct'] = df_trades_copy['trade_result']/df_trades_copy["open_trade_size"]
        good_trades = df_trades_copy.loc[df_trades_copy['trade_result_pct'] > 0]
        win_rate = len(good_trades) / len(df_trades)
        avg_profit = df_trades_copy['trade_result_pct'].mean()
        
        return {
            "sharpe_ratio": sharpe_ratio,
            "win_rate": win_rate,
            "avg_profit": avg_profit,
            "total_trades": len(df_trades_copy),
            "max_drawdown": max_drawdown
        }

    def basic_single_asset_backtest(trades, days):
        df_trades = trades.copy()
        df_days = days.copy()
        
        df_days['evolution'] = df_days['wallet'].diff()
        df_days['daily_return'] = df_days['evolution']/df_days['wallet'].shift(1)
        
        df_trades['trade_result'] = df_trades["close_trade_size"] - df_trades["open_trade_size"] - df_trades["open_fee"]
        df_trades['trade_result_pct'] = df_trades['trade_result']/df_trades["open_trade_size"]
        
        df_trades['wallet_ath'] = df_trades['wallet'].cummax()
        df_trades['drawdown'] = df_trades['wallet_ath'] - df_trades['wallet']
        df_trades['drawdown_pct'] = df_trades['drawdown'] / df_trades['wallet_ath']
        df_days['wallet_ath'] = df_days['wallet'].cummax()
        df_days['drawdown'] = df_days['wallet_ath'] - df_days['wallet']
        df_days['drawdown_pct'] = df_days['drawdown'] / df_days['wallet_ath']
        
        good_trades = df_trades.loc[df_trades['trade_result'] > 0]
        
        initial_wallet = df_days.iloc[0]["wallet"]
        total_trades = len(df_trades)
        total_good_trades = len(good_trades)
        avg_profit = df_trades['trade_result_pct'].mean()   
        global_win_rate = total_good_trades / total_trades
        max_trades_drawdown = df_trades['drawdown_pct'].max()
        max_days_drawdown = df_days['drawdown_pct'].max()
        final_wallet = df_days.iloc[-1]['wallet']
        buy_and_hold_pct = (df_days.iloc[-1]['price'] - df_days.iloc[0]['price']) / df_days.iloc[0]['price']
        buy_and_hold_wallet = initial_wallet + initial_wallet * buy_and_hold_pct
        vs_hold_pct = (final_wallet - buy_and_hold_wallet)/buy_and_hold_wallet
        vs_usd_pct = (final_wallet - initial_wallet)/initial_wallet
        sharpe_ratio = (365**0.5)*(df_days['daily_return'].mean()/df_days['daily_return'].std())
        
        best_trade = df_trades['trade_result_pct'].max()
        best_trade_date1 =  str(df_trades.loc[df_trades['trade_result_pct'] == best_trade].iloc[0]['open_date'])
        best_trade_date2 =  str(df_trades.loc[df_trades['trade_result_pct'] == best_trade].iloc[0]['close_date'])
        worst_trade = df_trades['trade_result_pct'].min()
        worst_trade_date1 =  str(df_trades.loc[df_trades['trade_result_pct'] == worst_trade].iloc[0]['open_date'])
        worst_trade_date2 =  str(df_trades.loc[df_trades['trade_result_pct'] == worst_trade].iloc[0]['close_date'])
        
        print("Period: [{}] -> [{}]".format(df_days.iloc[0]["day"], df_days.iloc[-1]["day"]))
        print("Initial wallet: {} $".format(round(initial_wallet,2)))
        
        print("\n--- General Information ---")
        print("Final wallet: {} $".format(round(final_wallet,2)))
        print("Performance vs US dollar: {} %".format(round(vs_usd_pct*100,2)))
        print("Sharpe Ratio: {}".format(round(sharpe_ratio,2)))
        print("Worst Drawdown T|D: -{}% | -{}%".format(round(max_trades_drawdown*100, 2), round(max_days_drawdown*100, 2)))
        print("Buy and hold performance: {} %".format(round(buy_and_hold_pct*100,2)))
        print("Performance vs buy and hold: {} %".format(round(vs_hold_pct*100,2)))
        print("Total trades on the period: {}".format(total_trades))
        print("Global Win rate: {} %".format(round(global_win_rate*100, 2)))
        print("Average Profit: {} %".format(round(avg_profit*100, 2)))
        
        print("\nBest trades: +{} % the {} -> {}".format(round(best_trade*100, 2), best_trade_date1, best_trade_date2))
        print("Worst trades: {} % the {} -> {}".format(round(worst_trade*100, 2), worst_trade_date1, worst_trade_date2))

        return df_trades, df_days

    def basic_multi_asset_backtest(trades, days):
        df_trades = trades.copy()
        df_days = days.copy()
        
        df_days['evolution'] = df_days['wallet'].diff()
        df_days['daily_return'] = df_days['evolution']/df_days['wallet'].shift(1)
       
        
        df_trades = df_trades.copy()
        df_trades['trade_result'] = df_trades["close_trade_size"] - df_trades["open_trade_size"] - df_trades["open_fee"] - df_trades["close_fee"]
        df_trades['trade_result_pct'] = df_trades['trade_result']/(df_trades["open_trade_size"] + df_trades["open_fee"])
        #df_trades['trade_result_pct_pos'] = df_trades['trade_result_pct'] > 0
        
        #good_trades = df_trades.loc[df_trades['trade_result_pct'] > 0]
        good_trades = df_trades[df_trades['trade_result_pct'] > 0]["trade_result_pct"]
        bad_trades = df_trades[df_trades['trade_result_pct'] <= 0]["trade_result_pct"]
        #bad_trades = df_trades.loc[df_trades['trade_result_pct'] < 0]
        #avg_win = good_trades.mean()
        #avg_lose = bad_trades.mean()

        #if  df_trades['trade_result_pct'] > 0:
        #    df_trades['good_trade'] = df_trades['trade_result_pct']
        #else:
        #    df_trades['bad_trade'] = df_trades['trade_result_pct']
        
        df_trades['wallet_ath'] = df_trades['wallet'].cummax()
        df_trades['drawdown'] = df_trades['wallet_ath'] - df_trades['wallet']
        df_trades['drawdown_pct'] = df_trades['drawdown'] / df_trades['wallet_ath']
        df_days['wallet_ath'] = df_days['wallet'].cummax()
        df_days['drawdown'] = df_days['wallet_ath'] - df_days['wallet']
        df_days['drawdown_pct'] = df_days['drawdown'] / df_days['wallet_ath']
        
        #good_trades = df_trades.loc[df_trades['trade_result'] > 0]
        
        total_pair_traded = df_trades['pair'].nunique()
        initial_wallet = df_days.iloc[0]["wallet"]
        total_trades = len(df_trades)
        total_good_trades = len(good_trades)
        avg_profit = df_trades['trade_result_pct'].mean()  
        avg_win = good_trades.mean()  
        avg_lose =  bad_trades.mean()  
        global_win_rate = total_good_trades / total_trades
        max_trades_drawdown = df_trades['drawdown_pct'].max()
        max_days_drawdown = df_days['drawdown_pct'].max()
        final_wallet = df_days.iloc[-1]['wallet']
        buy_and_hold_pct = (df_days.iloc[-1]['price'] - df_days.iloc[0]['price']) / df_days.iloc[0]['price']
        buy_and_hold_wallet = initial_wallet + initial_wallet * buy_and_hold_pct
        vs_hold_pct = (final_wallet - buy_and_hold_wallet)/buy_and_hold_wallet
        vs_usd_pct = (final_wallet - initial_wallet)/initial_wallet
        sharpe_ratio = (365**0.5)*(df_days['daily_return'].mean()/df_days['daily_return'].std())
        
        print("Period: [{}] -> [{}]".format(df_days.iloc[0]["day"], df_days.iloc[-1]["day"]))
        print("Initial wallet: {} $".format(round(initial_wallet,2)))
        print("Trades on {} pairs".format(total_pair_traded))
        
        print("\n--- General Information ---")
        print("Final wallet: {} $".format(round(final_wallet,2)))
        print("Performance vs US dollar: {} %".format(round(vs_usd_pct*100,2)))
        print("Sharpe Ratio: {}".format(round(sharpe_ratio,2)))
        print("Worst Drawdown T|D: -{}% | -{}%".format(round(max_trades_drawdown*100, 2), round(max_days_drawdown*100, 2)))
        print("Buy and hold performance: {} %".format(round(buy_and_hold_pct*100,2)))
        print("Performance vs buy and hold: {} %".format(round(vs_hold_pct*100,2)))
        print("Total trades on the period: {}".format(total_trades))
        print("Global Win rate: {} %".format(round(global_win_rate*100, 2)))
        print("Average Profit: {} %".format(round(avg_profit*100, 2)))
        print("Average Win Profit: {} %".format(round(avg_win*100, 2)))
        print("Average Lose Profit: {} %".format(round(avg_lose*100, 2)))

        


        
        print("\n----- Pair Result -----")
        print('-' * 95)
        print('{:<6s}{:>10s}{:>15s}{:>15s}{:>15s}{:>15s}{:>15s}{:>15s}{:>15s}'.format(
                    "Trades","Pair","Sum-result","Mean-trade","Worst-trade","Best-trade","Win-rate","Avg-Win","Avg-Lose"
                    ))
        print('-' * 95)
        for pair in df_trades["pair"].unique():
            df_pair = df_trades.loc[df_trades["pair"] == pair]
            pair_total_trades = len(df_pair)
            pair_good_trades = len(df_pair.loc[df_pair["trade_result"] > 0])
            pair_bad_trades = len(df_pair.loc[df_pair["trade_result"] <= 0])
            pair_worst_trade = str(round(df_pair["trade_result_pct"].min() * 100, 2))+' %'
            pair_best_trade = str(round(df_pair["trade_result_pct"].max() * 100, 2))+' %'
            pair_win_rate = str(round((pair_good_trades / pair_total_trades) * 100, 2))+' %'
            pair_sum_result = str(round(df_pair["trade_result_pct"].sum() * 100, 2))+' %'
            pair_avg_result = str(round(df_pair["trade_result_pct"].mean() * 100, 2))+' %'
            pair_avg_result_pos = str(round((df_pair.loc[df_pair["trade_result_pct"] > 0]["trade_result_pct"]).mean() * 100, 2))+' %'
            pair_avg_result_neg = str(round((df_pair.loc[df_pair["trade_result_pct"] <= 0]["trade_result_pct"]).mean() * 100, 2))+' %'
            print('{:<6d}{:>10s}{:>15s}{:>15s}{:>15s}{:>15s}{:>15s}{:>15s}{:>15s}'.format(
                                pair_total_trades,pair,pair_sum_result,pair_avg_result,pair_worst_trade,pair_best_trade,pair_win_rate,pair_avg_result_pos, pair_avg_result_neg
                            ))
        
            
        return df_trades, df_days
    
    def plot_wallet_vs_asset(df_days):
        fig, axes = plt.subplots(figsize=(15, 12), nrows=2, ncols=1)
        df_days['wallet'].plot(ax=axes[0])
        df_days['price'].plot(ax=axes[1], color='orange')