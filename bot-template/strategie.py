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

            # Indicateur EMA_SHORT (avec paramètres pour l'indicateur)
            dfList[perpSymbol]["ema_short"] = ta.trend.ema_indicator(
                close=dfList[perpSymbol]["close"], window=ema_short_windows
            )
            # Indicateur EMA_LONG (avec paramètres pour l'indicateur)
            dfList[perpSymbol]["ema_long"] = ta.trend.ema_indicator(
                close=dfList[perpSymbol]["close"], window=ema_long_windows
            )
            # Indicateur EMA10
            dfList[perpSymbol]["EMA10"] = ta.trend.ema_indicator(
                close=dfList[perpSymbol]["close"], window=10
            )
            # Indicateur EMA 9 Jours
            dfList[perpSymbol]["ema9d"] = ta.trend.ema_indicator(
                close=dfList[perpSymbol]["close"], window=216
            )
            # Indicateur EMA 50
            dfList[perpSymbol]["ema50"] = ta.trend.ema_indicator(
                close=dfList[perpSymbol]["close"], window=50
            )
            # Indicateur EMA Trend (2000)
            dfList[perpSymbol]["ema_trend"] = ta.trend.ema_indicator(
                close=dfList[perpSymbol]["close"], window=2000
            )

            # Indicateur SuperTrend (avec paramètres pour l'indicateur)
            superTrend = pda.supertrend(
                dfList[perpSymbol]["high"],
                dfList[perpSymbol]["low"],
                dfList[perpSymbol]["close"],
                length=ST_length,
                multiplier=ST_multiplier,
            )
            dfList[perpSymbol]["SUPER_TREND"] = superTrend[
                "SUPERT_" + str(ST_length) + "_" + str(ST_multiplier)
            ]
            dfList[perpSymbol]["sp"] = superTrend[
                "SUPERTd_" + str(ST_length) + "_" + str(ST_multiplier)
            ]

            # Indicateur Average True Range (ATR)
            dfList[perpSymbol]["atr"] = ta.volatility.average_true_range(
                high=dfList[perpSymbol]["high"],
                low=dfList[perpSymbol]["low"],
                close=dfList[perpSymbol]["close"],
                window=14,
            )

            # Indicateur Kama
            dfList[perpSymbol]["kama"] = ta.momentum.kama(
                close=dfList[perpSymbol]["close"], window=10, pow1=2, pow2=30
            )

            # Indicateur PSAR
            PSAR = ta.trend.PSARIndicator(
                dfList[perpSymbol]["high"],
                dfList[perpSymbol]["low"],
                dfList[perpSymbol]["close"],
                step=0.2,
                max_step=0.2,
            )
            dfList[perpSymbol]["psar"] = PSAR.psar()

            # Indicateur ADX
            ADX = ta.trend.ADXIndicator(
                dfList[perpSymbol]["high"],
                dfList[perpSymbol]["low"],
                dfList[perpSymbol]["close"],
                window=20,
            )
            dfList[perpSymbol]["ADX"] = ADX.adx()
            dfList[perpSymbol]["ADX_NEG"] = ADX.adx_neg()
            dfList[perpSymbol]["ADX_POS"] = ADX.adx_pos()
            dfList[perpSymbol]["adx"] = (
                dfList[perpSymbol]["ADX_POS"] - dfList[perpSymbol]["ADX_NEG"]
            )

            # Indicateurs PVO
            pvo = ta.momentum.PercentageVolumeOscillator(
                dfList[perpSymbol]["volume"],
                window_slow=26,
                window_fast=12,
                window_sign=18,
            )
            dfList[perpSymbol]["pvo"] = pvo.pvo_hist()

            pvo2 = ta.momentum.PercentageVolumeOscillator(
                dfList[perpSymbol]["volume"],
                window_slow=26,
                window_fast=12,
                window_sign=10,
            )
            dfList[perpSymbol]["pvo2"] = pvo2.pvo_hist()

            # Indicateur MFI
            vol = ta.volume.MFIIndicator(
                dfList[perpSymbol]["high"],
                dfList[perpSymbol]["low"],
                dfList[perpSymbol]["close"],
                dfList[perpSymbol]["volume"],
                window=14,
            )
            dfList[perpSymbol]["vol"] = vol.money_flow_index()

            # Indicateurs MACD
            MACD2 = ta.trend.MACD(
                close=dfList[perpSymbol]["close"],
                window_fast=120,
                window_slow=260,
                window_sign=20,
            )
            dfList[perpSymbol]["macd2"] = MACD2.macd_diff()

            MACD = ta.trend.MACD(
                close=dfList[perpSymbol]["close"],
                window_fast=12,
                window_slow=26,
                window_sign=10,
            )
            dfList[perpSymbol]["macd"] = MACD.macd_diff()

            # Indicateur KST
            kst = ta.trend.KSTIndicator(
                close=dfList[perpSymbol]["close"],
                roc1=10,
                roc2=15,
                roc3=20,
                roc4=30,
                window1=10,
                window2=10,
                window3=10,
                window4=15,
                nsig=9,
            )
            dfList[perpSymbol]["kst"] = kst.kst_diff()

            # Indicateur TRIX
            trixLength = 8
            trixSignal = 21
            dfList[perpSymbol]["TRIX"] = ta.trend.ema_indicator(
                ta.trend.ema_indicator(
                    ta.trend.ema_indicator(
                        close=dfList[perpSymbol]["close"], window=trixLength
                    ),
                    window=trixLength,
                ),
                window=trixLength,
            )
            dfList[perpSymbol]["TRIX_PCT"] = (
                dfList[perpSymbol]["TRIX"].pct_change() * 100
            )
            dfList[perpSymbol]["TRIX_SIGNAL"] = ta.trend.sma_indicator(
                dfList[perpSymbol]["TRIX_PCT"], trixSignal
            )
            dfList[perpSymbol]["trix"] = (
                dfList[perpSymbol]["TRIX_PCT"] - dfList[perpSymbol]["TRIX_SIGNAL"]
            )

            # Plus bas prix atteint par la crypto depuis les 300 dernières bougies
            dfList[perpSymbol]["ATL 300"] = dfList[perpSymbol]["low"].rolling(300).min()

            # Indicateur Aroon
            Aroon = ta.trend.AroonIndicator(
                close=dfList[perpSymbol]["close"], window=25
            )
            dfList[perpSymbol]["aroon"] = Aroon.aroon_indicator()

            # Indicateur Awesome Oscillator
            dfList[perpSymbol]["ao"] = ta.momentum.awesome_oscillator(
                high=dfList[perpSymbol]["high"],
                low=dfList[perpSymbol]["low"],
                window1=5,
                window2=34,
            )

            # Indicateur STOCH_RSI
            dfList[perpSymbol]["stochrsi"] = ta.momentum.stochrsi(
                close=dfList[perpSymbol]["close"], window=14, smooth1=3, smooth2=3
            )

            # print(f"Chargement de la paire : {perpSymbol}")
        except:
            print(f"Impossible de charger la paire : {perpSymbol}")
            pass
    return dfList


# -- Condition to open Market SHORT --
def openShortCondition(row, previousRow, dfList, indicators):
    try:
        if row["macd"] < 0 and row["EMA10"] < row["ema50"]:
            return True
        else:
            return False
    except:
        return False


# -- Condition to close Market SHORT --
def closeShortCondition(row, previousRow, dfList, indicators):
    try:
        if (
            row["psar"] < row["close"]
            and row["kst"] > -0.5
            and row["trix"] > 0.02
            and row["stochrsi"] < 0.99
        ):
            return True
        else:
            return False
    except:
        return False


def openLongCondition(row, previousRow, dfList, indicators):
    try:
        if row["macd"] > 0 and row["EMA10"] > row["ema50"]:
            return True
        else:
            return False
    except:
        return False


# -- Condition to close Market LONG --
def closeLongCondition(row, previousRow, dfList, indicators):
    try:
        if (
            row["kst"] < 0
            or row["vol"] > 80
            or row["trix"] < 0
            or row["EMA10"] < row["ema50"]
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
