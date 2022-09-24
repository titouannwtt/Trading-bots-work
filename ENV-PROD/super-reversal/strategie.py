import pandas as pd
import pandas_ta as pda
import ta


# =======================================
#        GENERATION DES INDICATEURS
# =======================================
def load_indicators(dfList, dfListSorted, indicators):
    # On récupère les paramètres des indicateurs spécifiés dans le fichier parametres.cfg
    ST_length = int(indicators["ST_length"])
    ST_multiplier = float(indicators["ST_multiplier"])
    ema_short_windows = int(indicators["ema_short_windows"])
    ema_long_windows = int(indicators["ema_long_windows"])

    for perpSymbol in dfList:
        try:
            superTrend = pda.supertrend(dfList[perpSymbol]['high'], dfList[perpSymbol]['low'], dfList[perpSymbol]['close'], length=ST_length, multiplier=ST_multiplier)
            dfList[perpSymbol]['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
            dfList[perpSymbol]['sp'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]
            dfList[perpSymbol]['ema_short'] = ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=ema_short_windows)
            dfList[perpSymbol]['ema_long'] = ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=ema_long_windows)
            dfList[perpSymbol]['atr'] = ta.volatility.average_true_range(high=dfList[perpSymbol]['high'], low=dfList[perpSymbol]['low'], close=dfList[perpSymbol]['close'], window=14)
            
            dfList[perpSymbol]['ema9d']=ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=216)
            dfList[perpSymbol]['ema50']=ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=50)
            dfList[perpSymbol]['ema_trend'] = ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=2000)
            dfList[perpSymbol]['kama'] = ta.momentum.kama(close=dfList[perpSymbol]['close'], window=10, pow1=2, pow2=30)
            PSAR = ta.trend.PSARIndicator(dfList[perpSymbol]['high'], dfList[perpSymbol]['low'], dfList[perpSymbol]['close'], step = 0.2, max_step = 0.2)
            dfList[perpSymbol]['psar'] = PSAR.psar()
                    
            ADX = ta.trend.ADXIndicator(dfList[perpSymbol]['high'], dfList[perpSymbol]['low'], dfList[perpSymbol]['close'], window=20)
            dfList[perpSymbol]['ADX'] = ADX.adx()
            dfList[perpSymbol]['ADX_NEG'] = ADX.adx_neg()
            dfList[perpSymbol]['ADX_POS'] = ADX.adx_pos()
            dfList[perpSymbol]['adx'] = dfList[perpSymbol]['ADX_POS'] - dfList[perpSymbol]['ADX_NEG']
            pvo2 = ta.momentum.PercentageVolumeOscillator(dfList[perpSymbol]['volume'], window_slow = 26, window_fast = 12, window_sign = 10)
            dfList[perpSymbol]['pvo2'] = pvo2.pvo_hist()
            vol = ta.volume.MFIIndicator(dfList[perpSymbol]['high'], dfList[perpSymbol]['low'], dfList[perpSymbol]['close'], dfList[perpSymbol]['volume'], window = 14)
            dfList[perpSymbol]['vol'] = vol.money_flow_index()
            pvo = ta.momentum.PercentageVolumeOscillator(dfList[perpSymbol]['volume'], window_slow = 26, window_fast = 12, window_sign = 18)
            dfList[perpSymbol]['pvo'] = pvo.pvo_hist()
            MACD2 = ta.trend.MACD(close=dfList[perpSymbol]['close'], window_fast=120, window_slow=260, window_sign=20)
            dfList[perpSymbol]['macd2'] = MACD2.macd_diff()
            MACD = ta.trend.MACD(close=dfList[perpSymbol]['close'], window_fast=12, window_slow=26, window_sign=10)
            dfList[perpSymbol]['macd'] = MACD.macd_diff()
            kst = ta.trend.KSTIndicator(close=dfList[perpSymbol]['close'], roc1 = 10, roc2= 15, roc3 = 20, roc4 = 30, window1 = 10, window2 = 10, window3 = 10, window4 = 15, nsig = 9) 
            dfList[perpSymbol]['kst'] = kst.kst_diff()
            trixLength = 8
            trixSignal = 21
            dfList[perpSymbol]['TRIX'] = ta.trend.ema_indicator(ta.trend.ema_indicator(ta.trend.ema_indicator(close=dfList[perpSymbol]['close'], window=trixLength), window=trixLength), window=trixLength)
            dfList[perpSymbol]['TRIX_PCT'] = dfList[perpSymbol]["TRIX"].pct_change()*100
            dfList[perpSymbol]['TRIX_SIGNAL'] = ta.trend.sma_indicator(dfList[perpSymbol]['TRIX_PCT'],trixSignal)
            dfList[perpSymbol]['trix'] = dfList[perpSymbol]['TRIX_PCT'] - dfList[perpSymbol]['TRIX_SIGNAL']
            #Plus bas prix atteint par la crypto depuis les 300 dernières bougies
            dfList[perpSymbol]["ATL 300"] = dfList[perpSymbol]["low"].rolling(300).min()
            Aroon = ta.trend.AroonIndicator(close=dfList[perpSymbol]['close'], window = 25)
            dfList[perpSymbol]['aroon'] = Aroon.aroon_indicator()
            dfList[perpSymbol]['ao'] = ta.momentum.awesome_oscillator(high=dfList[perpSymbol]['high'], low=dfList[perpSymbol]['low'], window1=5, window2=34)
            
            dfList[perpSymbol]['stochrsi'] = ta.momentum.stochrsi(close=dfList[perpSymbol]['close'], window=14, smooth1=3, smooth2=3)
        except Exception as err :
            print(f"Impossible de charger la paire : {perpSymbol} : {err}")
            pass
    return dfList


# -- Condition to open Market SHORT --
def openShortCondition(row, previousRow, dfList, indicators):
    try:
        if (
            row['ema_short'] <= row['ema_long']
            and row['sp'] == -1
            and row['ema_short'] > row['close']
            and btcOk(dfList)==True
            and row['stochrsi'] < 0.812
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
            (row['ema_short'] >= row['ema_long']
            or row['sp'] == 1)
            and row['ema_short'] > row['close']
        ):
            return True
        else:
            return False
    except:
        return False


def openLongCondition(row, previousRow, dfList, indicators):
    try:
        if (
            row['ema_short'] >= row['ema_long']
            and row['sp'] == 1
            and row['ema_short'] > row['low']
            and (
                row['psar'] < 62322
                or row['close']/row['kama'] > 0.94
                or row['close']/row['kama'] < 1.22
                or row['close']/row['ema9d'] > 0.9356831
                or row['close']/row['ema9d'] < 1.6449085
                or row['close']/row['ema50'] < 1.2205431
                or row['close']/row['ema50'] > 0.9474454
                or row['close']/row['ema300'] < 1.9092231
                or row['close']/row['Prix moyen 600'] < 1.8799226
                or row['close']/row['Prix moyen 600'] > 0.9170606
                or row['close']/row['Prix moyen 1100'] > 2.5754199
                or row['adx'] < 52.8820860
                or row['pvo2'] > 50 or row['pvo2'] < -23.5
                or row['vol'] == 100
                or row['pvo'] < -25 or row['pvo'] > 85
                or row['macd2'] < -171 or row['macd2'] > 287
                or row['macd'] < -208 or row['macd'] > 450
                or row['kst'] > 192.8 or row['kst'] <-75.9
                or row['close']/row['trix']<-899485.8347299  or row['close']/row['trix']>18889998
                or row['close']/row['ATL 300'] > 5.3405263
                or row['atr'] < 0.0000139 or row['atr'] > 1318.9067468
                or row['aroon'] == -92.0
                or row['ao'] > 2491.3823529
                or row['adx'] < -19.4164236
            )
        ):
            return True
        else:
            return False
    except:
        return False


# -- Condition to close Market LONG --
def closeLongCondition(row, previousRow, dfList, indicators):
    try:
        if (
            (row['ema_short'] <= row['ema_long']
            or row['sp'] == -1)
            and row['ema_short'] < row['close']
        ):
            return True
        else:
            return False
    except:
        return False


def btcOk(dfList):
    if (
        dfList["BTC-PERP"].iloc[-2]["ema_trend"]
        > dfList["BTC-PERP"].iloc[-2]["close"] * 0.9875
    ):
        return True
    else:
        return False

# -- Fonction to get the takeprofit price --
def getTakeprofit(position, prixAchat, row, previousRow, dfList, indicators):
    tpMultiplicator=float(indicators['tpMultiplicator'])
    if position=="long" :
        return float(prixAchat+tpMultiplicator*row["atr"])
    elif position=="short":
        return float(prixAchat-row["atr"]*tpMultiplicator)
    else :
        raise UnknowPositionType

# -- Fonction to get the stoploss price --
def getStoploss(position, prixAchat, row, previousRow, dfList, indicators):
    slMultiplicator=float(indicators['slMultiplicator'])
    if position=="long" :
        return prixAchat - (prixAchat / 2) * slMultiplicator
    elif position=="short":
        return prixAchat + (prixAchat / 2) * slMultiplicator
    else :
        raise UnknowPositionType
