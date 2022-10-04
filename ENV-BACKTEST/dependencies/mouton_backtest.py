import configparser
import datetime
import json
import os
import sys
import traceback
import warnings
from datetime import datetime
from statistics import mean

import ccxt
import matplotlib.dates as mpl_dates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandas_ta as pda
import requests
import seaborn as sns
import ta
from finta import TA

import others as o1
from backtesting import Backtesting
from custom_indicators import CustomIndocators as ci
from data_engine import DataEngine

pd.options.mode.chained_assignment = None

warnings.simplefilter("ignore")


def str2bool(v):
    return v.lower() in ("true", "t", "1")


def getCryptoListFromDf(df, maxPairs: int):
    i = 0
    cryptoNameList = []
    for index, row in df.iterrows():
        if i <= maxPairs - 1:
            cryptoNameList.append(row["name"])
        i = i + 1
    return cryptoNameList


makerFrais = 0.0002
takerFrais = 0.0007


class Backtest:
    # Fonction permettant d'initialiser le backtest
    def __init__(
        self,
        start_date: str,
        end_date: str,
        strategy_name: str,
        forceDownload=False,
        downloadFrom2019=False,
        showLog=False,
        startingBalance=None,
    ):
        self.showLog = showLog
        self.start_date = start_date
        self.end_date = end_date
        self.forceDownload = forceDownload
        self.downloadFrom2019 = downloadFrom2019
        self.strategy_name = strategy_name
        self.startingBalance = startingBalance
        self.ohlc = None
        self.dfList = None
        self.parametres = None
        self.configs = None

    # =========================================
    # Fichier parametres.cfg

    # Pour prendre les paramètres par défaut dans parametres.cfg
    def load_params_from_cfg(self):
        if self.showLog == True:
            print("Récupérations des paramètres...")
        indicators = configparser.ConfigParser()
        indicators.read(
            [
                self.get_strategy_path() + "parametres.cfg",
                self.get_strategy_path() + "config-bot.cfg",
            ]
        )
        self.parametres = indicators["params"]
        return self.parametres

    # Pour imposer de nouveaux paramètres au backtest
    # Utile pour faire tourner un algorithme qui fait varier les paramètres
    def set_params(self, params):
        if self.showLog == True:
            print("Nouveaux paramètres définis.")
        self.parametres = params

    # Fonction permettant de récupérer les paramètres actuels du backtest
    # Exemple : print(self.get_params()['ema_size']) --> 50
    def get_params(self):
        if self.parametres == None:
            self.parametres = self.load_params_from_cfg()
        return self.parametres


    # =========================================
    # Fichier configs-bot.cfg

    def load_configs_from_cfg(self):
        if self.showLog == True:
            print("Récupérations des configurations...")
        configs = configparser.ConfigParser()
        configs.read(
            [
                self.get_strategy_path() + "parametres.cfg",
                self.get_strategy_path() + "config-bot.cfg",
            ]
        )
        self.configs = configs
        return self.configs

    def set_configs(self, configs):
        if self.showLog == True:
            print("Nouvelle configuration définie.")
        self.configs = configs

    def get_configs(self):
        if self.configs == None:
            self.configs = self.load_configs_from_cfg()
        return self.configs

    # =========================================

    # Permet de récupérer le dossier où se situe la stratégie de ce backtest
    # Exemple : /home/moutonneux/ENV-BACKTEST/super-reversal/
    def get_strategy_path(self):
        folder_name = str(self.strategy_name).split("/")[0]
        path = os.path.dirname(os.path.abspath(__file__)) + "/../" + folder_name + "/"
        return path

    # Fonction chargeant/téléchargeant les données du passés pour chaque crypto.
    def load_ohlc(
        self,
        start_date: str,
        end_date: str,
        forceDownload: bool,
        downloadFrom2019: bool,
    ):

        useWhitelist = str2bool(self.get_configs()["STRATEGIE"]["useWhitelist"])
        useBlacklist = str2bool(self.get_configs()["STRATEGIE"]["useBlacklist"])
        try:
            f = open(self.get_strategy_path() + "pair_list.json")
            pairJson = json.load(f)
            f.close()
        except Exception as err:
            print(
                f"Erreur lors de l'ouverture du fichier {self.get_strategy_path() + 'pair_list.json'} : {err}"
            )
            exit(5)
        if end_date == None:
            end_date = "aujourd'hui"
            useEndDate = False
        else:
            useEndDate = True
        timeframe = str(self.get_configs()["STRATEGIE"]["timeframe"])
        os.makedirs(
            self.get_strategy_path() + f"../dependencies/database/FTX/{timeframe}",
            exist_ok=True,
        )
        if self.showLog == True:
            print(
                f"Téléchargement des données en timeframe {timeframe} du {start_date} à {end_date}."
            )
        if useWhitelist == False:
            cryptoNameList = []
            try:
                liste_pairs = requests.get("https://ftx.com/api/futures").json()
            except Exception as err:
                print(f"Erreur lors de la récupération des données : {err}")
            dataResponse = liste_pairs["result"]
            df = pd.DataFrame(
                dataResponse,
                columns=["name", "perpetual", "marginPrice", "volume", "volumeUsd24h"],
            )
            df["volume"] = df["volume"] * df["marginPrice"]
            df.drop(df.loc[df["perpetual"] == False].index, inplace=True)
            df.sort_values(by="volume", ascending=False, inplace=True)
            cryptoNameList = getCryptoListFromDf(
                df, int(self.get_configs()["STRATEGIE"]["classementminimum"])
            )
        else:
            cryptoNameList = pairJson["whitelist"]
        if useBlacklist == True:
            for pair in pairJson["blacklist"]:
                if pair in cryptoNameList:
                    cryptoNameList.remove(pair)
                    if self.showLog == True:
                        print(
                            pair, "ne sera pas utilisée car appartient à la blacklist."
                        )
        if self.showLog == True:
            print(
                f"Les {len(cryptoNameList)} paires sélectionnées sont :\n {cryptoNameList}"
            )
        try:
            if self.showLog == True:
                print("Récupération des données FTX...")
            dataEngine = DataEngine(
                session=ccxt.ftx(), path_to_data="dependencies/database/"
            )
        except Exceptions as err:
            print(f"Erreur lors de la création de la session dataEngine : {err}")

        dfList = {}
        if downloadFrom2019 == True:
            date = "2019-07-20T00:00:00"
        else:
            date = start_date
        if forceDownload == True:
            for pair in cryptoNameList:
                timeframes = [f"{timeframe}"]
                pair_symbol = [f"{pair}"]
                dataEngine.download_data(pair_symbol, timeframes, date)
                df = None
                df = dataEngine.get_historical_from_db(pair, timeframe, date)
                if df is not None:
                    if self.showLog == True:
                        print(
                            f"Les données de {pair} en timeframe {timeframe} ont bien été récupérées sur l'API\n"
                        )
                else:
                    if self.showLog == True:
                        print(
                            f"Echec, on reessaye, peut être que l'API n'était pas joignable."
                        )
                    dataEngine.download_data(pair_symbol, timeframes, date)
                    df = dataEngine.get_historical_from_db(pair, timeframe, date)
                    if df is not None:
                        if self.showLog == True:
                            print(
                                f"Les données de {pair} en timeframe {timeframe} ont bien été récupérées sur l'API\n"
                            )
                    elif df is None:
                        print(
                            f"Les données de {pair} en timeframe {timeframe} n'ont pas été récupérées correctement sur l'API\n"
                        )
                if useEndDate == True:
                    dfList[pair] = df.loc[start_date:end_date]
                else:
                    dfList[pair] = df.loc[start_date]
        else:
            for pair in cryptoNameList:
                df = dataEngine.get_historical_from_db(pair, timeframe, start_date)
                if df is None or (df.empty == True):
                    if self.showLog == True:
                        print(
                            f"Données introuvables ou corrompues pour {pair} en timeframe {timeframe}, tentative de récupération sur l'API..."
                        )
                    # -- Download data from data variable --
                    timeframes = [f"{timeframe}"]
                    pair_symbol = [f"{pair}"]
                    dataEngine.download_data(pair_symbol, timeframes, date)
                    df = dataEngine.get_historical_from_db(pair, timeframe, date)
                    if df is not None:
                        if self.showLog == True:
                            print(
                                f"Les données de {pair} en timeframe {timeframe} ont bien été récupérées sur l'API\n"
                            )
                    elif df is None:
                        if self.showLog == True:
                            print(
                                f"Echec, on reessaye, peut être que l'API n'était pas joignable."
                            )
                        dataEngine.download_data(pair_symbol, timeframes, date)
                        df = dataEngine.get_historical_from_db(pair, timeframe, date)
                        if df is not None:
                            if self.showLog == True:
                                print(
                                    f"Les données de {pair} en timeframe {timeframe} ont bien été récupérées sur l'API\n"
                                )
                        elif df is None:
                            print(
                                f"Les données de {pair} en timeframe {timeframe} n'ont pas été récupérées correctement sur l'API\n"
                            )
                try:
                    if useEndDate == True:
                        dfList[pair] = df.loc[start_date:end_date]
                    else:
                        dfList[pair] = df.loc[start_date]
                except:
                    print(f"Impossible de prendre en compte la paire : {pair}")
                    cryptoNameList.remove(pair)
        if df is not None:
            if self.showLog == True:
                print(
                    f"Données récupérées pour les {len(dfList)} paires en timeframe {timeframe}."
                )
        return dfList

    # Fonction permettant de récupérer les données du passées
    # ohlc['crypto'] contient uniquement open, high, low et close.
    def get_ohlc(self, forceRedownload=False):
        if self.ohlc == None or forceRedownload == True:
            if self.showLog == True:
                print("Téléchargement des données OHLC...")
            self.ohlc = self.load_ohlc(
                start_date=self.start_date,
                end_date=self.end_date,
                forceDownload=self.forceDownload,
                downloadFrom2019=self.downloadFrom2019,
            )
            if self.showLog == True:
                print("Données OHLC chargées.")
        return self.ohlc

    # Permet de changer le nom du dossier de la stratégie dédiée à ce backtest
    def change_strategy_name(self, strategy_name):
        if self.showLog == True:
            print(f"Le nom de la stratégie est devenue : {strategy_name}")
        self.strategy_name = strategy_name

    # Fonction permettant de récupérer les indicateurs présents dans la fonction load_indicators() de strategie.py pour chaque crypto
    # dfList['crypto'] contient open, high, low, close, ema50, stoch_rsi, supertrend, macd, ...
    def internal_load_indicators(self, forceRedownload=False, indicators=None):
        if self.showLog == True:
            print("Récupérations des indicateurs...")
        if self.ohlc == None or forceRedownload == True:
            if self.showLog == True:
                print("Données OHLC introuvables.")
            self.ohlc = self.get_ohlc()
        if self.dfList == None or forceRedownload == True:
            if self.showLog == True:
                print("Données avec indicateurs introuvables.")
                print("Génération des indicateurs...")
            sys.path.append(self.get_strategy_path())
            from strategie import load_indicators

            if indicators == None:
                indicators = self.get_params()["params"]
            self.dfList = load_indicators(
                self.ohlc, self.ohlc, indicators, self.showLog
            )
            if self.showLog == True:
                print("Données avec indicateurs récupérées.")
        return self.dfList

    def run(self, showLog=True, params=None, startingBalance=None):
        self.showLog = showLog
        self.configs = self.get_configs()
        self.parametres = self.get_configs()
        if params != None:
            self.set_params(params)
            params=params['params']
        else:
            params = self.parametres['params']
        self.dfList = self.internal_load_indicators(indicators=params)
        if int(self.dfList["BTC-PERP"].shape[0]) < int(
            self.configs["STRATEGIE"]["nbOfCandlesRecovered"]
        ):
            print(
                f"Attention, vous avez indiqué dans les configurations que {int(self.configs['STRATEGIE']['nbOfCandlesRecovered'])} doivent être récupérées pour cette stratégie, hors vous n'avez que {self.dfList['BTC-PERP'].shape[0]} bougies de données pour le BTC."
            )
        self.botname = str(self.configs["CONFIGS"]["botname"])
        self.useTakeProfit = str2bool(self.configs["STRATEGIE"]["useTakeProfit"])
        self.useStoploss = str2bool(self.configs["STRATEGIE"]["useStoploss"])
        maxPositions = int(self.configs["STRATEGIE"]["maxPositions"])
        useFixAmountOfUSD = str2bool(self.configs["STRATEGIE"]["useFixAmountOfUSD"])
        fixAmount = float(self.configs["STRATEGIE"]["fixAmount"])
        repartitionLongAndShort = str2bool(
            self.configs["STRATEGIE"]["repartitionLongAndShort"]
        )

        if startingBalance == None:
            if self.startingBalance == None:
                quantityUSD = float(self.configs["STRATEGIE"]["totalInvestment"])
            else:
                quantityUSD = self.startingBalance
        else:
            quantityUSD = startingBalance
        sys.path.append(self.get_strategy_path())
        from strategie import (
            openShortCondition,
            closeShortCondition,
            openLongCondition,
            closeLongCondition,
            getTakeprofit,
            getStoploss,
        )

        dfTestList = []
        cryptoNameList = []
        for perpSymbol in self.dfList:
            dfTestList.append(self.dfList[perpSymbol])
            cryptoNameList.append(perpSymbol)
        prixAchat = [0] * len(self.dfList)
        stopLoss = [0] * len(self.dfList)
        takeProfit = [5000000] * len(self.dfList)
        quantiteDeCoinDuneCrypto = [0] * len(self.dfList)
        quantiteDeCoinDuneCryptoShorted = [0] * len(self.dfList)
        equivalentUSDdeCryptoEnPossession = [0] * len(self.dfList)
        activePositions = 0
        lastIndex = dfTestList[0].index.values[1]
        lastlastIndex = dfTestList[0].index.values[1]
        positionsSkipped = []
        openLongPositions = []
        openShortPositions = []
        count = []
        dfTrades = None
        dfTrades = pd.DataFrame(
            columns=[
                "date",
                "symbol",
                "position",
                "reason",
                "price",
                "frais",
                "fiat",
                "coins",
                "wallet",
            ]
        )
        quantiteUSD = quantityUSD
        useLong = str2bool(self.configs["STRATEGIE"]["useLong"])
        useShort = str2bool(self.configs["STRATEGIE"]["useShort"])

        for index, row in dfTestList[0].iterrows():
            if self.showLog==True :
                print("================", index, " ================")
            # -- On vérifie si on a au moins une crypto en possession en ce moment --
            if (
                (quantiteDeCoinDuneCrypto.count(0) == len(quantiteDeCoinDuneCrypto))
                == False
                or (
                    quantiteDeCoinDuneCryptoShorted.count(0)
                    == len(quantiteDeCoinDuneCryptoShorted)
                )
                == False
            ):
                for i in range(0, len(dfTestList)):
                    if quantiteDeCoinDuneCrypto[i] != 0 and useLong == True:
                        try:
                            row = dfTestList[i].loc[lastIndex]
                            previousRow = dfTestList[i].loc[lastlastIndex]
                            prixDeVente = 0
                            # Si le stoploss a été dépassé :
                            if self.useStoploss == True and (stopLoss[i] >= row["low"]):
                                prixDeVente = stopLoss[i]
                                stopLoss[i] = 0
                                raison = "Stoploss"
                            # Si le takeprofit a été dépassé :
                            if (
                                self.useTakeProfit == True
                                and takeProfit[i] <= row["high"]
                                and prixDeVente == 0
                            ):
                                prixDeVente = takeProfit[i]
                                raison = "Takeprofit"
                                takeProfit[i] = 5000000
                            # On regarde si les conditions de fermeture de position Long sont respectées
                            if (
                                closeLongCondition(
                                    row,
                                    previousRow,
                                    self.dfList,
                                    self.get_params()["params"],
                                )
                                and prixDeVente == 0
                            ):
                                # On calcule le nouveau solde d'USD après la vente
                                prixDeVente = row["close"]
                                raison = "Conditions respectées"
                            # Si une des conditions de vente est définie, on a un prix de vente fixé différent de 0 :
                            if prixDeVente != 0:
                                gain_perte = (
                                    prixDeVente - prixAchat[i]
                                ) * quantiteDeCoinDuneCrypto[i]
                                if raison == "Takeprofit":
                                    frais = (
                                        quantiteDeCoinDuneCrypto[i]
                                        * prixDeVente
                                        * takerFrais
                                    )
                                else:
                                    frais = (
                                        quantiteDeCoinDuneCrypto[i]
                                        * prixDeVente
                                        * takerFrais
                                    )
                                quantiteUSD = (
                                    quantiteUSD
                                    + (
                                        gain_perte
                                        + prixAchat[i] * quantiteDeCoinDuneCrypto[i]
                                    )
                                    - frais
                                )
                                # -- LOG --
                                if showLog:
                                    print(
                                        index,
                                        "| CLOSE LONG  (",
                                        round(gain_perte - frais, 5),
                                        "$) :",
                                        round(quantiteDeCoinDuneCrypto[i], 5),
                                        cryptoNameList[i].split("-")[0],
                                        "at",
                                        round(prixDeVente, 5),
                                        "$ :",
                                        raison,
                                    )
                                # -- On rénitialise les variables après la vente --
                                quantiteDeCoinDuneCrypto[i] = 0
                                equivalentUSDdeCryptoEnPossession[i] = 0
                                prixAchat[i] = 0
                                takeProfit[i] = 5000000
                                stopLoss[i] = 0
                                activePositions -= 1
                                while cryptoNameList[i] in openLongPositions:
                                    del openLongPositions[
                                        openLongPositions.index(cryptoNameList[i])
                                    ]
                                myrow = {
                                    "date": index,
                                    "symbol": cryptoNameList[i],
                                    "execution": dfTestList[i].loc[lastIndex],
                                    "position": "CLOSE LONG",
                                    "reason": raison,
                                    "price": prixDeVente,
                                    "frais": frais,
                                    "fiat": quantiteUSD,
                                    "coins": 0,
                                    "wallet": sum(equivalentUSDdeCryptoEnPossession)
                                    + quantiteUSD,
                                }
                                dfTrades = dfTrades.append(myrow, ignore_index=True)
                        except Exception as err:
                            print(traceback.format_exc())
                            pass
                    # -- Check if you have more than 0 coin in SHORT --
                    if quantiteDeCoinDuneCryptoShorted[i] != 0 and useShort == True:
                        try:
                            row = dfTestList[i].loc[lastIndex]
                            previousRow = dfTestList[i].loc[lastlastIndex]
                            prixDeVente = 0
                            # Si le stoploss a été dépassé :
                            if self.useStoploss == True and stopLoss[i] <= row["high"]:
                                prixDeVente = stopLoss[i]
                                raison = "Stoploss"
                            # Si le takeprofit a été dépassé :
                            if (
                                self.useTakeProfit == True
                                and takeProfit[i] >= row["low"]
                                and prixDeVente == 0
                            ):
                                prixDeVente = takeProfit[i]
                                raison = "Takeprofit"
                            # On regarde si les conditions de fermeture de position Short sont respectées
                            if (
                                closeShortCondition(
                                    row,
                                    previousRow,
                                    self.dfList,
                                    self.get_params()["params"],
                                )
                                and prixDeVente == 0
                            ):
                                # On calcule le nouveau solde d'USD après la vente
                                prixDeVente = row["close"]
                                raison = "Conditions respectées"
                            if prixDeVente != 0:
                                gain_perte = (
                                    prixAchat[i] - prixDeVente
                                ) * quantiteDeCoinDuneCryptoShorted[i]
                                if raison == "Takeprofit":
                                    frais = (
                                        prixDeVente
                                        * quantiteDeCoinDuneCryptoShorted[i]
                                        * makerFrais
                                    )
                                else:
                                    frais = (
                                        prixDeVente
                                        * quantiteDeCoinDuneCryptoShorted[i]
                                        * takerFrais
                                    )
                                quantiteUSD = (
                                    quantiteUSD
                                    + (
                                        gain_perte
                                        + prixAchat[i]
                                        * quantiteDeCoinDuneCryptoShorted[i]
                                    )
                                    - frais
                                )
                                # -- LOG --
                                if showLog:
                                    print(
                                        index,
                                        "| CLOSE SHORT (",
                                        round(gain_perte, 5),
                                        "$) :",
                                        round(quantiteDeCoinDuneCryptoShorted[i], 5),
                                        cryptoNameList[i].split("-")[0],
                                        "at",
                                        round(prixDeVente, 5),
                                        "$ :",
                                        raison,
                                    )
                                # -- On rénitialise les variables après la vente --
                                quantiteDeCoinDuneCryptoShorted[i] = 0
                                equivalentUSDdeCryptoEnPossession[i] = 0
                                prixAchat[i] = 0
                                takeProfit[i] = 0
                                stopLoss[i] = 0
                                activePositions -= 1
                                while cryptoNameList[i] in openShortPositions:
                                    del openShortPositions[
                                        openShortPositions.index(cryptoNameList[i])
                                    ]
                                # -- Add the trade to DfTrades to analyse it later --
                                myrow = {
                                    "date": index,
                                    "symbol": cryptoNameList[i],
                                    "execution": dfTestList[i].loc[lastIndex],
                                    "position": "CLOSE SHORT",
                                    "reason": raison,
                                    "price": prixDeVente,
                                    "frais": frais,
                                    "fiat": quantiteUSD,
                                    "coins": 0,
                                    "wallet": sum(equivalentUSDdeCryptoEnPossession)
                                    + quantiteUSD,
                                }
                                dfTrades = dfTrades.append(myrow, ignore_index=True)
                        except Exception as err:
                            print(traceback.format_exc())
                            pass
            # -- Buy market order --
            # -- Check if you can open a new position --
            if activePositions < maxPositions:
                perf = {}
                for i in range(0, len(dfTestList)):
                    try:
                        row = dfTestList[i].loc[lastIndex]
                        previousRow = dfTestList[i].loc[lastlastIndex]
                        if (
                            useLong == True
                            and openLongCondition(
                                row,
                                previousRow,
                                self.dfList,
                                self.get_params()["params"],
                            )
                            and activePositions < maxPositions
                            and quantiteDeCoinDuneCryptoShorted[i] == 0
                            and quantiteDeCoinDuneCrypto[i] == 0
                            and (useFixAmountOfUSD==False or (useFixAmountOfUSD==True and float(self.configs["STRATEGIE"]["fixAmount"]) <= quantiteUSD))
                        ):
                            try:
                                prixAchat[i] = row["close"]
                                # -- Define size of the position --
                                if useFixAmountOfUSD == True:
                                    usdAllocated = float(
                                        self.configs["STRATEGIE"]["fixAmount"]
                                    )
                                    if quantiteUSD < usdAllocated:
                                        print(
                                            f"Vous n'avez plus suffisamment d'USD pour ouvrir une position. La valeur fixe d'USD pour une position est de {usdAllocated}$ et vous ne possedez que {quantiteUSD}$"
                                        )
                                else:
                                    usdMultiplier = float(
                                        self.configs["STRATEGIE"]["usdAllocated"]
                                    ) / (maxPositions - activePositions)
                                    usdAllocated = quantiteUSD * usdMultiplier
                                frais = takerFrais * usdAllocated
                                coin = (usdAllocated - frais) / prixAchat[i]
                                quantiteUSD = quantiteUSD - coin * prixAchat[i] - frais

                                # -- Set coin and equivalent usd to size of position after open position --
                                quantiteDeCoinDuneCrypto[i] = coin
                                equivalentUSDdeCryptoEnPossession[i] = (
                                    coin * row["close"]
                                )
                                activePositions += 1
                                openLongPositions.append(cryptoNameList[i])

                                if self.useStoploss:
                                    stopLoss[i] = getStoploss(
                                        "long",
                                        prixAchat[i],
                                        row,
                                        previousRow,
                                        self.dfList,
                                        self.get_params()["params"],
                                    )
                                # -- Create a Take Profit --
                                if self.useTakeProfit:
                                    takeProfit[i] = getTakeprofit(
                                        "long",
                                        prixAchat[i],
                                        row,
                                        previousRow,
                                        self.dfList,
                                        self.get_params()["params"],
                                    )
                                # -- LOG --
                                if showLog:
                                    print(
                                        index,
                                        "| OPEN  LONG  :",
                                        round(quantiteDeCoinDuneCrypto[i], 5),
                                        cryptoNameList[i].split("-")[0],
                                        "at",
                                        round(prixAchat[i], 5),
                                        "$",
                                    )

                                # -- Add the trade to dfTrades to analyse it later --
                                myrow = {
                                    "date": index,
                                    "symbol": cryptoNameList[i],
                                    "execution": dfTestList[i].loc[lastIndex],
                                    "position": "OPEN LONG",
                                    "reason": "Conditions respectées",
                                    "price": prixAchat[i],
                                    "frais": frais,
                                    "fiat": quantiteUSD,
                                    "coins": coin,
                                    "wallet": sum(equivalentUSDdeCryptoEnPossession)
                                    + quantiteUSD,
                                }
                                dfTrades = dfTrades.append(myrow, ignore_index=True)
                            except Exception as err:
                                print(traceback.format_exc())
                                break
                        if (
                            useShort == True
                            and openShortCondition(
                                row,
                                previousRow,
                                self.dfList,
                                self.get_params()["params"],
                            )
                            and activePositions < maxPositions
                            and quantiteDeCoinDuneCryptoShorted[i] == 0
                            and quantiteDeCoinDuneCrypto[i] == 0
                            and (useFixAmountOfUSD==False or (useFixAmountOfUSD==True and float(self.configs["STRATEGIE"]["fixAmount"]) <= quantiteUSD))
                        ):
                            try:
                                prixAchat[i] = row["close"]
                                # -- Define size of the position --
                                if useFixAmountOfUSD == True:
                                    usdAllocated = float(
                                        self.configs["STRATEGIE"]["fixAmount"]
                                    )
                                    if quantiteUSD < usdAllocated:
                                        print(
                                            f"Vous n'avez plus suffisamment d'USD pour ouvrir une position. La valeur fixe d'USD pour une position est de {usdAllocated}$ et vous ne possedez que {quantiteUSD}$"
                                        )
                                else:
                                    usdMultiplier = float(
                                        self.configs["STRATEGIE"]["usdAllocated"]
                                    ) / (maxPositions - activePositions)
                                    usdAllocated = quantiteUSD * usdMultiplier
                                frais = takerFrais * usdAllocated
                                coin = usdAllocated / prixAchat[i]
                                quantiteUSD = quantiteUSD - coin * prixAchat[i] - frais
                                # -- Set coin and equivalent usd to size of position after open position --
                                quantiteDeCoinDuneCryptoShorted[i] = coin
                                equivalentUSDdeCryptoEnPossession[i] = (
                                    coin * row["close"]
                                )
                                activePositions += 1
                                openShortPositions.append(cryptoNameList[i])
                                # -- Create a Stop Loss --
                                if self.useStoploss:
                                    stopLoss[i] = getStoploss(
                                        "short",
                                        prixAchat[i],
                                        row,
                                        previousRow,
                                        self.dfList,
                                        self.get_params()["params"],
                                    )
                                # -- Create a Take Profit --
                                if self.useTakeProfit:
                                    takeProfit[i] = getTakeprofit(
                                        "short",
                                        prixAchat[i],
                                        row,
                                        previousRow,
                                        self.dfList,
                                        self.get_params()["params"],
                                    )
                                # -- LOG --
                                if showLog:
                                    print(
                                        index,
                                        "| OPEN  SHORT :",
                                        round(quantiteDeCoinDuneCryptoShorted[i], 5),
                                        cryptoNameList[i].split("-")[0],
                                        "at",
                                        round(prixAchat[i], 5),
                                        "$",
                                    )
                                # -- Add the trade to dfTrades to analyse it later --
                                myrow = {
                                    "date": index,
                                    "symbol": cryptoNameList[i],
                                    "execution": dfTestList[i].loc[lastIndex],
                                    "position": "OPEN SHORT",
                                    "reason": "Conditions respectées",
                                    "price": prixAchat[i],
                                    "frais": frais,
                                    "fiat": quantiteUSD,
                                    "coins": coin,
                                    "wallet": sum(equivalentUSDdeCryptoEnPossession)
                                    + quantiteUSD,
                                }
                                dfTrades = dfTrades.append(myrow, ignore_index=True)
                            except Exception as err:
                                print(traceback.format_exc())
                                break
                    except Exception as err:
                        pass
            else:
                positionsSkipped.append(1)
            # -- Keep last index to define last row --
            lastlastIndex = lastIndex
            lastIndex = index

        dfTrades["walletAth"] = dfTrades["wallet"].cummax()
        dfTrades["drawDown"] = dfTrades["walletAth"] - dfTrades["wallet"]
        dfTrades["drawDownPct"] = dfTrades["drawDown"] / dfTrades["walletAth"]
        drawdown = str(round(100 * dfTrades["drawDownPct"].max(), 2))
        if showLog:
            print("Final wallet", sum(equivalentUSDdeCryptoEnPossession) + quantiteUSD)
            print(f"Drawdown : -{drawdown} %")
            print(
                len(positionsSkipped),
                "opportunités d'ouvertures de positions n'ont pu être prise car maxOpenPositions était atteint",
            )
            if useLong == True:
                print(openLongPositions, "sont ouvertes actuellement en LONG")
            if useShort == True:
                print(openShortPositions, "sont ouvertes actuellement en SHORT")
            print("Timeframe=", str(self.get_configs()["STRATEGIE"]["timeframe"]))
            print("maxPositions=", maxPositions)
            print(
                f"Frais : {makerFrais*100}% de makerFees et {takerFrais*100}% de takerFees"
            )
            try:
                BTobject = Backtesting()
                newDf = BTobject.multi_spot_backtest_analys(
                    dfTrades=dfTrades,
                    dfTest=dfTestList[0],
                    pairList=cryptoNameList,
                    timeframe=str(self.get_configs()["STRATEGIE"]["timeframe"]),
                )
            except Exception as err:
                if "single positional indexer is out-of-bounds" in str(err):
                    print(
                        "ERREUR : Votre backtest semble n'avoir fait aucune ouverture de position"
                    )
                    if int(self.dfList["BTC-PERP"].shape[0]) < int(
                        self.configs["STRATEGIE"]["nbOfCandlesRecovered"]
                    ):
                        print(
                            f"TIPS : Il semblerait que vous n'ayez que {self.dfList['BTC-PERP'].shape[0]} bougies téléchargées pour le BTC, or, d'après les configurations votre stratégie a besoin de {int(self.configs['STRATEGIE']['nbOfCandlesRecovered'])} bougies. Essayez de rajouter au moins {int((int(self.configs['STRATEGIE']['nbOfCandlesRecovered'])-self.dfList['BTC-PERP'].shape[0])/24+1)} jours de données"
                        )
                else:
                    print(f"ERREUR : {err}")
        return (
            sum(equivalentUSDdeCryptoEnPossession) + quantiteUSD,
            len(dfTrades) / 2,
            drawdown,
        )
