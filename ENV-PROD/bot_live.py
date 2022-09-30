# AUTHORS : MOUTONNEUX ( https://github.com/titouannwtt )
# CE TEMPLATE EST ADAPTEE A DES TIMEFRAMES DE 1 heure ou moins
# VERSION :
version = "7.06"
# ====================================================================

# Ce template de bot de trading vous est partagé gratuitement.
# Son développement représente des centaines d'heures de travail et tout a été commenté pour vous faciliter sa compréhension.
# Vous pouvez me soutenir en utilisant mon lien d'affiliation FTX ( https://ftx.com/eu/profile#a=titouannwtt ),
# Ou en me faisant des dons en crypto-monnaie :
#           Adresse BTC :                     3GYhBgZMfgzqjYhVhc2w53oMcvZb4jfGfL
#           Adresse ETH (Réseau ERC20) :      0x43fC6F9B8b1CfBd83b52a1FD1de510effe0A49a7
#           (Même une petite somme me soutient énormement moralement :D)

# Vous êtes autorisé à modifier ce code pour un usage personnel uniquement.
# Vous êtes autorisé à partager ce code ou un extrait de ce code dans un cadre privé uniquement, à condition de me créditez en tant qu'auteur de façon explicite.
# Vous n'êtes pas autorisé à vendre ce code, un extrait de ce code ou une modification de ce code.
# Vous n'êtes pas autorisé à tirer profit de ce code, un extrait de ce code ou une modification de ce code.

# ====================================================================

# =======================
#  IMPORTS NECESSAIRES
# =======================

import configparser
import datetime
import json
import os
import sys
import time
# Cet import + le code suivant permettent d'éviter les warnings dans les logs
import warnings
from optparse import Values

import ftx
import matplotlib.pyplot as plt
import pandas as pd
import requests
import telegram_send
from constantly import ValueConstant
from numpy import NaN, float64, little_endian

from cBot_perp_ftx import cBot_perp_ftx

# dans le dossier ./dependencies/
try :
    if len(sys.argv) == 2:
        folder_name = str(sys.argv[1]).split("/")[0]
        path = os.path.dirname(os.path.abspath(__file__)) + "/" + folder_name
        sys.path.append(path)
    elif len(sys.argv) == 1 :
        path = os.path.dirname(os.path.abspath(__file__))
    else:
        print(f"Mauvaise syntaxe : python3 {sys.argv[0]} <dossier-strategie>")
        exit(1)
except IndexError :
    print(f"Mauvaise syntaxe : python3 {sys.argv[0]} <dossier-strategie>")
    exit(1)

# Si le dossier ne termine pas par un /
if path[-1] != "/":
    path = path + "/"

if os.path.exists(path) == False:
    print(f"Dossier {path} introuvable.")
    print(f"Utilisez : python3 {sys.argv[0]} <dossier-strategie>")
    exit(2)

os.makedirs(path+"data", exist_ok=True)
try:
    from strategie import *
except Exception as err:
    print(f"Impossible d'importer strategie.py du dossier {path} : {err}")
    exit(3)
try:
    from cBot_perp_ftx import cBot_perp_ftx
except Exception as err:
    print(f"Impossible d'importer cBot_perp_ftx.py du dossier {path} : {err}")
    exit(4)


warnings.simplefilter("ignore")

# =====================================
#     RECUPERATION DU FICHIER DE
# CONFIGURATIONS ET DES INDICATEURS
# =====================================

try :
    with open(path+'credentials.json') as credentials:
        creds = json.load(credentials)
except Exception as err :
    print(f"Impossible de récupérer les credentials : {err}")
    exit(1)

# On récupère le fichier contenant les configurations (par défaut config-bot.cfg)
config = configparser.ConfigParser()
config.read(path + "config-bot.cfg")

try:
    botname = str(config["CONFIGS"]["botname"])
except KeyError:
    botname = creds['subAccountName']


try:
    strategy_version = str(config["CONFIGS"]["strategy_version"])
except KeyError:
    strategy_version = ""



print(
    f"========================\n{botname} sv{strategy_version} - tv{version}\n" + str(datetime.datetime.now())
)
#sv = Strategie Version
#tv = Template Version

print("Sections recupérées dans le fichier de configuration: " + str(config.sections()))

# On récupère le fichier contenant les paramètres des indicateurs (par défaut CONFIGS.cfg)
indicators = configparser.ConfigParser()
try:
    parametersFile = str(config["FICHIER.HISTORIQUE"]["parametersFile"])
except:
    parametersFile = path + "parametres.cfg"
indicators.read(path + parametersFile)
print(
    "Sections recupérées dans le fichier des indicateurs : "
    + str(indicators.sections())
)


# Le mode debug permet d'afficher beaucoup de détails dans les logs d'executions du bot
if str(config["CONFIGS"]["debug"]) == "false":
    debug = False
else:
    debug = True

soldeToSaveInvestisment = float(config["STRATEGIE"]["soldeToSaveInvestisment"])
totalInvestment = float(config["STRATEGIE"]["totalInvestment"])

stopTheBotIfSoldeDownBelow = float(config["STRATEGIE"]["stopTheBotIfSoldeDownBelow"])

# =========================
#  AUTHENTIFICATION PART
# =========================

client = ftx.FtxClient(
    api_key=str(creds["apiKey"]),
    api_secret=str(creds["secret"]),
    subaccount_name=str(creds["subAccountName"]),
)
# Grâce à la librairie cBot_perp_ftx créée par CryptoRobotsFR, on instancie une connexion avec l'API FTX sur notre sous-compte associé au bot.
# Grâce à cette connexion on sera par la suite en mesure de faire des appels à l'API pour récupérer des données, et envoyer des ordres à l'exchange.
ftx = cBot_perp_ftx(
    apiKey=str(creds["apiKey"]),
    secret=str(creds["secret"]),
    subAccountName=str(creds["subAccountName"]),
)

# Cette fonction permet d'obtenir le nombre d'USD disponible sur ce sous-compte
def getFreeUSDBalance():
    jsonBalance = client.get_balances()
    if jsonBalance == []:
        return 0
    pandaBalance = pd.DataFrame(jsonBalance)
    pandaBalance.drop(
        pandaBalance.loc[pandaBalance["coin"] != "USD"].index, inplace=True
    )
    return float(pandaBalance["free"].tolist()[0])


def changeSaveInvestissement(statement) :
    global config
    if 0==(statement != "true" or statement != "false") :
        print("Les arguments pour la fonction changeSaveInvestissement() ne peuvent que être 'true' ou 'false'.")
        raise WrongArgumentException
    with open(path + "data/saveInvestissementState.dat", 'w') as configfile:
        configfile.write(statement)


usdAmount=ftx.get_balance_of_one_coin("USD")

def getInitialSoldeStatement() :
    global soldeToSaveInvestisment
    global usdAmount
    try :
        with open(path + "data/saveInvestissementState.dat", 'r') as configfile:
            if configfile.read()=="true" :
                saveInvestisment = 'true'
                return "true"
            else :
                if usdAmount > soldeToSaveInvestisment :
                    freeUSD=usdAmount-totalInvestment
                    print(f"Votre solde a dépassé {soldeToSaveInvestisment}$, on sauvegarde le solde initial et on utilise plus que {freeUSD}$ pour conserver les {totalInvestment}$ initiaux")
                    saveInvestisment = "true"
                    changeSaveInvestissement("true")
                    return "true"
                else :
                    changeSaveInvestissement("false")
                    return "false"
    except :
        if usdAmount > soldeToSaveInvestisment :
            freeUSD=usdAmount-totalInvestment
            print(f"Votre solde a dépassé {soldeToSaveInvestisment}$, on sauvegarde le solde initial et on utilise plus que {freeUSD}$ pour conserver les {totalInvestment}$ initiaux")
            saveInvestisment = "true"
            changeSaveInvestissement("true")
            return "true"
        else :
            changeSaveInvestissement("false")
            return "false"
        

saveInvestisment = getInitialSoldeStatement()
if saveInvestisment=="false" :
    print("Vous ne sauvegardez pas encore votre investissement initial.")
if saveInvestisment=="true" :
    if debug == "true" :
        print("Vous sauvegardez votre investissement initial.")

# ================================
#      CONFIGS PAR DEFAUT
# ================================

# Levier par défaut qui sera utilisé lors de l'ouverture des positions
defaultLeverage = int(config["STRATEGIE"]["defaultLeverage"])
leverage = defaultLeverage


useFixAmountOfUSD = str(config["STRATEGIE"]["useFixAmountOfUSD"])

# Pourcentage d'usd qui sera alloué au bot
usdAllocated = float(config["STRATEGIE"]["usdAllocated"])

# Quantité d'USD qui sera alloué si useFixAmountOfUSD est sur "true"
fixAmount = float(config["STRATEGIE"]["fixAmount"])


useLimitOrderToOpen = str(config["STRATEGIE"]["useLimitOrderToOpen"])

useLimitOrderToClose = str(config["STRATEGIE"]["useLimitOrderToClose"])
forceSell = str(config["STRATEGIE"]["forceSell"])

# Bougie utilisé comme réferentielle pour déterminer la performance de la crypto (on récupère le prix il y a X bougies et on le compare avec maintenant)
# Par défaut : -351 signifie qu'on récupère les données il y a 2 semaines (351/24=~14 jours)
nombreDeBougiesMinimum = int(
    config["STRATEGIE"]["nombreDeBougiesMinimum"]
)*-1

# Nombre de pairs que l'on utilisera pour l'execution du bot
classementminimum = int(config["STRATEGIE"]["classementminimum"])
# Timeframe utilisée par le bot pour récupérer les données, vous devrez executé ce script sur la même période (par défaut : 1h)
timeframe = str(config["STRATEGIE"]["timeframe"])
# Liste de paires spécifiées dans un json, sera utilisée à la place des {classementminimum} premières paires de FTX si vous mettez useWhitelist=true (par défaut : false)
useWhitelist = str(config["STRATEGIE"]["useWhitelist"])


# =============================================
#      FONCTIONS NECESSAIRES POUR L'ENVOIE
#     DE LA NOTIFICATION FINALE SUR TELEGRAM
#         Codé par Mouton - 05/04/2022
# =============================================

# Si cette option est sur "true", les notifications telegram seront envoyées à chaque execution
alwaysNotifTelegram = str(config["CONFIGS"]["alwaysNotifTelegram"])
# Si cette option est sur "true" et que alwaysNotifTelegram est également sur "true" : les notifications telegram ne vous seront envoyées qu'en cas d'ouvertures ou de fermeture de positions
notifTelegramOnChangeOnly = str(config["CONFIGS"]["notifTelegramOnChangeOnly"])

# Si cette option est sur "true", la notification telegram contiendra les moments où votre solde a été le plus haut selon différentes périodes
notifBilanDePerformance = str(config["CONFIGS"]["notifBilanDePerformance"])
# Si cette option est sur "true", la notification telegram contiendra la variation du solde heure par heure
notifBilanEvolutionContinue = str(config["CONFIGS"]["notifBilanEvolutionContinue"])
# Si cette option est sur "true", chaque paire mentionnée contiendra un lien permettant de la consulter sur FTX
showURLonTelegramNotif = str(config["CONFIGS"]["showURLonTelegramNotif"])
# Si cette optioen est sur "true", le stoploss sera spécifié à côté de la paire
showSecurityStopLossOnTelegram = str(
    config["CONFIGS"]["showSecurityStopLossOnTelegram"]
)

# Permet de stocker tout ce qu'on veut envoyer sur telegram dans la variable "message", à la fin de l'execution du code, on envoit la notification telegram avec cette variable en tant que message
message = " "


def addMessageComponent(string):
    global message
    message = message + "\n" + string


# Contient la liste des positions ouvertes en LONG actuellement
positionLongList = " "


def addPositionLONG(string):
    global positionLongList
    positionLongList = positionLongList + ", " + string


# Contient la liste des positions ouvertes en SHORT actuellement
positionShortList = " "


def addPositionSHORT(string):
    global positionShortList
    positionShortList = positionShortList + ", " + string


# =======================
#  FONCTIONS BASIQUES
# =======================

# Vérifie si des cryptos ont été vendues par des ordres limites
def check():
    print("Lancement du check...")
    global changement
    try:
        lastLongPosition = {}
        lastShortPosition = {}
        with open(path + str(config["FICHIER.HISTORIQUE"]["positionFile"]), "r") as f:
            for line in f:
                if "#" in line:
                    # on saute la ligne
                    continue
                data = line.split()
                # 2022-08-19 10:30:39 | open LONG 8.840906444288304 CRV-PERP at 1.01213685
                date = str(data[0]) + str(data[1])
                positionType = str(data[3])  # open/close
                position = str(data[4])  # LONG/SHORT
                # quantity = float(data[6]) #quantité
                perpSymbol = str(data[6])  # XXX-PERP
                if position == "LONG":
                    lastLongPosition[perpSymbol] = positionType
                if position == "SHORT":
                    lastShortPosition[perpSymbol] = positionType
        cointrades = ftx.get_open_position()
        date = datetime.datetime.now()
        separateDate = str(date).split(".")
        date = str(separateDate[0])
        for perpSymbol, positionType in lastLongPosition.items():
            if (
                perpSymbol not in str(cointrades)
                and lastLongPosition[perpSymbol] == "open"
                and position == "LONG"
            ):
                print(
                    f"Votre position LONG sur {perpSymbol} a été fermée depuis la dernière execution."
                )
                addMessageComponent(f"ORDRE LIMITE ATTEINT (LONG) :")
                addMessageComponent(f" • {perpSymbol}")
                changement = changement + 1
                if showURLonTelegramNotif == "true":
                    addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
                addMessageComponent(" ")
                with open(
                    path + str(config["FICHIER.HISTORIQUE"]["positionFile"]), "a"
                ) as f:
                    f.write(
                        f"{date} | close LONG 0.0 {perpSymbol} at ORDRE LIMITE (TP/SL) \n"
                    )
        for perpSymbol, positionType in lastShortPosition.items():
            if (
                perpSymbol not in str(cointrades)
                and lastShortPosition[perpSymbol] == "open"
                and position == "SHORT"
            ):
                print(
                    f"Votre position SHORT sur {perpSymbol} a été fermée depuis la dernière execution."
                )
                addMessageComponent(f"ORDRE LIMITE ATTEINT (SHORT) :")
                addMessageComponent(f" • {perpSymbol}")
                changement = changement + 1
                if showURLonTelegramNotif == "true":
                    addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
                addMessageComponent(" ")
                with open(
                    path + str(config["FICHIER.HISTORIQUE"]["positionFile"]), "a"
                ) as f:
                    f.write(
                        f"{date} | close SHORT 0.0 {perpSymbol} at ORDRE LIMITE (TP/SL) \n"
                    )
    except Exception as err:
        print(f"Erreur survenue lors du check : {err}")
        pass


# Cette fonction permet d'obtenir le prix actuel d'une crypto sur FTX
def getCurrentPrice(perpSymbol):
    return ftx.get_bid_ask_price(symbol=perpSymbol)["ask"]


# Récupère le prix auquel a été fixé le stoploss sur une position ouverte
def getSecureStopLossPrice(perpSymbol, position=None, price=None, levier=None):
    if price == None:
        price = getPrixAchat(perpSymbol)
    if levier == None:
        levier = getLevier(perpSymbol)
    if (
        position == "long"
        or getTypeOfPosition(perpSymbol) == "long"
        or getTypeOfPosition(perpSymbol) == "buy"
    ):
        prixSL = getStoploss(
                    "long",
                    price,
                    dfList[perpSymbol].iloc[-2],
                    dfList[perpSymbol].iloc[-3],
                    dfList,
                    indicators["params"])
    if (
        position == "short"
        or getTypeOfPosition(perpSymbol) == "short"
        or getTypeOfPosition(perpSymbol) == "sell"
    ):
        prixSL = getStoploss(
            "short",
            price,
            dfList[perpSymbol].iloc[-2],
            dfList[perpSymbol].iloc[-3],
            dfList,
            indicators["params"])
    print(f"Prix stop loss = {prixSL}")
    return prixSL


# Permet de récupérer le prix d'achat sur une position ouverte
def getPrixAchat(perpSymbol):
    ct = ftx.get_open_position(perpSymbol)
    for i in range(0, len(ct)):
        if ct[i]["info"]["future"] == perpSymbol:
            # renvoit un float, par exemple 24183.16
            return float(ct[i]["info"]["entryPrice"])


# Permet de récupérer le prix d'achat sur une position ouverte
def getNumberOfPositions():
    ct = ftx.get_open_position()
    nbLong = 0
    nbShort = 0
    for i in range(0, len(ct)):
        if ct[i]["side"] == "long":
            nbLong += 1
        if ct[i]["side"] == "short":
            nbShort += 1
    return nbLong, nbShort


# Permet de récupérer le type de position (LONG/SHORT) pour une position donnée
def getTypeOfPosition(perpSymbol):
    cointrades = ftx.get_open_position()
    for i in range(0, len(cointrades)):
        if cointrades[i]["symbol"] == perpSymbol:
            # renvoit "long" ou "short"
            return str(cointrades[i]["side"])


# Permet de récupérer la quantité de crypto d'une position ouverte
def getQuantite(perpSymbol):
    cointrades = ftx.get_open_position(perpSymbol)
    for i in range(0, len(cointrades)):
        if cointrades[i]["info"]["future"] == perpSymbol:
            try:
                taille = float(cointrades[i]["size"])
            except:
                try:
                    taille = float(cointrades[i]["info"]["netSize"])
                except:
                    taille = float(cointrades[i]["contracts"])
                pass
            if float(cointrades[i]["info"]["netSize"]) != taille:
                taille = float(cointrades[i]["contracts"])
            if getTypeOfPosition(perpSymbol) == "short" and taille < 0.0:
                # Si c'est une position short, on multiplie par -1 pour éviter que la valeur soit négative. (par défaut FTX renvoit une valeur négative pour les shorts)
                taille = taille * -1
            return taille


# Permet de récupérer le levier d'une position ouverte
def getLevier(perpSymbol):
    cointrades = ftx.get_open_position(perpSymbol)
    for i in range(0, len(cointrades)):
        if cointrades[i]["info"]["future"] == perpSymbol:
            return float(cointrades[i]["leverage"])


# Permet de récupérer la performance d'une position ouverte
def getPerformance(perpSymbol):
    return float(percentage[perpSymbol])


# Permet de récupérer les gains/pertes d'une position ouverte
def getProfit(perpSymbol):
    return float(Pnl[perpSymbol])


# =================================================
#  PAIRES SUR LESQUELLES ON APPLIQUE LA STRATEGIE
#        Codé par L'Architecte - 31/03/2022
# =================================================

perpListBase = []
if useWhitelist == "true":
    # On récupère les crytpos listées dans le fichier JSON
    f = open(path + "pair_list.json")
    pairJson = json.load(f)
    f.close()
    perpListBase = pairJson["whitelist"]
else:
    # On récupère les paires avec le plus de volumes au cours des 24h dernières heures sur FTX et on les trie selon leurs volumes
    try:
        if debug == True:
            print("Collecte des paires...")
        liste_pairs = requests.get("https://ftx.com/api/futures").json()
        if debug == True:
            print("Paires collectées sur https://ftx.com/api/futures avec succès.")
    except Exception as e:
        print(f"Error obtaining BTC old data: {e}")
    dataResponse = liste_pairs["result"]
    df = pd.DataFrame(
        dataResponse,
        columns=["name", "perpetual", "marginPrice", "volume", "volumeUsd24h"],
    )
    df["volume"] = df["volume"] * df["marginPrice"]
    df.drop(df.loc[df["perpetual"] == False].index, inplace=True)
    df.sort_values(by="volume", ascending=False, inplace=True)

    # On ne selectionne que les {classementminimum} premières paires
    i = 1
    for index, row in df.iterrows():
        if i <= classementminimum:
            perpListBase.append(row["name"])
        i = i + 1

if debug == True:
    print(f"{len(perpListBase)} paires sélectionnées :\n {perpListBase}")

# Spécifie une liste de paires que le bot exclurera systématiquement de ses executions (par défaut : quelques stablecoins)
if str(config["STRATEGIE"]["useBlacklist"])=="true" :
    f = open(path + "pair_list.json")
    pairJson = json.load(f)
    f.close()
    neverUseThesePairs = pairJson["blacklist"]
    # On récupère la liste des cryptos à ne pas utiliser et on les supprime de notre liste si elles sont présentes
    noUse = ""
    for perpSymbol in neverUseThesePairs:
        try:
            del perpListBase[perpListBase.index(perpSymbol)]
            if noUse == "":
                noUse = perpSymbol
            else:
                noUse = noUse + ", " + perpSymbol
        except:
            # print(perpSymbol, "ne sera pas utilisée.")
            pass
    if noUse != "":
        print(
            f"Les cryptos qu'on aurait dû utiliser mais qui appartiennent à la blacklist sont : {noUse}"
        )

try :
    # On récupère les paires présentent dans des positions déja ouvertes pour les ajouter à la liste des cryptos que le bot va utiliser pour être en mesure de les vendre même si elles n'étaient pas dans la liste initialement.
    cointrades = ftx.get_open_position()
    for cointrade in cointrades:
        if cointrade.get("symbol") not in perpListBase:
            perpListBase.append(cointrade.get("symbol"))
            if debug == True:
                print(
                    cointrade.get("symbol"),
                    "n'aurait pas dû être utilisé mais a été ajouté à la liste car une position est en cours avec cette paire.",
                )
except TypeError as err :
    if 'Not logged in: Invalid API key' in str(err) :
        print("ERROR : Connexion impossible à l'API FTX, veuillez vérifier vos clés API et votre subaccount dans credentials.json")
    exit(300)

# On créer 2 listes, une contenant les positions actuellement ouvertes en long et une contenant les positions actuellement ouvertes en short
pairs_long_ouvertes = []
pairs_short_ouvertes = []
cointrades = ftx.get_open_position()
for cointrade in cointrades:
    if cointrade.get("side") == "long":
        pairs_long_ouvertes.append(cointrade.get("symbol"))
    if cointrade.get("side") == "short":
        pairs_short_ouvertes.append(cointrade.get("symbol"))

# ======================================
#  COLLECTE DES COURS ET PERFORMANCES
# ======================================
# On récupère le nombre bougies précedentes spécifié en configuration pour notre timeframe
nbOfCandlesRecovered = int(config["STRATEGIE"]["nbOfCandlesRecovered"])
print(
    f"Récupération des {nbOfCandlesRecovered} dernières bougies en timeframe {timeframe} pour l'ensemble des cryptos..."
)
# On récupère l'historique de chaque crypto.
# On les range de la plus performante à la moins performante
dfList = {}
dfListSorted = {}
for perpSymbol in perpListBase:
    # On essaie de récupérer les bougies sur l'API FTX
    try:
        dfList[perpSymbol] = ftx.get_last_historical(
            perpSymbol, timeframe, nbOfCandlesRecovered
        )
    except:
        # Parfois elle n'est pas joignable ou bug, si c'est le cas, on reessaie 3 fois en réduisant le nombre de bougies qu'on récupère à chaque fois :
        time.sleep(1)
        try:
            dfList[perpSymbol] = ftx.get_last_historical(
                perpSymbol,
                timeframe,
                nbOfCandlesRecovered - int(nbOfCandlesRecovered * 0.25),
            )
        except:
            time.sleep(2)
            try:
                dfList[perpSymbol] = ftx.get_last_historical(
                    perpSymbol,
                    timeframe,
                    nbOfCandlesRecovered - int(nbOfCandlesRecovered * 0.5),
                )
            except:
                time.sleep(2)
                try:
                    dfList[perpSymbol] = ftx.get_last_historical(
                        perpSymbol,
                        timeframe,
                        nbOfCandlesRecovered - int(nbOfCandlesRecovered * 0.75),
                    )
                except:
                    # Si vraiment on a pas réussi à récupérer la crypto :
                    try:
                        del dfList[perpSymbol]
                    except:
                        pass
                    try :
                        del perpListBase[perpListBase.index(perpSymbol)]
                        perpListBase.remove(perpSymbol)
                    except :
                        pass
                    # On envoit une notification télégram pour prévenir, mais l'execution du bot continuera normalement sans utiliser cette paire.
                    telegram_send.send(
                        messages=[
                            f"{botname} : Impossible de récupérer les {nbOfCandlesRecovered} dernières bougies de {perpSymbol} en timeframe {timeframe} à 4 reprises, on n'utilisera pas cette paire durant cette execution."
                        ]
                    )
                    print(
                        f"Impossible de récupérer les {nbOfCandlesRecovered} dernières bougies de {perpSymbol} en timeframe {timeframe} à 2 reprises, on n'utilisera pas cette paire durant cette execution"
                    )
                    pass

    # Vérifie si la crypto a assez de données historiques pour être utilisé avec les indicateurs (par défaut : au moins 14 jours de présence sur FTX sont nécesaires)
    try:
        dfListSorted[perpSymbol] = (
            dfList[perpSymbol].iloc[-2]["close"]
            / dfList[perpSymbol].iloc[nombreDeBougiesMinimum]["close"]
            - 1
        ) * 100
    # Si elle n'a pas assez de données, on l'enlève de la liste
    except:
        try:
            del dfList[perpSymbol]
            perpListBase.remove(perpSymbol)
            del perpListBase[perpListBase.index(perpSymbol)]
        except:
            pass
            print(perpSymbol, "ne sera pas utilisée : manque de données.")

if str(config["STRATEGIE"]["sortByRecentPerf"]) == "true":
    # Classe les paires et structure la liste de dataframe correctement
    perpListBase = sorted(dfListSorted.items(), key=lambda item: item[1])
    perpList = []
    for perpListBase in perpListBase:
        for i in perpListBase:
            perpList.append(i)

    for i in range(1, round(len(perpList) / 2) + 1, 1):
        del perpList[i]

    perpList = list(reversed(perpList))
    if debug == True:
        print(perpList)
else:
    perpList = perpListBase

# =================================================
#   CODES NECESSAIRES POUR DETERMINER COMBIEN
#     D'USD SONT DETENUS PAR LE SUBACCOUNT :
# =================================================

usdAmount = ftx.get_balance_of_one_coin("USD")
Pnl = {}
percentage = {}
levier = {}
amount = {}
cointrade = ftx.get_open_position()
for cointrade in cointrade:
    pair = cointrade.get("symbol")
    Pnl[pair] = float(cointrade.get("unrealizedPnl"))
    levier[pair] = int(cointrade.get("leverage"))
    percentage[pair] = float(cointrade.get("percentage"))
    amount[pair] = float(cointrade.get("contracts"))
if debug == True:
    print(Pnl)
openPositions = len(pairs_long_ouvertes) + len(pairs_short_ouvertes)
if debug == True:
    print(pairs_long_ouvertes)
SumPnl = 0
for i in Pnl.values():
    SumPnl += i

# Recupère le prix actuel de chaque crypto (en soit on a déjà la fonction getPrixAchat() qui nous permet de connaitre ce prix, mais ça nous permet d'éviter d'appeler régulièrement l'API)
actualPrice = {}
for perpSymbol in perpList:
    try :
        actualPrice[perpSymbol] = dfList[perpSymbol].iloc[-2]["close"]
    except :
        perpList.remove(perpSymbol)
        actualPrice[perpSymbol] = getCurrentPrice(perpSymbol)


# ===================================
#  RECUPERE LA DATE EXACTE DU JOUR
# ===================================

date = datetime.datetime.now()
todayJour = date.day
todayMois = date.month
todayAnnee = date.year
todayHeure = date.hour
todayMinutes = date.minute
separateDate = str(date).split(".")
date = str(separateDate[0])
heureComplète = str(separateDate[1])


# On commence à créer le contenu de la notification Telegram
addMessageComponent(f"{date}\n{botname} v{version}")
addMessageComponent("===================\n")

maxOpenPosition = int(config["STRATEGIE"]["maxPositions"])
maxPositions=maxOpenPosition

# A ce stade du code, on a récupéré toutes les informations nécessaires nous permettant de traiter les données.
# On connait l'état du bot : nombres positions ouvertes, date, solde, etc.
# On connait l'état du marché : bougies précedentes sur les cryptos qui nous intéressent, etc.
# On va désormais générer des indicateurs et prendre des décisions sur la fermeture ou l'ouverture de nouvelle position

dfList = load_indicators(dfList, dfListSorted, indicators["params"])

# Si on utilise un takeprofit ou non
useTakeProfit = str(config["STRATEGIE"]["useTakeProfit"])

# Si on utilise un stoploss de sécurité pour éviter la liquidation
useStoploss = str(config["STRATEGIE"]["useStoploss"])

# On notifie dans les logs l'utilisation du takeprofit et du stoploss :
if useTakeProfit == "true":
    print(f"TakeProfit est activé.")
else:
    print("TakeProfit n'est pas activé.")
if useStoploss == "true":
    print("Stoploss est activé")
else:
    print("Stoploss n'est pas activé.")

# Variable permettant de savoir combien de changements ont eu lieu, on l'incrémente à chaque action.
changement = 0

# ====================================================================
#                    FONCTION PRINCIPALE DU BOT :
#    • PLACE LES ORDRES LIMITE D'ACHAT ET DE VENTE SUR FTX
#    • GERE LES ERREURS VIA UNE NOTIF TELEGRAM EN CAS DE PROBLEME
# ====================================================================

ordresLong = []
ordresShort = []
ordresCloseLong = []
ordresCloseShort = []

def placeOrder(order, perpSymbol, quantityMax, price, leverage, position):
    global changement
    global openPositions
    global actualPrice
    global usdAmount
    global maxOpenPosition
    global usdAllocated
    global Pnl
    global amount
    global ordresLong
    global ordresShort
    global useLimitOrderToOpen
    global useLimitOrderToClose

    # En cas de prix négatif (parfois ça arrive, je ne sais pas pourquoi)
    if price < 0.0:
        price = price * -1
    # Dans le cadre d'une position LONG
    if position == "LONG":
        # Si on souhaite ouvrir une position LONG
        if order == "open":
            if useLimitOrderToOpen == "false":
                try:
                    ftx.place_market_order(
                        perpSymbol, "buy", quantityMax, leverage=leverage
                    )
                    changement = changement + 1
                    openPositions += 1
                    print("Ouverture de position LONG : ", quantityMax, perpSymbol)
                    addMessageComponent(f"OPEN LONG :")
                    addMessageComponent(f" • {quantityMax} {perpSymbol}")
                    addMessageComponent(f" • Prix du marché : {price} $\n")
                    if showURLonTelegramNotif == "true":
                        addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
                    with open(
                        path + str(config["FICHIER.HISTORIQUE"]["positionFile"]), "a"
                    ) as f:
                        f.write(
                            f"{date} | {order} {position} {quantityMax} {perpSymbol} at {price} \n"
                        )
                except Exception as err:
                    # Si l'erreur est un manque de provision d'USD
                    print(f"Impossible d'ouvrir une position LONG sur {perpSymbol}")
                    if "Account does not have enough margin for order." in str(err):
                        # On réduit le prix d'achat de 10%
                        print(
                            f"Impossible d'ouvrir l'ordre pour {perpSymbol} à {price}$"
                        )
                        quantityMax = quantityMax * 0.7
                        print(f"On reessaye à {quantityMax*price}$")
                        try:
                            ftx.place_market_order(
                                perpSymbol, "buy", quantityMax, leverage=leverage
                            )
                            changement = changement + 1
                            openPositions += 1

                            print(
                                "Ouverture de position LONG : ", quantityMax, perpSymbol
                            )
                            addMessageComponent(f"OPEN LONG :")
                            addMessageComponent(f" • {quantityMax} {perpSymbol}")
                            addMessageComponent(f" • Prix du marché : {price} $")
                            if showURLonTelegramNotif == "true":
                                addMessageComponent(
                                    f" • https://ftx.com/trade/{perpSymbol}\n"
                                )
                            with open(
                                path
                                + str(config["FICHIER.HISTORIQUE"]["positionFile"]),
                                "a",
                            ) as f:
                                f.write(
                                    f"{date} | {order} {position} {quantityMax} {perpSymbol} at {price} \n"
                                )
                        except Exception as err:
                            print(
                                f"Même en baissant la quantité initiale de 30% : une erreur est survenue lors de l'ouverture d'une position LONG de {quantityMax} {perpSymbol}"
                            )
                            print("Détails :", err)
                            telegram_send.send(
                                messages=[
                                    f"{botname} : Une erreur est survenue lors de l'ouverture d'une position LONG de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité.\n\nDétails : {err}"
                                ]
                            )
                    else:
                        if "Size too small" in str(err):
                            print(
                                f"Vous n'avez pas suffisamment d'USD pour l'ouverture d'une position LONG de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité."
                            )
                            print("Détails :", err)
                            telegram_send.send(
                                messages=[
                                    f"{botname} : Vous n'avez pas suffisamment d'USD pour l'ouverture d'une position LONG de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité.\n\nDétails : {err}"
                                ]
                            )
                        else:
                            print(
                                f"Une erreur est survenue lors de l'ouverture d'une position LONG de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité."
                            )
                            print("Détails :", err)
                            telegram_send.send(
                                messages=[
                                    f"{botname} : Une erreur est survenue lors de l'ouverture d'une position LONG de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité.\n\nDétails : {err}"
                                ]
                            )
            else:
                if price > 10000:
                    price = getCurrentPrice(perpSymbol) * 0.99999
                elif price > 1000:
                    price = getCurrentPrice(perpSymbol) * 0.99995
                else:
                    price = getCurrentPrice(perpSymbol) * 0.99990
                try:
                    ftx.place_limit_order(
                        perpSymbol, "buy", quantityMax, price=price, leverage=leverage
                    )
                    changement = changement + 1
                    openPositions += 1
                    ordresLong.append(perpSymbol)
                    print(
                        f"Ordre limite placé à {price} pour ouvrir une position LONG : ",
                        quantityMax,
                        perpSymbol,
                    )
                    addMessageComponent(f"OPEN LONG :")
                    addMessageComponent(f" • {quantityMax} {perpSymbol}")
                    addMessageComponent(f" • Prix de l'ordre limite : {price} $\n")
                    if showURLonTelegramNotif == "true":
                        addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
                except Exception as err:
                    # Si l'erreur est un manque de provision d'USD
                    print(
                        f"Impossible d'ouvrir un ordre limite à {price} pour ouvrir une position long sur {perpSymbol}"
                    )
                    if "Account does not have enough margin for order." in str(err):
                        # On réduit le prix d'achat de 10%
                        print(
                            f"Impossible d'ouvrir l'ordre pour {perpSymbol} à {price}$"
                        )
                        quantityMax = quantityMax * 0.7
                        print(f"On reessaye à {quantityMax*price}$")
                        try:
                            ftx.place_limit_order(
                                perpSymbol,
                                "buy",
                                quantityMax,
                                price=price,
                                leverage=leverage,
                            )
                            changement = changement + 1
                            openPositions += 1
                            ordresLong.append(perpSymbol)
                            print(
                                f"Ordre limite placé à {price} pour ouvrir une position LONG : ",
                                quantityMax,
                                perpSymbol,
                            )
                            addMessageComponent(f"OPEN LONG :")
                            addMessageComponent(f" • {quantityMax} {perpSymbol}")
                            addMessageComponent(
                                f" • Prix de l'ordre limite : {price} $\n"
                            )
                            if showURLonTelegramNotif == "true":
                                addMessageComponent(
                                    f" • https://ftx.com/trade/{perpSymbol}\n"
                                )
                        except Exception as err:
                            print(
                                f"Même en baissant la quantité initiale de 30% : une erreur est survenue lors de l'ouverture d'une position LONG de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité."
                            )
                            print("Détails :", err)
                            telegram_send.send(
                                messages=[
                                    f"{botname} : Une erreur est survenue lors du placement d'un ordre limite pour ouvrir une position LONG de {quantityMax} {perpSymbol}, au prix de {price} $ unité.\n\nDétails : {err}"
                                ]
                            )
                    else:
                        if "Size too small" in str(err):
                            print(
                                f"Vous n'avez pas suffisamment d'USD pour placer un ordre limite qui ouvrira une position long de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité."
                            )
                            print("Détails :", err)
                        else:
                            print(
                                f"Une erreur est survenue lors du placement d'un ordre limite pour ouvrir une position LONG de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité."
                            )
                            print("Détails :", err)
        # Si on souhaite fermer une position LONG
        elif order == "close":
            if useLimitOrderToClose == "false" or (
                nbOfLongPositionsAvailable + nbOfShortPositionsAvailable > 0
            ):
                try:
                    profit = float(getProfit(perpSymbol))
                    prixAchat = getPrixAchat(perpSymbol)
                    currentPrice = getCurrentPrice(perpSymbol)
                    performance = getPerformance(perpSymbol)
                    levier = getLevier(perpSymbol)
                    ftx.close_open_position(symbol=perpSymbol)
                    changement = changement + 1
                    openPositions -= 1
                    ordresCloseLong.append(perpSymbol)

                    print("Fermeture de position LONG : ", perpSymbol, "à", price)
                    addMessageComponent(f"CLOSE LONG :")
                    addMessageComponent(f" • {perpSymbol}")
                    if profit > 0:
                        addMessageComponent(f" • Profit de +{profit} $")
                    else:
                        addMessageComponent(f" • Perte de {profit} $")
                    addMessageComponent(f" • Prix d'achat :  {prixAchat} $")
                    addMessageComponent(f" • Prix actuel : {currentPrice} $")
                    addMessageComponent(f" • Performance : {performance}%")
                    addMessageComponent(f" • Levier : {levier}")

                    if showURLonTelegramNotif == "true":
                        addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
                    addMessageComponent(" ")
                    with open(
                        path + str(config["FICHIER.HISTORIQUE"]["positionFile"]), "a"
                    ) as f:
                        f.write(
                            f"{date} | {order} {position} {quantityMax} {perpSymbol} at {price} \n"
                        )
                except Exception as err:
                    print(
                        f"Une erreur est survenue lors de la fermeture de {quantityMax} {perpSymbol}, au prix de {price} $ unité : {err}"
                    )
                    print("Détails :", err)
                    telegram_send.send(
                        messages=[
                            f"{botname} : Une erreur est survenue lors de la vente de {quantityMax} {perpSymbol}, au prix de {price} $ unité\nDétails : {err}"
                        ]
                    )
            else:
                if price > 10000:
                    price = getCurrentPrice(perpSymbol) * 1.00001
                elif price > 1000:
                    price = getCurrentPrice(perpSymbol) * 1.00005
                else:
                    price = getCurrentPrice(perpSymbol) * 1.0001
                try:
                    profit = float(getProfit(perpSymbol))
                    prixAchat = getPrixAchat(perpSymbol)
                    currentPrice = getCurrentPrice(perpSymbol)
                    performance = getPerformance(perpSymbol)
                    levier = getLevier(perpSymbol)
                    ftx.place_reduce_limit_order(
                        perpSymbol, "sell", quantityMax, price=price, leverage=leverage
                    )
                    changement = changement + 1
                    ordresCloseLong.append(perpSymbol)
                    print(
                        f"Ordre limite placé à {price} pour fermer une position LONG : ",
                        quantityMax,
                        perpSymbol,
                    )
                    addMessageComponent(f"CLOSE LONG :")
                    addMessageComponent(f" • {quantityMax} {perpSymbol}")
                    addMessageComponent(f" • Prix de l'ordre limite : {price} $\n")
                    if showURLonTelegramNotif == "true":
                        addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
                except Exception as err:
                    print(
                        f"Une erreur est survenue lors de la mise en place d'un ordre limite de fermeture de position : {quantityMax} {perpSymbol}, au prix de {price} $ unité : {err}"
                    )
                    print("Détails :", err)
                    useLimitOrderToClose = "false"
                    price = ftx.get_bid_ask_price(symbol=perpSymbol)["ask"]
                    placeOrder("close", perpSymbol, quantityMax, price, leverage, position)
                    useLimitOrderToClose = "true"
                    
        # Pour mettre un takeprofit
        elif order == "takeProfit":
            try:
                ftx.place_market_take_profit(
                    perpSymbol, "sell", quantityMax*2, price=price, leverage=leverage
                )
                changement = changement + 1
                print(
                    "TakeProfit : Open limit order for close my LONG position on",
                    perpSymbol,
                    "at",
                    price,
                )
            except Exception as err:
                print(
                    f"TakeProfit : Une erreur est survenue lors de la mise en place d'un takeprofit de {quantityMax} {perpSymbol}, à un prix de {price} $ unité"
                )
                print("Détails :\n", Exception, err)
                # telegram_send.send(messages=[f"{botname} : Une erreur est survenue lors de la mise en place d'un takeprofit de {getQuantite(perpSymbol)} {perpSymbol}, à un prix de {price} $ unité : {err}"])
        # Pour mettre un stoploss
        elif order == "securityStopLoss":
            try:
                ftx.place_market_stop_loss(
                    perpSymbol, "sell", quantityMax, price=price, leverage=leverage
                )
                print("SecurityStopLoss : StopLoss placé sur ", perpSymbol, "à", price)
            except Exception as err:
                print(
                    f"SecurityStopLoss : Une erreur est survenue lors de la mise en place d'un stoploss de {quantityMax} {perpSymbol}, à un prix de {price} $ unité\nDétails : {err}"
                )
                print("Détails :", err)
                # telegram_send.send(messages=[f"{botname} : Une erreur est survenue lors de la mise en place d'un stoploss de {getQuantite(perpSymbol)} {perpSymbol}, à un prix de {price} $ unité\nDétails : {err}"])
    # Dans le cadre d'une position SHORT
    elif position == "SHORT":
        # Si on souhaite ouvrir une position SHORT
        if order == "open":
            if useLimitOrderToOpen == "false" or (
                nbOfLongPositionsAvailable + nbOfShortPositionsAvailable > 0
            ):
                try:
                    ftx.place_market_order(
                        perpSymbol, "sell", quantityMax, leverage=leverage
                    )
                    changement = changement + 1
                    openPositions += 1
                    print("Ouverture de position SHORT : ", quantityMax, perpSymbol)
                    addMessageComponent(f"OPEN SHORT :")
                    addMessageComponent(f" • {quantityMax} {perpSymbol}")
                    addMessageComponent(f" • Prix du marché : {price} $\n")
                    if showURLonTelegramNotif == "true":
                        addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
                    with open(
                        path + str(config["FICHIER.HISTORIQUE"]["positionFile"]), "a"
                    ) as f:
                        f.write(
                            f"{date} | {order} {position} {quantityMax} {perpSymbol} at {price} \n"
                        )
                except Exception as err:
                    # Si l'erreur est un manque de provision d'USD
                    print(f"Impossible d'ouvrir une position SHORT sur {perpSymbol}")
                    if "Account does not have enough margin for order." in str(err):
                        # On réduit le prix d'achat de 10%
                        print(
                            f"Impossible d'ouvrir l'ordre pour {perpSymbol} à {price}$"
                        )
                        quantityMax = quantityMax * 0.7
                        print(f"On reessaye à {quantityMax*price}$")
                        try:
                            ftx.place_market_order(
                                perpSymbol, "sell", quantityMax, leverage=leverage
                            )

                            changement = changement + 1
                            openPositions += 1

                            print("Achat de ", quantityMax, perpSymbol)
                            addMessageComponent(f"OPEN SHORT :")
                            addMessageComponent(f" • {quantityMax} {perpSymbol}")
                            addMessageComponent(f" • Prix du marché : {price} $")
                            if showURLonTelegramNotif == "true":
                                addMessageComponent(
                                    f" • https://ftx.com/trade/{perpSymbol}\n"
                                )
                            with open(
                                path
                                + str(config["FICHIER.HISTORIQUE"]["positionFile"]),
                                "a",
                            ) as f:
                                f.write(
                                    f"{date} | {order} {position} {quantityMax} {perpSymbol} at {price} \n"
                                )
                        except:
                            print(
                                f"Même en baissant la quantité initiale de 10% : une erreur est survenue lors de l'achat de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité."
                            )
                            print("Détails :", err)
                            telegram_send.send(
                                messages=[
                                    f"{botname} : Une erreur est survenue lors de l'achat de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité.\n\nDétails : {err}"
                                ]
                            )
                    else:
                        print(
                            f"Une erreur est survenue lors de l'achat de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité."
                        )
                        print("Détails :", err)
                        telegram_send.send(
                            messages=[
                                f"{botname} : Une erreur est survenue lors de l'achat de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité.\n\nDétails : {err}"
                            ]
                        )
            else:
                if price > 10000:
                    price = getCurrentPrice(perpSymbol) * 1.00001
                elif price > 1000:
                    price = getCurrentPrice(perpSymbol) * 1.00005
                elif price > 100:
                    price = getCurrentPrice(perpSymbol) * 1.0001
                elif price > 10:
                    price = getCurrentPrice(perpSymbol) * 1.0001
                else:
                    price = getCurrentPrice(perpSymbol) * 1.0001
                try:
                    ftx.place_limit_order(
                        perpSymbol, "sell", quantityMax, price=price, leverage=leverage
                    )
                    changement = changement + 1
                    openPositions += 1
                    ordresShort.append(perpSymbol)
                    print(
                        f"Ouverture d'un ordre limite à {price} pour ouvrir une position SHORT : ",
                        quantityMax,
                        perpSymbol,
                    )
                    addMessageComponent(f"OPEN SHORT :")
                    addMessageComponent(f" • {quantityMax} {perpSymbol}")
                    addMessageComponent(f" • Prix de l'ordre : {price} $\n")
                    if showURLonTelegramNotif == "true":
                        addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
                except Exception as err:
                    # Si l'erreur est un manque de provision d'USD
                    print(
                        f"Impossible de placer un ordre limite pour ouvrir une position SHORT sur {perpSymbol} à un prix de {price}"
                    )
                    if "Account does not have enough margin for order." in str(err):
                        # On réduit le prix d'achat de 10%
                        print(
                            f"Impossible d'ouvrir l'ordre pour {perpSymbol} à {price}$"
                        )
                        quantityMax = quantityMax * 0.7
                        print(f"On reessaye avec {quantityMax} {perpSymbol}")
                        try:
                            ftx.place_limit_order(
                                perpSymbol,
                                "sell",
                                quantityMax,
                                price=price,
                                leverage=leverage,
                            )
                            changement = changement + 1
                            openPositions += 1
                            ordresShort.append(perpSymbol)
                            print(
                                f"Ouverture d'un ordre limite à {price} pour ouvrir une position SHORT : ",
                                quantityMax,
                                perpSymbol,
                            )
                            addMessageComponent(f"OPEN SHORT :")
                            addMessageComponent(f" • {quantityMax} {perpSymbol}")
                            addMessageComponent(f" • Prix de l'ordre : {price} $\n")
                            if showURLonTelegramNotif == "true":
                                addMessageComponent(
                                    f" • https://ftx.com/trade/{perpSymbol}\n"
                                )
                        except:
                            print(
                                f"Même en baissant la quantité initiale de 10% : une erreur est survenue lors de l'achat de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité."
                            )
                            print("Détails :", err)
                            telegram_send.send(
                                messages=[
                                    f"{botname} : Une erreur est survenue lors de l'achat de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité.\n\nDétails : {err}"
                                ]
                            )
                    else:
                        print(
                            f"Une erreur est survenue lors de l'achat de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité."
                        )
                        print("Détails :", err)
                        telegram_send.send(
                            messages=[
                                f"{botname} : Une erreur est survenue lors de l'achat de {quantityMax} {perpSymbol}, au prix de {getCurrentPrice(perpSymbol)} $ unité.\n\nDétails : {err}"
                            ]
                        )
        # Si on souhaite fermer une position SHORT
        elif order == "close":
            if useLimitOrderToClose == "false":
                try:
                    profit = float(getProfit(perpSymbol))
                    prixAchat = getPrixAchat(perpSymbol)
                    currentPrice = getCurrentPrice(perpSymbol)
                    performance = getPerformance(perpSymbol)
                    levier = getLevier(perpSymbol)
                    ftx.close_open_position(symbol=perpSymbol)
                    changement = changement + 1
                    openPositions -= 1

                    print("Fermeture de position SHORT : ", perpSymbol, "à", price)
                    addMessageComponent(f"CLOSE SHORT :")
                    addMessageComponent(f" • {perpSymbol}")
                    if profit > 0:
                        addMessageComponent(f" • Profit de +{profit} $")
                    else:
                        addMessageComponent(f" • Perte de {profit} $")
                    addMessageComponent(f" • Prix d'achat :  {prixAchat} $")
                    addMessageComponent(f" • Prix actuel : {currentPrice} $")
                    addMessageComponent(f" • Performance : {performance}%")
                    addMessageComponent(f" • Levier : {levier}")

                    if showURLonTelegramNotif == "true":
                        addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
                    addMessageComponent(" ")
                    with open(
                        path + str(config["FICHIER.HISTORIQUE"]["positionFile"]), "a"
                    ) as f:
                        f.write(
                            f"{date} | {order} {position} {quantityMax} {perpSymbol} at {price} \n"
                        )
                except Exception as err:
                    print(
                        f"Une erreur est survenue lors de la fermeture d'une position SHORT de {getQuantite(perpSymbol)} {perpSymbol}, au prix de {price} $ unité"
                    )
                    print("Détails :", err)
                    telegram_send.send(
                        messages=[
                            f"{botname} : Une erreur est survenue lors de la vente de {getQuantite(perpSymbol)} {perpSymbol}, au prix de {price} $ unité\nDétails : {err}"
                        ]
                    )
            else:
                if price > 10000:
                    price = getCurrentPrice(perpSymbol) * 0.99999
                elif price > 1000:
                    price = getCurrentPrice(perpSymbol) * 0.99995
                else:
                    price = getCurrentPrice(perpSymbol) * 0.99990
                try:
                    profit = float(getProfit(perpSymbol))
                    prixAchat = getPrixAchat(perpSymbol)
                    currentPrice = getCurrentPrice(perpSymbol)
                    performance = getPerformance(perpSymbol)
                    levier = getLevier(perpSymbol)
                    ftx.place_reduce_limit_order(
                        perpSymbol, "buy", quantityMax, price=price, leverage=leverage
                    )
                    changement = changement + 1
                    ordresCloseShort.append(perpSymbol)
                    print(
                        f"Ordre limite placé à {price} pour fermer une position SHORT : ",
                        quantityMax,
                        perpSymbol,
                    )
                    addMessageComponent(f"CLOSE SHORT :")
                    addMessageComponent(f" • {quantityMax} {perpSymbol}")
                    addMessageComponent(f" • Prix de l'ordre limite : {price} $\n")
                    if showURLonTelegramNotif == "true":
                        addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
                except Exception as err:
                    print(
                        f"Une erreur est survenue lors de la mise en place d'un ordre limite de fermeture de position : {quantityMax} {perpSymbol}, au prix de {price} $ unité : {err}"
                    )
                    print("Détails :", err)
                    useLimitOrderToClose = "false"
                    price = ftx.get_bid_ask_price(symbol=perpSymbol)["ask"]
                    placeOrder("close", perpSymbol, quantityMax, price, leverage, position)
                    useLimitOrderToClose = "true"
        # Si on souhaite placer un takeprofit
        elif order == "takeProfit":
            try:
                ftx.place_market_take_profit(
                    perpSymbol, "buy", quantityMax*2, price=price, leverage=leverage
                )
                changement = changement + 1
                print(
                    "TakeProfit : Open limit order for close my SHORT position on",
                    perpSymbol,
                    "at",
                    price,
                )
            except Exception as err:
                print(
                    f"TakeProfit : Une erreur est survenue lors de la mise en place d'un takeprofit de {getQuantite(perpSymbol)} {perpSymbol}, à un prix de {price} $ unité"
                )
                print("Détails :\n", Exception, err)
                # telegram_send.send(messages=[f"{botname} : Une erreur est survenue lors de la mise en place d'un takeprofit de {getQuantite(perpSymbol)} {perpSymbol}, à un prix de {price} $ unité : {err}"])
        # Si on souhaite placer un stoploss
        elif order == "securityStopLoss":
            try:
                ftx.place_market_stop_loss(
                    perpSymbol, "buy", quantityMax, price=price, leverage=leverage
                )
                print("SecurityStopLoss : StopLoss placé sur ", perpSymbol, "à", price)
            except Exception as err:
                print(
                    f"SecurityStopLoss : Une erreur est survenue lors de la mise en place d'un stoploss de {getQuantite(perpSymbol)} {perpSymbol}, à un prix de {price} $ unité\nDétails : {err}"
                )
                print("Détails :", err)
                # telegram_send.send(messages=[f"{botname} : Une erreur est survenue lors de la mise en place d'un stoploss de {getQuantite(perpSymbol)} {perpSymbol}, à un prix de {price} $ unité\nDétails : {err}"])


# ==================================================
#          EXECUTION DE SECURITE DU BOT :
# ==================================================

def close_all_positions():
    global useLimitOrderToClose
    global perpList
    global pairs_long_ouvertes
    global pairs_short_ouverte
    useLimitOrderToClose='false'
    i=0
    for perpSymbol in perpList :
        if perpSymbol in pairs_long_ouvertes or perpSymbol in pairs_short_ouvertes :
            i=i+1
            if perpSymbol in pairs_long_ouvertes :
                time.sleep(1)
                quantityMaxsell = getQuantite(perpSymbol)
                if quantityMaxsell is None:
                    quantityMaxsell = 10000000
                # Créer une position de vente sur le marché pour cette crypto
                price = ftx.get_bid_ask_price(symbol=perpSymbol)["ask"]
                placeOrder(
                    "close", perpSymbol, quantityMaxsell, price, leverage, position="LONG"
                )
            if perpSymbol in pairs_short_ouvertes :
                time.sleep(1)
                quantityMaxsell = getQuantite(perpSymbol)
                if quantityMaxsell is None:
                    quantityMaxsell = 10000000
                # Créer une position de vente sur le marché pour cette crypto
                price = ftx.get_bid_ask_price(symbol=perpSymbol)["ask"]
                placeOrder(
                    "close", perpSymbol, quantityMaxsell, price, leverage, position="SHORT"
                )
    if i==0 :
        print("Aucune position n'est ouverte : aucune position à fermer.")

if usdAmount<=stopTheBotIfSoldeDownBelow :
    print(f"Solde inférieur à {stopTheBotIfSoldeDownBelow}$ : perte maximum tolérée atteinte.")
    #On défini useLimitOrderToClose sur false pour que les positions se ferment automatiquement.
    close_all_positions()
    print(f"DANGER : Votre bot est descendu sous {stopTheBotIfSoldeDownBelow}$, toutes les positions potentiellement ouvertes ont été fermées et on a stoppé l'execution.")
    print(f"Pour relancer le bot, diminuez la valeur de 'stopTheBotIfSoldeDownBelow' à un montant inférieur à votre solde ou ajouter de l'USD sur votre compte.")
    exit(0)
    

# ==================================================
#          EXECUTION PRINCIPALE DU BOT :
#
# • VERIFIE NOS POSITIONS OUVERTES ET DETERMINE :
#     • Si on doit les fermer
#     • Si on doit les garder
# • VERIFIE SI IL Y A DES OPPORTUNITEES DE POSITIONS A OUVRIR
#
# ==================================================

config = configparser.ConfigParser()
config.read(path + "config-bot.cfg")
indicators = configparser.ConfigParser()
parametersFile = str(config["FICHIER.HISTORIQUE"]["parametersFile"])
indicators.read(path + parametersFile)

# Permet de lister les cryptos que le bot souhaite acheter (indépendemment du nombre maximum de position)
# Cela permet d'avoir un ordre d'idée du nombre d'opportunitées manquées à cause de la limitation maxOpenPositions
nbOfLongPositionsAvailable = 0
nbOfShortPositionsAvailable = 0
for perpSymbol in dfList:
    if (
        openLongCondition(
            dfList[perpSymbol].iloc[-2],
            dfList[perpSymbol].iloc[-3],
            dfList,
            indicators["params"],
        )
        == True
    ):
        print(perpSymbol + " est en position d'achat LONG")
        addPositionLONG(f"{perpSymbol}")
        nbOfLongPositionsAvailable += 1
    if (
        openShortCondition(
            dfList[perpSymbol].iloc[-2],
            dfList[perpSymbol].iloc[-3],
            dfList,
            indicators["params"],
        )
        == True
    ):
        print(perpSymbol + " est en position d'achat SHORT")
        addPositionSHORT(f"{perpSymbol}")
        nbOfShortPositionsAvailable += 1

currentCrypto = ""

addMessageComponent("Actions prises par le bot :\n")

nbLong = 0
nbShort = 0

check()

for perpSymbol in perpList:
    currentCrypto = perpSymbol
    # On vérifie si on a une position long ouverte
    if perpSymbol in pairs_long_ouvertes:
        # On vérifie si on doit fermer notre position long ouverte en (bear ou en bull)
        if (
            closeLongCondition(
                dfList[perpSymbol].iloc[-2],
                dfList[perpSymbol].iloc[-3],
                dfList,
                indicators["params"],
            )
            == True
        ):
            time.sleep(1)
            quantityMaxsell = getQuantite(perpSymbol)
            # Créer une position de vente sur le marché pour cette crypto
            price = ftx.get_bid_ask_price(symbol=perpSymbol)["ask"]
            placeOrder(
                "close",
                perpSymbol,
                getQuantite(perpSymbol),
                price,
                leverage,
                position="LONG",
            )
        else:
            print(f"On maintient notre position long sur {perpSymbol}")
            addMessageComponent(f"Maintient de position LONG :")
            addMessageComponent(f" • {getQuantite(perpSymbol)} {perpSymbol}")
            if float(getProfit(perpSymbol)) > 0:
                addMessageComponent(
                    f" • Profit de +{round(getProfit(perpSymbol), 3)} $"
                )
            else:
                addMessageComponent(f" • Perte de {round(getProfit(perpSymbol), 3)} $")
            addMessageComponent(f" • Prix d'achat :  {getPrixAchat(perpSymbol)} $")
            addMessageComponent(f" • Prix actuel : {getCurrentPrice(perpSymbol)} $")
            addMessageComponent(
                f" • Performance : {round(getPerformance(perpSymbol), 4)}%"
            )
            addMessageComponent(f" • Levier : {getLevier(perpSymbol)}")
            if showURLonTelegramNotif == "true":
                addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
            addMessageComponent(" ")
            nbLong += 1
    if perpSymbol in pairs_short_ouvertes:
        # On vérifie si on doit fermer notre position long ouverte en (bear ou en bull)
        if (
            closeShortCondition(
                dfList[perpSymbol].iloc[-2],
                dfList[perpSymbol].iloc[-3],
                dfList,
                indicators["params"],
            )
            == True
        ):
            time.sleep(1)
            quantityMaxsell = getQuantite(perpSymbol)
            if quantityMaxsell is None:
                quantityMaxsell = 10000000
            # Créer une position de vente sur le marché pour cette crypto
            price = ftx.get_bid_ask_price(symbol=perpSymbol)["ask"]
            placeOrder(
                "close", perpSymbol, quantityMaxsell, price, leverage, position="SHORT"
            )
        else:
            print(f"On maintient notre position short sur {perpSymbol}")
            addMessageComponent(f"Maintient de position SHORT :")
            addMessageComponent(f" • {getQuantite(perpSymbol)} {perpSymbol}")
            profit = float(getProfit(perpSymbol))
            if profit > 0:
                addMessageComponent(f" • Profit de +{round(profit, 3)} $")
            else:
                addMessageComponent(f" • Perte de {round(profit, 3)} $")
            addMessageComponent(f" • Prix d'achat :  {getPrixAchat(perpSymbol)} $")
            addMessageComponent(f" • Prix actuel : {getCurrentPrice(perpSymbol)} $")
            addMessageComponent(
                f" • Performance : {round(getPerformance(perpSymbol), 4)}%"
            )
            addMessageComponent(f" • Levier : {getLevier(perpSymbol)}")
            if showURLonTelegramNotif == "true":
                addMessageComponent(f" • https://ftx.com/trade/{perpSymbol}\n")
            addMessageComponent(" ")
            nbShort += 1

#On regarde si le nombre de positions détenu est supérieur au nombre maximum de positions autorisé.
#Cela peut arriver si vous changez le nombre maximum de positions dans les configs durant une période d'utilisation du bot.
if openPositions > maxOpenPosition :
    print(f"Le nombre positions ouvertes dépasse le nombre de positions maximum autorisé ({openPositions}/{maxOpenPosition}), régulation des positions...")
    i=openPositions
    for perpSymbol in perpList :
        if perpSymbol in pairs_long_ouvertes or perpSymbol in pairs_short_ouvertes :
            if perpSymbol in pairs_long_ouvertes :
                time.sleep(1)
                quantityMaxsell = getQuantite(perpSymbol)
                if quantityMaxsell is None:
                    quantityMaxsell = 10000000
                # Créer une position de vente sur le marché pour cette crypto
                price = ftx.get_bid_ask_price(symbol=perpSymbol)["ask"]
                placeOrder(
                    "close", perpSymbol, quantityMaxsell, price, leverage, position="LONG"
                )
                i=i-1
            if perpSymbol in pairs_short_ouvertes :
                time.sleep(1)
                quantityMaxsell = getQuantite(perpSymbol)
                if quantityMaxsell is None:
                    quantityMaxsell = 10000000
                # Créer une position de vente sur le marché pour cette crypto
                price = ftx.get_bid_ask_price(symbol=perpSymbol)["ask"]
                placeOrder(
                    "close", perpSymbol, quantityMaxsell, price, leverage, position="SHORT"
                )
                i=i-1
            if i <= maxOpenPosition :
                print(f"Le nombre positions ouvertes par rapport au nombre de positions maximum a été régulé ({openPositions}/{maxOpenPosition}).")
                break

# On vérifie si on peut ouvrir une nouvelle position
if openPositions < maxOpenPosition :
    # Si la répartition des shorts et des longs est activé, cela signifie que l'on doit prendre autant de short que de long
    if str(config["STRATEGIE"]["repartitionLongAndShort"]) == "true" and config["STRATEGIE"]['useShort']=="true" and config["STRATEGIE"]['useLong']=="true":
        # Nombre de positions que l'on peut ouvrir
        longRestant = maxPositions/2 - nbLong
        shortRestant = maxPositions/2 - nbShort
        if shortRestant == 0 and longRestant == 0 and nbOfShortPositionsAvailable+nbOfLongPositionsAvailable>0 :
            availablePos = maxOpenPosition - openPositions
            shortRestant=shortRestant+1
            longRestant=longRestant+1
    else:
        longRestant = maxOpenPosition - openPositions
        shortRestant = maxOpenPosition - openPositions
    for perpSymbol in perpList:
        currentCrypto = perpSymbol
        if (
            perpSymbol not in pairs_long_ouvertes
            and str(config["STRATEGIE"]["useLong"]) == "true"
        ):
            if (
                openLongCondition(
                    dfList[perpSymbol].iloc[-2],
                    dfList[perpSymbol].iloc[-3],
                    dfList,
                    indicators["params"],
                )
                == True
                and openPositions < maxOpenPosition
                and longRestant > 0
            ):
                time.sleep(1)
                # On défini la quantité maximum de tokens qu'on va acheter avec nos USD
                freeUSD = getFreeUSDBalance()
                if freeUSD>soldeToSaveInvestisment or saveInvestisment=="true":
                    freeUSD=freeUSD-totalInvestment
                    print(f"Votre solde a dépassé {soldeToSaveInvestisment}$, on sauvegarde le solde initial et on utilise plus que {freeUSD}$ pour conserver les {totalInvestment}$ initiaux")
                    changeSaveInvestissement("true")
                if freeUSD <= 0.5:
                    print(
                        "Vous n'avez pas suffisamment d'USD disponible sur votre compte pour ouvrir une nouvelle position pour le moment"
                    )
                else:
                    if useFixAmountOfUSD == "true" :
                        if fixAmount>freeUSD :
                            print(f"Vous ne disposez pas de suffisamment d'USD pour ouvrir une position de {fixAmount}$.")
                            print(f"Vous pouvez baisser votre le montant fixe alloué à chaque position (fixAmount) ou alimenter votre compte en USD.")
                            break
                        else : 
                            usdForPosition = fixAmount
                    else :
                        usdForPosition = (
                            freeUSD / (maxOpenPosition - openPositions) * usdAllocated
                        )
                    # quantityMax = usdAmount/maxOpenPosition*usdAllocated
                    price = ftx.get_bid_ask_price(symbol=perpSymbol)["bid"] * 0.9990
                    
                    quantityMax = usdForPosition / price
                    if quantityMax <= float(ftx.get_min_order_amount(perpSymbol)):
                        print(
                            "Vous n'avez pas suffisamment d'USD pour prendre une position sur ",
                            perpSymbol,
                        )
                    else:
                        prixTakeProfit = getTakeprofit(
                            "long",
                            price,
                            dfList[perpSymbol].iloc[-2],
                            dfList[perpSymbol].iloc[-3],
                            dfList,
                            indicators["params"]
                        )
                        # Créer une prise position long sur le marché pour cette crypto
                        ftx.cancel_all_open_order(symbol=perpSymbol)
                        placeOrder(
                            "open",
                            perpSymbol,
                            quantityMax,
                            price,
                            leverage,
                            position="LONG",
                        )
                        placeOrder(
                            "takeProfit",
                            perpSymbol,
                            quantityMax,
                            prixTakeProfit,
                            leverage,
                            position="LONG",
                        )
                        placeOrder(
                            "securityStopLoss",
                            perpSymbol,
                            quantityMax,
                            getSecureStopLossPrice(perpSymbol, "long", price, leverage),
                            leverage,
                            position="LONG",
                        )
                        longRestant -= 1
            else:
                if str(config["CONFIGS"]["showPairsWithoutOpportunity"]) == "true":
                    print("Aucune opportunité en LONG à prendre sur", perpSymbol)
        if (
            perpSymbol not in pairs_short_ouvertes
            and str(config["STRATEGIE"]["useShort"]) == "true"
        ):
            # Si la crypto respecte une des conditions suivantes d'ouverture en bear ou en bull :
            if (
                openShortCondition(
                    dfList[perpSymbol].iloc[-2],
                    dfList[perpSymbol].iloc[-3],
                    dfList,
                    indicators["params"],
                )
                == True
                and openPositions < maxOpenPosition
                and shortRestant > 0
            ):
                time.sleep(1)
                freeUSD = getFreeUSDBalance()
                if freeUSD>soldeToSaveInvestisment or saveInvestisment=="true":
                    freeUSD=freeUSD-totalInvestment
                    print(f"Votre solde a dépassé {soldeToSaveInvestisment}$, on sauvegarde le solde initial et on utilise plus que {freeUSD}$ pour conserver les {totalInvestment}$ initiaux")
                    changeSaveInvestissement("true")
                if freeUSD <= 0.5:
                    print(
                        "Vous n'avez pas suffisamment d'USD disponible sur votre compte pour ouvrir une nouvelle position pour le moment"
                    )
                else:
                    if useFixAmountOfUSD == "true" :
                        if fixAmount>freeUSD :
                            print(f"Vous ne disposez pas de suffisamment d'USD pour ouvrir une position de {fixAmount}$.")
                            print(f"Vous pouvez baisser votre le montant fixe alloué à chaque position (fixAmount) ou alimenter votre compte en USD.")
                            break
                        else : 
                            usdForPosition = fixAmount
                    else :
                        usdForPosition = (
                            freeUSD / (maxOpenPosition - openPositions) * usdAllocated
                        )
                    price = ftx.get_bid_ask_price(symbol=perpSymbol)["bid"] * 0.9990
                    quantityMax = usdForPosition / price
                    if quantityMax <= float(ftx.get_min_order_amount(perpSymbol)):
                        print(
                            "Vous n'avez pas suffisamment d'USD pour prendre une position sur ",
                            perpSymbol,
                        )
                    else:
                        prixTakeProfit = getTakeprofit(
                            "short",
                            price,
                            dfList[perpSymbol].iloc[-2],
                            dfList[perpSymbol].iloc[-3],
                            dfList,
                            indicators["params"]
                        )
                        # Créer une prise position short sur le marché pour cette crypto
                        ftx.cancel_all_open_order(symbol=perpSymbol)
                        placeOrder(
                            "open",
                            perpSymbol,
                            quantityMax,
                            price,
                            leverage,
                            position="SHORT",
                        )
                        placeOrder(
                            "takeProfit",
                            perpSymbol,
                            quantityMax,
                            prixTakeProfit,
                            leverage,
                            position="SHORT",
                        )
                        placeOrder(
                            "securityStopLoss",
                            perpSymbol,
                            quantityMax,
                            getSecureStopLossPrice(
                                perpSymbol, "short", price, leverage
                            ),
                            leverage,
                            position="SHORT",
                        )
                        shortRestant -= 1
            else:
                if str(config["CONFIGS"]["showPairsWithoutOpportunity"]) == "true":
                    print("Aucune opportunité en SHORT à prendre sur", perpSymbol)

else:
    print("Nombre de position ouverte max atteint")
    # addMessageComponent(f"Positions maximums atteintes : {openPositions}/{maxOpenPosition}\n")
    addMessageComponent(f"Résultats totaux depuis les prises de positions : {SumPnl} $")

currentCrypto = ""

# Affiche cette liste dans la notification telegram
if len(positionLongList) + len(positionShortList) > 1:
    addMessageComponent(f"Position d'achat LONG :\n{positionLongList}")
    addMessageComponent(f"Position d'achat SHORT :\n{positionShortList}")

# Dans le cas où le bot ne fait aucune action
if openPositions == 0 and len(positionLongList) + len(positionShortList) == 0:
    addMessageComponent(f"Aucune.")

# ============================================
#   CODES NECESSAIRES POUR FAIRE DES BILANS
#    DE PERFORMANCES AU FIL DU TEMPS DANS
#       LA NOTIFICATION TELEGRAM FINALE
# ============================================

usdAmount = ftx.get_balance_of_one_coin("USD")
soldeMaxAnnee = usdAmount
soldeMaxMois = usdAmount
soldeMaxJour = usdAmount
soldeMinAnnee = usdAmount
soldeMinMois = usdAmount
soldeMinJour = usdAmount

jourMinAnnee = moisMinAnnee = anneeMinAnnee = heureMinAnnee = 0
jourMinMois = moisMinMois = anneeMinMois = heureMinMois = 0
jourMinJour = moisMinJour = anneeMinJour = heureMinJour = 0

jourMaxAnnee = moisMaxAnnee = anneeMaxAnnee = heureMaxAnnee = 0
jourMaxMois = moisMaxMois = anneeMaxMois = heureMaxMois = 0
jourMaxJour = moisMaxJour = anneeMaxJour = heureMaxJour = 0

if saveInvestisment=="true" :
    print(f"Solde du compte => {usdAmount} $ dont {soldeToSaveInvestisment}$ d'investissement initial sécurisé")
else :
    print(f"Solde du compte => {usdAmount} $")

# Récupérations des anciennes données dans le fichier historiques-soldes.dat
x = []
y = []
try:
    with open(path + str(config["FICHIER.HISTORIQUE"]["soldeFile"]), "r") as f:
        for line in f:
            if "#" in line:
                # on saute la ligne
                continue
            data = line.split()
            jour = int(data[0])
            mois = int(data[1])
            annee = int(data[2])
            heure = int(data[3])
            minutes = int(data[4])
            solde = float(data[5])
            x.append(f"{jour}-{mois}-{annee} {heure}:{minutes}")
            y.append(solde)

            # permet de trouver le jour où vous avez eu le plus petit solde cette année
            if soldeMinAnnee > solde and annee == todayAnnee:
                soldeMinAnnee = solde
                jourMinAnnee = jour
                moisMinAnnee = mois
                anneeMinAnnee = annee
                heureMinAnnee = heure

            # permet de trouver le jour où vous avez eu le plus petit solde ce mois-ci
            if soldeMinMois > solde and annee == todayAnnee and mois == todayMois:
                soldeMinMois = solde
                jourMinMois = jour
                moisMinMois = mois
                anneeMinMois = annee
                heureMinMois = heure

            # permet de trouver l'heure où vous avez eu le plus petit solde aujourd'hui
            if (
                soldeMinJour > solde
                and annee == todayAnnee
                and mois == todayMois
                and jour == todayJour
            ):
                soldeMinJour = solde
                jourMinJour = jour
                moisMinJour = mois
                anneeMinJour = annee
                heureMinJour = heure

            # permet de trouver le jour où vous avez eu le plus gros solde cette année
            if soldeMaxAnnee < solde and annee == todayAnnee:
                soldeMaxAnnee = solde
                jourMaxAnnee = jour
                moisMaxAnnee = mois
                anneeMaxAnnee = annee
                heureMaxAnnee = heure

            # permet de trouver le jour où vous avez eu le plus gros solde ce mois-ci
            if soldeMaxMois < solde and annee == todayAnnee and mois == todayMois:
                soldeMaxMois = solde
                jourMaxMois = jour
                moisMaxMois = mois
                anneeMaxMois = annee
                heureMaxMois = heure

            # permet de trouver l'heure où vous avez eu le plus gros solde aujourd'hui
            if (
                soldeMaxJour < solde
                and annee == todayAnnee
                and mois == todayMois
                and jour == todayJour
            ):
                soldeMaxJour = solde
                jourMaxJour = jour
                moisMaxJour = mois
                anneeMaxJour = annee
                heureMaxJour = heure

            # permet de trouver le solde de 6 heures auparavant
            if todayHeure <= 6:
                if (
                    (todayJour - 1 == jour)
                    and (todayMois == mois)
                    and (todayAnnee == annee)
                ):
                    if 24 - (6 - todayHeure) == heure:
                        solde6heures = solde
                elif (
                    todayJour == 1
                    and ((todayMois - 1 == mois) and (todayAnnee == annee))
                    or ((todayMois == 1) and (todayAnnee - 1 == annee) and (jour == 31))
                ):
                    if 24 - (6 - todayHeure) == heure:
                        solde6heures = solde
            elif (
                (todayHeure - 6 == heure)
                and (todayJour == jour)
                and (todayMois == mois)
                and (todayAnnee == annee)
            ):
                solde6heures = solde

            # permet de trouver le solde de 12 heures auparavant
            if todayHeure <= 12:
                if (
                    (todayJour - 1 == jour)
                    and (todayMois == mois)
                    and (todayAnnee == annee)
                ):
                    if 24 - (12 - todayHeure) == heure:
                        solde12heures = solde
                elif (
                    todayJour == 1
                    and ((todayMois - 1 == mois) and (todayAnnee == annee))
                    or ((todayMois == 1) and (todayAnnee - 1 == annee) and (jour == 31))
                ):
                    if 24 - (12 - todayHeure) == heure:
                        solde12heures = solde
            elif (
                (todayHeure - 12 == heure)
                and (todayJour == jour)
                and (todayMois == mois)
                and (todayAnnee == annee)
            ):
                solde12heures = solde
            # permet de trouver le solde de 1 jours auparavant
            if todayJour <= 1:
                if ((todayMois - 1 == mois) and (todayAnnee == annee)) or (
                    (todayMois == 1 and mois == 12) and (todayAnnee - 1 == annee)
                ):
                    if (
                        mois == 1
                        or mois == 3
                        or mois == 5
                        or mois == 7
                        or mois == 8
                        or mois == 10
                        or mois == 12
                    ):
                        if 31 - todayJour + 1 == jour:
                            solde1jours = solde
                    else:
                        if 30 - todayJour + 1 == jour:
                            solde1jours = solde
            elif (
                (todayJour - 1 == jour)
                and (todayMois == mois)
                and (todayAnnee == annee)
            ):
                solde1jours = solde
            # permet de trouver le solde de 3 jours auparavant
            if todayJour <= 3:
                if ((todayMois - 1 == mois) and (todayAnnee == annee)) or (
                    (todayMois == 1 and mois == 12) and (todayAnnee - 1 == annee)
                ):
                    if (
                        mois == 1
                        or mois == 3
                        or mois == 5
                        or mois == 7
                        or mois == 8
                        or mois == 10
                        or mois == 12
                    ):
                        if 31 - todayJour + 3 == jour:
                            solde3jours = solde
                    else:
                        if 30 - todayJour + 3 == jour:
                            solde3jours = solde
            elif (
                (todayJour - 3 == jour)
                and (todayMois == mois)
                and (todayAnnee == annee)
            ):
                solde3jours = solde

            # permet de trouver le solde de 7 jours auparavant
            if todayJour <= 7:
                if ((todayMois - 1 == mois) and (todayAnnee == annee)) or (
                    (todayMois == 1 and mois == 12) and (todayAnnee - 1 == annee)
                ):
                    if (
                        mois == 1
                        or mois == 3
                        or mois == 5
                        or mois == 7
                        or mois == 8
                        or mois == 10
                        or mois == 12
                    ):
                        if 31 - todayJour + 7 == jour:
                            solde7jours = solde
                    else:
                        if 30 - -todayJour + 7 == jour:
                            solde7jours = solde
            elif (
                (todayJour - 7 == jour)
                and (todayMois == mois)
                and (todayAnnee == annee)
            ):
                solde7jours = solde

            # permet de trouver le solde de 14 jours auparavant
            if todayJour <= 14:
                if ((todayMois - 1 == mois) and (todayAnnee == annee)) or (
                    (todayMois == 1 and mois == 12) and (todayAnnee - 1 == annee)
                ):
                    if (
                        mois == 1
                        or mois == 3
                        or mois == 5
                        or mois == 14
                        or mois == 8
                        or mois == 10
                        or mois == 12
                    ):
                        if 31 - todayJour + 14 == jour:
                            solde14jours = solde
                    else:
                        if 30 - todayJour + 14 == jour:
                            solde14jours = solde
            elif (
                (todayJour - 14 == jour)
                and (todayMois == mois)
                and (todayAnnee == annee)
            ):
                solde14jours = solde

            # permet de trouver le solde de 1 mois auparavant
            if (
                todayMois == 1
                and mois == 12
                and annee == todayAnnee - 1
                and todayJour == jour
            ):
                solde1mois = solde
            elif todayMois - 1 == mois and annee == todayAnnee and todayJour == jour:
                solde1mois = solde

            # permet de trouver le solde de 2 mois auparavant
            if (
                todayMois == 1
                and mois == 11
                and annee == todayAnnee - 1
                and todayJour == jour
            ):
                solde2mois = solde
            if (
                todayMois == 2
                and mois == 12
                and annee == todayAnnee - 1
                and todayJour == jour
            ):
                solde2mois = solde
            elif todayMois - 2 == mois and annee == todayAnnee and todayJour == jour:
                solde2mois = solde
        if "solde" in locals():
            soldeLastExec = solde
        else:
            soldeLastExec = usdAmount
except:
    heure=int(datetime.datetime.now().strftime('%H'))
    print(
        f"WARNING : Le fichier {str(config['FICHIER.HISTORIQUE']['soldeFile'])} est introuvable, il va être créé."
    )

# ==================================================
#  Enregistrement du solde dans le fichier .dat
# ==================================================

# On enregistre la date d'execution ainsi que le solde dans un fichier historiques-soldes.dat
todaySolde = usdAmount
with open(path + str(config["FICHIER.HISTORIQUE"]["soldeFile"]), "a") as f:
    f.write(
        f"{todayJour} {todayMois} {todayAnnee} {todayHeure} {todayMinutes} {todaySolde} \n"
    )
#Si l'heure est différente de la dernière heure enregistrée, on sauvegarde les données
if int(heure) != int(datetime.datetime.now().strftime('%H')) :
    filename=path + str(config["FICHIER.HISTORIQUE"]["soldeFile"])
    
    with open(filename.split(".")[0]+'-1h.'+filename.split(".")[1], "a") as f:
        f.write(
            f"{todayJour} {todayMois} {todayAnnee} {todayHeure} {todayMinutes} {todaySolde} {totalInvestment}\n"
        )

# On créer un graphique du solde à partir de ce fichier, on génère le fichier au format PDF
fig, ax = plt.subplots()
fig.set_figheight(20)
fig.set_figwidth(50)
plt.title(f"Solde {botname}")
plt.legend(prop={"size": 30})
plt.xlabel("Date", fontsize=20)
plt.ylabel("Solde", fontsize=20)
ax.plot(x, y)
ax.set_xticks(x[:: int(4000 / 50)])
ax.set_xticklabels(x[:: int(4000 / 50)], rotation=45)
ax.grid(axis="y")

try:
    plt.savefig(f"{path}data/solde-{botname}.pdf")
except Exception as err:
    print(f"Impossible de créer le fichier data/solde-{botname}.pdf")
    print(f"Détails : {err}")
    pass

# =======================================================
#  Affiche le bilan de perf dans le message telegram
# =======================================================

if notifBilanDePerformance == "true":
    addMessageComponent("\n===================\n")
    addMessageComponent("Bilan de performance :")
    if "soldeMaxJour" in locals():
        soldeMaxJour = round(soldeMaxJour, 3)
        addMessageComponent(
            f" - Best solde aujourd'hui : {soldeMaxJour}$ à {heureMaxJour}h"
        )
    if "soldeMaxMois" in locals():
        soldeMaxMois = round(soldeMaxMois, 3)
        addMessageComponent(
            f" - Best solde ce mois-ci : {soldeMaxMois}$ le {jourMaxMois}/{moisMaxMois} à {heureMaxMois}h"
        )
    if "soldeMaxAnnee" in locals():
        soldeMaxAnnee = round(soldeMaxAnnee, 3)
        addMessageComponent(
            f" - Best solde cette année : {soldeMaxAnnee}$ le {jourMaxAnnee}/{moisMaxAnnee}/{anneeMaxAnnee} à {heureMaxAnnee}h"
        )

    addMessageComponent(" ")

    if "soldeMinJour" in locals():
        soldeMinJour = round(soldeMinJour, 3)
        addMessageComponent(
            f" - Pire solde aujourd'hui : {soldeMinJour}$ à {heureMinJour}h"
        )
    if "soldeMinMois" in locals():
        soldeMinMois = round(soldeMinMois, 3)
        addMessageComponent(
            f" - Pire solde ce mois-ci : {soldeMinMois}$ le {jourMinMois}/{moisMinMois} à {heureMinMois}h"
        )
    if "soldeMinAnnee" in locals():
        soldeMinAnnee = round(soldeMinAnnee, 3)
        addMessageComponent(
            f" - Pire solde cette année : {soldeMinAnnee}$ le {jourMinAnnee}/{moisMinMois}/{anneeMinAnnee} à {heureMinAnnee}h"
        )

# =================================================================
#  Affiche le bilan d'évolution continue dans le message telegram
# =================================================================

if notifBilanEvolutionContinue == "true":
    addMessageComponent("\n===================\n")
    addMessageComponent("Bilan d'évolution continue :")
    if "soldeLastExec" in locals():
        bonus = 100 * (todaySolde - soldeLastExec) / soldeLastExec
        gain = bonus / 100 * soldeLastExec
        bonus = round(bonus, 3)
        gain = round(gain, 5)
        soldeLastExecRounded = round(soldeLastExec, 3)
        if gain < 0:
            addMessageComponent(
                f" - Dernière execution du bot : {bonus}% ({soldeLastExecRounded}$ {gain}$)"
            )
        else:
            addMessageComponent(
                f" - Dernière execution du bot : +{bonus}% ({soldeLastExecRounded}$ +{gain}$)"
            )
    if "solde6heures" in locals():
        bonus = 100 * (todaySolde - solde6heures) / solde6heures
        gain = round(bonus / 100 * todaySolde, 2)
        bonus = round(bonus, 3)
        gain = round(gain, 5)
        solde6heures = round(solde6heures, 3)
        if gain < 0:
            addMessageComponent(f" - il y a 6h : {bonus}% ({solde6heures}$ {gain}$)")
        else:
            addMessageComponent(f" - il y a 6h : +{bonus}% ({solde6heures}$ +{gain}$)")
    if "solde12heures" in locals():
        bonus = 100 * (todaySolde - solde12heures) / solde12heures
        gain = round(bonus / 100 * todaySolde, 2)
        bonus = round(bonus, 3)
        gain = round(gain, 5)
        solde12heures = round(solde12heures, 3)
        if gain < 0:
            addMessageComponent(f" - il y a 12h : {bonus}% ({solde12heures}${gain}$)")
        else:
            addMessageComponent(
                f" - il y a 12h : +{bonus}% ({solde12heures}$ +{gain}$)"
            )
    if "solde1jours" in locals():
        bonus = 100 * (todaySolde - solde1jours) / solde1jours
        gain = round(bonus / 100 * todaySolde, 2)
        bonus = round(bonus, 3)
        gain = round(gain, 5)
        solde1jours = round(solde1jours, 5)
        if gain < 0:
            addMessageComponent(f" - il y a 1j : {bonus}% ({solde1jours}$ {gain}$)")
        else:
            addMessageComponent(f" - il y a 1j : +{bonus}% ({solde1jours}$ +{gain}$)")
    if "solde3jours" in locals():
        bonus = 100 * (todaySolde - solde3jours) / solde3jours
        gain = round(bonus / 100 * todaySolde, 2)
        bonus = round(bonus, 3)
        gain = round(gain, 5)
        solde3jours = round(solde3jours, 3)
        if gain < 0:
            addMessageComponent(f" - il y a 3j : {bonus}% ({solde3jours}$ {gain}$)")
        else:
            addMessageComponent(f" - il y a 3j : +{bonus}% ({solde3jours}$ +{gain}$)")
    if "solde7jours" in locals():
        bonus = 100 * (todaySolde - solde7jours) / solde7jours
        gain = round(bonus / 100 * todaySolde, 2)
        bonus = round(bonus, 3)
        gain = round(gain, 5)
        solde7jours = round(solde7jours, 3)
        if gain < 0:
            addMessageComponent(f" - il y a 7j : {bonus}% ({solde7jours}$ {gain}$)")
        else:
            addMessageComponent(f" - il y a 7j : +{bonus}% ({solde7jours}$ +{gain}$)")
    if "solde14jours" in locals():
        bonus = 100 * (todaySolde - solde14jours) / solde14jours
        gain = round(bonus / 100 * todaySolde, 2)
        bonus = round(bonus, 3)
        gain = round(gain, 5)
        solde14jours = round(solde14jours, 3)
        if gain < 0:
            addMessageComponent(f" - il y a 14j : {bonus}% ({solde14jours}$ {gain}$)")
        else:
            addMessageComponent(f" - il y a 14j : +{bonus}% ({solde14jours}$ +{gain}$)")
    if "solde1mois" in locals():
        bonus = 100 * (todaySolde - solde1mois) / solde1mois
        gain = round(bonus / 100 * todaySolde, 2)
        bonus = round(bonus, 3)
        gain = round(gain, 5)
        solde1mois = round(solde1mois, 3)
        if gain < 0:
            addMessageComponent(f" - il y a 1 mois : {bonus}% ({solde1mois}$ {gain}$)")
        else:
            addMessageComponent(
                f" - il y a 1 mois : +{bonus}% ({solde1mois}$ +{gain}$)"
            )
    if "solde2mois" in locals():
        bonus = 100 * (todaySolde - solde2mois) / solde2mois
        gain = round(bonus / 100 * todaySolde, 2)
        bonus = round(bonus, 3)
        gain = round(gain, 5)
        solde2mois = round(solde2mois, 3)
        if gain < 0:
            addMessageComponent(f" - il y a 2 mois : {bonus}% ({solde2mois}$ {gain}$)")
        else:
            addMessageComponent(
                f" - il y a 2 mois : +{bonus}% ({solde2mois}$ +{gain}$)"
            )

totalInvestment = float(config["STRATEGIE"]["totalInvestment"])
bonus = 100 * (todaySolde - totalInvestment) / totalInvestment
gain = round((bonus / 100) * totalInvestment, 3)
bonus = round(bonus, 3)
totalInvestment = round(totalInvestment, 5)
addMessageComponent("\n===================\n")
addMessageComponent(f"INVESTISSEMENT INITIAL => {totalInvestment}$")
if gain < 0:
    addMessageComponent(f"PERTE TOTAL => {gain} $ ({bonus}%)\n")
else:
    addMessageComponent(f"GAIN TOTAL => +{gain} $ (+{bonus}%)\n")
if saveInvestisment == "true" :
    addMessageComponent(f"SOLDE TOTAL => {usdAmount}$ dont {soldeToSaveInvestisment}$ d'investissement initial sécurisé")
    addMessageComponent(f"SOLDE SECURISE => {soldeToSaveInvestisment}$")
else :
    addMessageComponent(f"SOLDE TOTAL => {usdAmount}$")

message = message.replace(" , ", " ")


# ======================================================
#  Se base sur les configurations pour déterminer s'il
#  faut vous envoyer une notification telegram ou non
# ======================================================

# Si on a activé de toujours recevoir la notification telegram
if alwaysNotifTelegram == "true":
    telegram_send.send(messages=[f"{message}"])
elif notifTelegramOnChangeOnly == "true" and changement > 0:
    telegram_send.send(messages=[f"{message}"])
elif notifTelegramOnChangeOnly == "false":
    if (
        changement == 0
        and (
            int(todayHeure) != 8
            and int(todayHeure) != 12
            and int(todayHeure) != 18
            and int(todayHeure) != 0
        )
        and todayMinutes == 0
    ):
        print(
            "Aucun changement de données, aucune information n'a été envoyé à Telegram"
        )
    else:
        print("Notif telegram envoyée")
        telegram_send.send(messages=[f"{message}"])
else:
    print("Aucun changement de données, aucune information n'a été envoyé à Telegram")

# On récupère les paires existantes
pairs_long_ouvertes = []
pairs_short_ouvertes = []
cointrades = ftx.get_open_position()
for cointrade in cointrades:
    if cointrade.get("side") == "long":
        pairs_long_ouvertes.append(cointrade.get("symbol"))
    if cointrade.get("side") == "short":
        pairs_short_ouvertes.append(cointrade.get("symbol"))

# Suppression de tout les ordres potentiellement ouvert et mises en place des takeprofits et des stop loss
# print("Fermeture des ordres dans 5 secondes...")

time.sleep(1)
if useLimitOrderToOpen == "false":
    for perpSymbol in perpList:
        try:
            ftx.cancel_all_open_order(perpSymbol)
        except:
            print(
                f"Une erreur est survenue en tentant d'annuler tous les ordres de la position {perpSymbol}"
            )
            # print(f"Détails : {e})
            pass
        # Si le SecureStopLoss est activé :
        if (
            perpSymbol in pairs_long_ouvertes or perpSymbol in pairs_short_ouvertes
        ) and useStoploss == "true":
            time.sleep(1)
            if perpSymbol in pairs_short_ouvertes:
                pos = "SHORT"
            if perpSymbol in pairs_long_ouvertes:
                pos = "LONG"
            prixAchat = getPrixAchat(perpSymbol)
            quantityMax = getQuantite(perpSymbol)
            levier = getLevier(perpSymbol)
            if perpSymbol in pairs_short_ouvertes:
                placeOrder(
                    "securityStopLoss",
                    perpSymbol,
                    quantityMax,
                    getSecureStopLossPrice(perpSymbol, "short", prixAchat, levier),
                    levier,
                    position=pos,
                )
            if perpSymbol in pairs_long_ouvertes:
                placeOrder(
                    "securityStopLoss",
                    perpSymbol,
                    quantityMax,
                    getSecureStopLossPrice(perpSymbol, "long", prixAchat, levier),
                    levier,
                    position=pos,
                )
        # Si le TakeProfit est activé :
        if (
            perpSymbol in pairs_long_ouvertes or perpSymbol in pairs_short_ouvertes
        ) and useTakeProfit == "true":
            time.sleep(1)
            if perpSymbol in pairs_short_ouvertes:
                pos = "SHORT"
            if perpSymbol in pairs_long_ouvertes:
                pos = "LONG"
            if pos == "LONG":
                prixTakeProfit = getTakeprofit(
                    "long",
                    getPrixAchat(perpSymbol),
                    dfList[perpSymbol].iloc[-2],
                    dfList[perpSymbol].iloc[-3],
                    dfList,
                    indicators["params"]
                )
            if pos == "SHORT":
                prixTakeProfit = getTakeprofit(
                    "short",
                    getPrixAchat(perpSymbol),
                    dfList[perpSymbol].iloc[-2],
                    dfList[perpSymbol].iloc[-3],
                    dfList,
                    indicators["params"]
                )
            quantityMax = getQuantite(perpSymbol)
            levier = getLevier(perpSymbol)
            placeOrder(
                "takeProfit",
                perpSymbol,
                quantityMax,
                prixTakeProfit,
                levier,
                position=pos,
            )

if useLimitOrderToOpen != "false":
    i = 0
    maxCheck = 30
    timeBetweenCheck = 10
    print("On attend que les ordres limites d'ouverture de positions se déclenchent...")
    closeOrders = len(ordresCloseShort) + len(ordresCloseLong)
    while (
        len(ordresLong) > 0
        or len(ordresShort) > 0
        or len(ordresCloseShort) > 0
        or len(ordresCloseLong) > 0
    ):
        openPositionsList = []
        for cointrade in ftx.get_open_position():
            openPositionsList.append(cointrade.get("symbol"))
        if len(ordresLong) > 0:
            for perpSymbol in ordresLong:
                if perpSymbol in openPositionsList:
                    price = getPrixAchat(perpSymbol)
                    prixTakeProfit = getTakeprofit(
                        "long",
                        price,
                        dfList[perpSymbol].iloc[-2],
                        dfList[perpSymbol].iloc[-3],
                        dfList,
                        indicators["params"]
                    )
                    quantityMax = getQuantite(perpSymbol)
                    ftx.cancel_all_open_order(symbol=perpSymbol)
                    placeOrder(
                        "takeProfit",
                        perpSymbol,
                        quantityMax,
                        prixTakeProfit,
                        leverage,
                        position="LONG",
                    )
                    placeOrder(
                        "securityStopLoss",
                        perpSymbol,
                        quantityMax,
                        getSecureStopLossPrice(perpSymbol, "long", price, leverage),
                        leverage,
                        position="LONG",
                    )
                    print(
                        f"L'ordre limite d'achat pour {perpSymbol} a été atteint (position LONG)."
                    )
                    with open(
                        path + str(config["FICHIER.HISTORIQUE"]["positionFile"]), "a"
                    ) as f:
                        f.write(
                            f"{date} | open LONG {quantityMax} {perpSymbol} at {price} \n"
                        )
                    if (
                        alwaysNotifTelegram == "true"
                        or notifTelegramOnChangeOnly == "true"
                    ):
                        telegram_send.send(
                            messages=[
                                f"{botname} : Confirmation d'achat pour {perpSymbol} (LONG) : l'ordre limite d'achat a bien été executé."
                            ]
                        )
                    del ordresLong[ordresLong.index(perpSymbol)]
        if len(ordresShort) > 0:
            for perpSymbol in ordresShort:
                if perpSymbol in openPositionsList:
                    price = getPrixAchat(perpSymbol)
                    prixTakeProfit = getTakeprofit(
                        "short",
                        price,
                        dfList[perpSymbol].iloc[-2],
                        dfList[perpSymbol].iloc[-3],
                        dfList,
                        indicators["params"]
                    )
                    quantityMax = getQuantite(perpSymbol)
                    ftx.cancel_all_open_order(symbol=perpSymbol)
                    placeOrder(
                        "takeProfit",
                        perpSymbol,
                        quantityMax,
                        prixTakeProfit,
                        leverage,
                        position="SHORT",
                    )
                    placeOrder(
                        "securityStopLoss",
                        perpSymbol,
                        quantityMax,
                        getSecureStopLossPrice(perpSymbol, "short", price, leverage),
                        leverage,
                        position="SHORT",
                    )
                    print(
                        f"L'ordre limite d'achat pour {perpSymbol} a été atteint (position SHORT)."
                    )
                    with open(
                        path + str(config["FICHIER.HISTORIQUE"]["positionFile"]), "a"
                    ) as f:
                        f.write(
                            f"{date} | open SHORT {quantityMax} {perpSymbol} at {price} \n"
                        )
                    if (
                        alwaysNotifTelegram == "true"
                        or notifTelegramOnChangeOnly == "true"
                    ):
                        telegram_send.send(
                            messages=[
                                f"{botname} : Confirmation d'achat pour {perpSymbol} (SHORT) : l'ordre limite d'achat a bien été executé."
                            ]
                        )
                    del ordresShort[ordresShort.index(perpSymbol)]
        for perpSymbol in ordresCloseLong:
            if perpSymbol in openPositionsList:
                # crypto toujours détenue
                pass
            else:
                print(
                    f"L'ordre limite de vente pour {perpSymbol} a été atteint (position LONG)."
                )
                ftx.cancel_all_open_order(symbol=perpSymbol)
                with open(
                    path + str(config["FICHIER.HISTORIQUE"]["positionFile"]), "a"
                ) as f:
                    f.write(
                        f"{date} | close LONG 0.0 {perpSymbol} at {getCurrentPrice(perpSymbol)} \n"
                    )
                if alwaysNotifTelegram == "true" or notifTelegramOnChangeOnly == "true":
                    telegram_send.send(
                        messages=[
                            f"{botname} : Confirmation de vente pour {perpSymbol} (LONG) : l'ordre limite de vente a bien été executé."
                        ]
                    )
                del ordresCloseLong[ordresCloseLong.index(perpSymbol)]
        for perpSymbol in ordresCloseShort:
            if perpSymbol in openPositionsList:
                # crypto toujours détenue
                pass
            else:
                print(
                    f"L'ordre limite de vente pour {perpSymbol} a été atteint (position SHORT)."
                )
                ftx.cancel_all_open_order(symbol=perpSymbol)
                with open(
                    path + str(config["FICHIER.HISTORIQUE"]["positionFile"]), "a"
                ) as f:
                    f.write(
                        f"{date} | close SHORT 0.0 {perpSymbol} at {getCurrentPrice(perpSymbol)} \n"
                    )
                if alwaysNotifTelegram == "true" or notifTelegramOnChangeOnly == "true":
                    telegram_send.send(
                        messages=[
                            f"{botname} : Confirmation de vente pour {perpSymbol} (SHORT) : l'ordre limite de vente a bien été executé."
                        ]
                    )
                del ordresCloseShort[ordresCloseShort.index(perpSymbol)]

        print(
            f"Check {i+1}/{maxCheck}, prochain check dans {timeBetweenCheck} secondes..."
        )
        time.sleep(timeBetweenCheck)
        i += 1
        if i >= maxCheck and (
            (len(ordresLong) > 0 or len(ordresShort) > 0)
            or (len(ordresCloseShort) > 0 or len(ordresCloseLong) > 0)
        ):
            if len(ordresLong) > 0 or len(ordresShort) > 0:
                openPositionsList = []
                for cointrade in ftx.get_open_position():
                    openPositionsList.append(cointrade.get("symbol"))
                print(
                    f"Fin du check et certains ordres limites n'ont pas été atteint : abandon des positions concernées : {ordresLong} {ordresShort}"
                )
                for perpSymbol in ordresLong:
                    if perpSymbol not in openPositionsList:
                        print(f"Annulation de l'ordre placé pour {perpSymbol}")
                        ftx.cancel_all_open_order(symbol=perpSymbol)
                for perpSymbol in ordresShort:
                    if perpSymbol not in openPositionsList:
                        print(f"Annulation de l'ordre placé pour {perpSymbol}")
                        ftx.cancel_all_open_order(symbol=perpSymbol)
            if len(ordresCloseShort) > 0 or len(ordresCloseLong) > 0:
                # On désactive le limite order
                useLimitOrderToClose = "false"
                for perpSymbol in ordresCloseShort:
                    if forceSell == "true":
                        quantityMaxsell = getQuantite(perpSymbol)
                        if quantityMaxsell is None:
                            quantityMaxsell = 10000000
                        ftx.cancel_all_open_order(symbol=perpSymbol)
                        price = ftx.get_bid_ask_price(symbol=perpSymbol)["ask"]
                        print(f"On force la fermeture de la position sur {perpSymbol}")
                        placeOrder(
                            "close",
                            perpSymbol,
                            quantityMaxsell,
                            price,
                            leverage,
                            position="SHORT",
                        )
                        with open(
                            path + str(config["FICHIER.HISTORIQUE"]["positionFile"]),
                            "a",
                        ) as f:
                            f.write(
                                f"{date} | close SHORT 0.0 {perpSymbol} at {getCurrentPrice(perpSymbol)} \n"
                            )
                        del ordresCloseShort[ordresCloseShort.index(perpSymbol)]
                    else:
                        print(
                            f"La position sur {perpSymbol} n'a pas été fermée, on laisse l'ordre limite de vente en espérant qu'il soit atteint d'ici la prochaine execution"
                        )
                for perpSymbol in ordresCloseLong:
                    if forceSell == "true":
                        quantityMaxsell = getQuantite(perpSymbol)
                        if quantityMaxsell is None:
                            quantityMaxsell = 10000000
                        ftx.cancel_all_open_order(symbol=perpSymbol)
                        price = ftx.get_bid_ask_price(symbol=perpSymbol)["ask"]
                        print(f"On force la fermeture de la position sur {perpSymbol}")
                        placeOrder(
                            "close",
                            perpSymbol,
                            quantityMaxsell,
                            price,
                            leverage,
                            position="LONG",
                        )
                        with open(
                            path + str(config["FICHIER.HISTORIQUE"]["positionFile"]),
                            "a",
                        ) as f:
                            f.write(
                                f"{date} | close LONG 0.0 {perpSymbol} at {getCurrentPrice(perpSymbol)} \n"
                            )
                        del ordresCloseLong[ordresCloseLong.index(perpSymbol)]
                    else:
                        print(
                            f"La position sur {perpSymbol} n'a pas été fermée, on laisse l'ordre limite de vente en espérant qu'il soit atteint d'ici la prochaine execution"
                        )
            break

print("Fin d'execution du bot.")
