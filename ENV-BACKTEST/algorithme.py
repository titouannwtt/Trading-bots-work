import json
import sys
import warnings
from datetime import datetime
sys.path.append("dependencies") # noqa

import matplotlib.dates as mpl_dates
import matplotlib.pyplot as plt
import pandas as pd
import requests
import time
from datetime import datetime 

from backtesting import Backtesting
from custom_indicators import CustomIndocators as ci
from mouton_backtest import Backtest
import configparser
import os

warnings.simplefilter("ignore")


def str2bool(v):
    return v.lower() in ("true", "t", "1", "y", "yes", "ye", "oui")


# ===================================

start_date="2022-08-01"
end_date="2022-09-30"
strategy_name = sys.argv[1]

forceDownload=False
downloadFrom2019=False
showLog=True
startingBalance=None

backtest = Backtest(
    strategy_name = strategy_name,

    start_date = start_date+"T00:00:00",
    end_date   = end_date+"T15:00:00",

    forceDownload=forceDownload,
    downloadFrom2019=downloadFrom2019,
    showLog=showLog,
    startingBalance=startingBalance,
)

params_algo={}
print("Récupération des paramètres présents dans le fichier paramètre...")
for param in backtest.get_params() :
    print("\n================")
    useThisParam=str2bool(input(f"Souhaitez-vous faire varier {param} dans votre algorithme ({backtest.get_params()[param]}) ? [y/n]\n")) 
    if useThisParam==False :
        params_algo[param]={
                            'use' : useThisParam,
                            'current' : float(backtest.get_params()[param])
                            }
    else :
        print(f"\nLa valeur par défaut de {param} est {backtest.get_params()[param]}, précisez ici de combien vous voulez la faire varier :")
        min=float(input(f" • Valeur minimale : "))
        max=float(input(f" • Valeur maximale : "))
        if max<min :
            tempMin=max
            max=min
            min=tempMin
            print("Votre valeur minimale était supérieure à votre valeur maximale, elles ont été inversées.")
        pas=float(input(f" • Pas à chaque itération : "))
        if pas> max-min :
            print(f"Votre pas est plus grand que l'écart entre votre minimum et votre maximum ({max-min}). Entrez une nouvelle valeur :")
            pas=float(input(f" • Pas à chaque itération : "))
            if pas> max-min :
                print(f"Votre pas est toujours plus grand que l'écart entre votre minimum et votre maximum ({max-min}). Annulation...")
                exit()
        params_algo[param]={
                            'use' : useThisParam,
                            'min' : min,
                            'max' : max,
                            'pas' : pas,
                            'current' : min
                            }
print("")
os.makedirs(
    backtest.get_strategy_path() + f"resultats_algorithme",
    exist_ok=True,
)
file = backtest.get_strategy_path() + f"resultats_algorithme/" + strategy_name.replace("/", "") + "_" + start_date + "_" + end_date + ".csv"
file2 = backtest.get_strategy_path() + f"resultats_algorithme/" + "_sorted_" + strategy_name.replace("/", "") + "_" + start_date + "_" + end_date + ".csv"

fichierEnregistrement=file
print("Enregistrement des données dans : ", fichierEnregistrement)
print("Si des données étaient déjà présente dans le fichier, elles vont être supprimées\n")
classement = pd.DataFrame([])
try :
    classement = pd.read_csv(fichierEnregistrement)
    classement.drop(classement.columns[classement.columns.str.contains('Unnamed',case = False)],axis = 1, inplace = True)
except :
    classement = classement.append(pd.DataFrame({
                'finalBalance' : [0],
                'totalTrades' : [0],
                'drawDown' : [0],
                'startingBalance': [1000],
                'configs': [0],
                'parametres': [0]
            }), ignore_index=True)
    print(f"Le fichier {fichierEnregistrement} n'existe pas, nous allons le créer.")

elapsed = 0
i=0

#================================================================================================================
#   FONCTION QUI LANCE LE BACKTEST AVEC LES PARAMETRES D'ENTREES ET ENREGISTRE LE RESULTAT DANS UN FICHIER CSV
#================================================================================================================
def launch_backtest(parametres):
    print(f"Lancement du backtest avec les paramètres : {parametres} ")
    global classement
    global i
    global elapsed
    global backtest
    global strategy_name
    global start_date
    global end_date
    global forceDownload
    global downloadFrom2019
    global showLog
    global startingBalance
    i=i+1
    pourcent=round(100*i/count,4)
    start = time.time()
    configs=[]
    for config in backtest.get_configs():
        configs.append(config)
    print(f"La dernière execution a durée : {elapsed} secondes")
    print(f"Avancement total d'execution : {i}/{count} ({pourcent}%) (Temps restant estimé {round((count-i)*elapsed/60/60, 1)} heures ou {round((count-i)*elapsed/60/60/24, 1)} jours)")
    if ((classement['parametres'] == str(parametres)) & (classement['configs'] == str(configs))).any() :
        print(f"Données {parametres} déjà présentes dans le classement")
    else :
        
        backtest = Backtest(
            strategy_name = strategy_name,

            start_date = start_date+"T00:00:00",
            end_date   = end_date+"T15:00:00",

            forceDownload=forceDownload,
            downloadFrom2019=downloadFrom2019,
            showLog=showLog,
            startingBalance=startingBalance,
        )
        backtest.set_params(parametres)
        finalBalance, totalTrades, drawDown = backtest.run(params=parametres, showLog=True)
        end = time.time()
        elapsed = end - start
        print("Terminé, résultats:")
        print(finalBalance)
        classement = classement.append(pd.DataFrame({
                        'finalBalance' : [finalBalance],
                        'totalTrades' : [totalTrades],
                        'drawDown' : [drawDown],
                        'startingBalance': [float(backtest.get_configs()['STRATEGIE']['totalInvestment'])],
                        'configs': [str(configs)],
                        'parametres': [str(parametres)]
                    }), ignore_index=True)
                    
        classement.finalBalance = classement.finalBalance.astype(float)
        classement.totalTrades = classement.totalTrades.astype(int)
        classement.drawDown = classement.drawDown.astype(float)
        classement.drop(classement.columns[classement.columns.str.contains('Unnamed',case = False)],axis = 1, inplace = True)
        
        classement.to_csv(fichierEnregistrement)
        classement2 = classement.sort_values(by=['finalBalance'], ascending=False)
        classement2 = classement2[classement2.finalBalance >= 50000.0]
        #classement2 = classement2.drop_duplicates(subset=['finalBalance'])
        classement2.to_csv(file2)
    return True

#params_algo
count=0
for j in range(2):
    for param_name in params_algo :
        if params_algo[param_name]['use']==True :
            min=float(params_algo[param_name]['min'])
            max=float(params_algo[param_name]['max'])
            pas=float(params_algo[param_name]['pas'])
            while(float(params_algo[param_name]['current'])<=max) :
                parametres={}
                parametres['params']={}
                print(param_name, params_algo[param_name]['current'], max)
                for param_name2 in params_algo :
                    parametres['params'][param_name2] = float(params_algo[param_name2]['current'])
                if j==1 : 
                    launch_backtest(parametres)
                else :
                    count = count+1
                params_algo[param_name]['current'] = float(params_algo[param_name]['current'])+pas
            params_algo[param_name]['current']=min
