import pandas as pd
import pandas_ta as pda
import ta


# =======================================
#        GENERATION DES INDICATEURS
# =======================================
def load_indicators(dfList, dfListSorted, indicators, showLog=False):
    # On récupère les paramètres des indicateurs spécifiés dans le fichier parametres.cfg
    trixLength = int(indicators['trixlength'])
    trixSignal = int(indicators['trixsignal'])
    RSI_WINDOWS = int(indicators['rsi_windows'])
    BB_WINDOWS_BULL = int(indicators['bb_windows_bull'])
    BB_WINDOWS_DEV_BULL = float(indicators['bb_windows_dev_bull'])
    BB_WINDOWS_BEAR = int(indicators['bb_windows_bear'])
    BB_WINDOWS_DEV_BEAR = float(indicators['bb_windows_dev_bear'])
    parametrePVO_BEAR = int(indicators['parametrepvo_bear'])
    parametrePVO_BULL = int(indicators['parametrepvo_bull'])
    parametrePERF_BULL = int(indicators['parametreperf_bull'])
    parametrePERF_BEAR = int(indicators['parametreperf_bear'])
    parametrePVO2 = int(indicators['parametrepvo2'])
    parametreADXV_BULL = float(indicators['parametreadxv_bull'])
    parametreADXV_BEAR = float(indicators['parametreadxv_bear'])
    parametreTRIX_HISTO_BULL = float(indicators['parametretrix_histo_bull'])
    parametreTRIX_HISTO_BEAR = float(indicators['parametretrix_histo_bear'])
    parametreSTOCH_RSI_BULL = float(indicators['parametrestoch_rsi_bull'])
    parametreSTOCH_RSI_BEAR = float(indicators['parametrestoch_rsi_bear'])
    parametreSTOCH_RSI2_BULL = float(indicators['parametrestoch_rsi2_bull'])
    parametreSTOCH_RSI2_BEAR = float(indicators['parametrestoch_rsi2_bear'])
    parametreTRIX_HISTO2_BULL = float(indicators['parametretrix_histo2_bull'])
    parametreTRIX_HISTO2_BEAR = float(indicators['parametretrix_histo2_bear'])

    for perpSymbol in dfList:
        try :
            dfList[perpSymbol]['EMA10']=ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=10)
            dfList[perpSymbol]['EMA50']=ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=50)
            dfList[perpSymbol]['EMA45']=ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=45)
            #dfList[perpSymbol]['EMA10']=ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=10)
            #dfList[perpSymbol]['EMA22']=ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=22)
            dfList[perpSymbol]['EMA9D']=ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=216)
            dfList[perpSymbol]['EMA13D']=ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=312)
            dfList[perpSymbol]['EMA45D']=ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=24*45)
            dfList[perpSymbol]['EMA100']=ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=100)
            
            #Plus bas prix atteint par la crypto depuis les 30 dernières bougies
            dfList[perpSymbol]["ATL 30"] = dfList[perpSymbol]["low"].rolling(30).min()
            dfList[perpSymbol]["ATL 72h"] = dfList[perpSymbol]["ATL 30"].rolling(72).agg(lambda rows: rows[0])
            
            dfList[perpSymbol]["Prix 24h"] = dfList[perpSymbol]["close"].rolling(24).agg(lambda rows: rows[0])
            dfList[perpSymbol]["Prix 8h"] = dfList[perpSymbol]["close"].rolling(8).agg(lambda rows: rows[0])
            
            dfList[perpSymbol]['TRIX'] = ta.trend.ema_indicator(ta.trend.ema_indicator(ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=trixLength), window=trixLength), window=trixLength)
            dfList[perpSymbol]['TRIX_PCT'] = dfList[perpSymbol]["TRIX"].pct_change()*100
            dfList[perpSymbol]['TRIX_SIGNAL'] = ta.trend.sma_indicator(dfList[perpSymbol]['TRIX_PCT'],trixSignal)
            dfList[perpSymbol]['TRIX_HISTO'] = dfList[perpSymbol]['TRIX_PCT'] - dfList[perpSymbol]['TRIX_SIGNAL']
            
            kst = ta.trend.KSTIndicator(close=dfList[perpSymbol]['close'], roc1 = 10, roc2= 15, roc3 = 20, roc4 = 30, window1 = 10, window2 = 10, window3 = 10, window4 = 15, nsig = 9) 
            dfList[perpSymbol]['kst'] = kst.kst_sig()
            
            #MACD
            MACD = ta.trend.MACD(close=dfList[perpSymbol]['close'], window_fast=12, window_slow=26, window_sign=10)
            MACD1 = ta.trend.MACD(close=dfList[perpSymbol]['close'], window_fast=120, window_slow=260, window_sign=20)
            dfList[perpSymbol]['MACD_SIGNAL'] = MACD.macd_signal()
            dfList[perpSymbol]['MACD_SIGNAL1'] = MACD1.macd_signal()
            #dfList[perpSymbol]['MACD_DIFF'] = MACD.macd_diff() #Histogramme MACD
            
            # #Stochastic RSI
            dfList[perpSymbol]['STOCH_RSI'] = ta.momentum.stochrsi(close=dfList[perpSymbol]['close'], window=RSI_WINDOWS, smooth1=3, smooth2=3) #Non moyenné 
            dfList[perpSymbol]['STOCH_RSI_D'] = ta.momentum.stochrsi_d(close=dfList[perpSymbol]['close'], window=14, smooth1=3, smooth2=3) #Orange sur TradingView
            dfList[perpSymbol]['STOCH_RSI_K'] =ta.momentum.stochrsi_k(close=dfList[perpSymbol]['close'], window=14, smooth1=3, smooth2=3) #Bleu sur TradingView
            
            #Bollinger Bands
            BOL_BAND = ta.volatility.BollingerBands(close=dfList[perpSymbol]['close'], window=BB_WINDOWS_BEAR, window_dev=BB_WINDOWS_DEV_BEAR) 
            dfList[perpSymbol]['BOL_H_BAND'] = BOL_BAND.bollinger_hband_indicator() #Bande Supérieur
            dfList[perpSymbol]['BOL_L_BAND'] = BOL_BAND.bollinger_lband_indicator()
            BOL_BAND1 = ta.volatility.BollingerBands(close=dfList[perpSymbol]['close'], window=BB_WINDOWS_BULL, window_dev=BB_WINDOWS_DEV_BULL)
            
            dfList[perpSymbol]['BOL_L_BAND1'] = BOL_BAND1.bollinger_lband_indicator()
            
            #dfList[perpSymbol]['perf'] = o1.daily_return(dfList[perpSymbol]['close'])
            #dfList[perpSymbol]['perf'] = dfListSorted[perpSymbol]
            
            Keltner = ta.volatility.KeltnerChannel(dfList[perpSymbol]['high'], dfList[perpSymbol]['low'], dfList[perpSymbol]['close'], window = 10, window_atr = 10)
            dfList[perpSymbol]['Keltner'] = Keltner.keltner_channel_lband_indicator()
            
            Aroon = ta.trend.AroonIndicator(close=dfList[perpSymbol]['close'], window = 25)
            dfList[perpSymbol]['Aroonindicateur'] = Aroon.aroon_indicator()
            
            CCI = ta.trend.CCIIndicator(dfList[perpSymbol]['high'], dfList[perpSymbol]['low'], dfList[perpSymbol]['close'], window = 45, constant = 0.015)
            dfList[perpSymbol]['CCI'] = CCI.cci()
            
            #Average True Range (ATR)
            dfList[perpSymbol]['atr'] = ta.volatility.average_true_range(high=dfList[perpSymbol]['high'], low=dfList[perpSymbol]['low'], close=dfList[perpSymbol]['close'], window=14)

            dfList[perpSymbol]['AWESOME_OSCILLATOR'] = ta.momentum.awesome_oscillator(high=dfList[perpSymbol]['high'], low=dfList[perpSymbol]['low'], window1=5, window2=34)
            
            pvo = ta.momentum.PercentageVolumeOscillator(dfList[perpSymbol]['volume'], window_slow = 26, window_fast = 12, window_sign = parametrePVO_BEAR)
            dfList[perpSymbol]['pvo'] = pvo.pvo_hist()
            pvo1 = ta.momentum.PercentageVolumeOscillator(dfList[perpSymbol]['volume'], window_slow = 26, window_fast = 12, window_sign = parametrePVO_BULL)
            dfList[perpSymbol]['pvo1'] = pvo1.pvo_hist()
            
            #ADX
            ADX = ta.trend.ADXIndicator(dfList[perpSymbol]['high'], dfList[perpSymbol]['low'], dfList[perpSymbol]['close'], window=20)
            dfList[perpSymbol]['ADX'] = ADX.adx()
            dfList[perpSymbol]['ADX_NEG'] = ADX.adx_neg()
            dfList[perpSymbol]['ADX_POS'] = ADX.adx_pos()
            dfList[perpSymbol]['ADXV'] = dfList[perpSymbol]['ADX_POS'] - dfList[perpSymbol]['ADX_NEG']
        except Exception as err :
            print(f"Impossible de charger la paire : {perpSymbol} : {err}")
            pass
    return dfList

def getEvolution(row, previousRow):
    return float(row['close']-previousRow['close'])/previousRow['close']*100

def openLongCondition(row, previousRow, dfList, indicators):
    try:
        if (
            row['TRIX_HISTO'] >= float(indicators['parametretrix_histo_bear'])
            and row['STOCH_RSI'] < float(indicators['parametrestoch_rsi_bear'])
            and row['ADXV'] > float(indicators['parametreadxv_bear'])
            and row['EMA9D'] > row['EMA13D']
            and row['MACD_SIGNAL'] > previousRow['MACD_SIGNAL']
            and row['EMA50'] < row['EMA10']
            and row['EMA45'] < row['close']
            and row['Keltner'] < 1.0
            and row['kst'] < 500.0
        ):
            return True
        else:
            return False
    except Exception as err:
        print(err)
        return False


# -- Condition to close Market LONG --
def closeLongCondition(row, previousRow, dfList, indicators):
    try:
        if (
            (row['TRIX_HISTO'] < float(indicators['parametretrix_histo2_bear'])
            and row['STOCH_RSI'] > float(indicators['parametrestoch_rsi2_bear']))
            or row['BOL_L_BAND'] == 1
            or (row['Aroonindicateur'] < -84.0 and row['CCI'] > -80.0)
            or getEvolution(row, previousRow)<-10.0
        ):
            return True
        else:
            return False
    except Exception as err:
        print(err)
        return False

# -- Condition to open Market SHORT --
def openShortCondition(row, previousRow, dfList, indicators):
    try:
        if (
            row['TRIX_HISTO'] >= 0.0
            and row['STOCH_RSI'] > 0.85
            and row['ADXV'] < 0.5
            and row['EMA9D'] < row['EMA13D']
            and row['MACD_SIGNAL'] < previousRow['MACD_SIGNAL']
            and row['EMA50'] > row['EMA10']
            and row['EMA45'] > row['close']
        ):
            return True
        else:
            return False
    except:
        return False


# -- Condition to close Market SHORT --
def closeShortCondition(row, previousRow, dfList, indicators):
    try:
        if (
            (row['TRIX_HISTO'] > indicators['parametretrix_histo2_bear']
            and row['STOCH_RSI'] < indicators['parametrestoch_rsi2_bear'])
        ):
            return True
        else:
            return False
    except:
        return False

# -- Fonction to get the takeprofit price --
def getTakeprofit(position, prixAchat, row, previousRow, dfList, indicators):
    tpMultiplicator=float(indicators['tpmultiplicator'])
    if position=="long" :
        return float(prixAchat+tpMultiplicator*row["atr"])
    elif position=="short":
        return float(prixAchat-row["atr"]*tpMultiplicator)
    else :
        raise UnknowPositionType

# -- Fonction to get the stoploss price --
def getStoploss(position, prixAchat, row, previousRow, dfList, indicators):
    slMultiplicator=float(indicators['slmultiplicator'])
    if position=="long" :
        return prixAchat - (prixAchat / 2) * slMultiplicator
    elif position=="short":
        return prixAchat + (prixAchat / 2) * slMultiplicator
    else :
        raise UnknowPositionType
