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


#================================================================================================================

start_date="2022-06-01"
end_date="2022-10-04"
strategy_name = sys.argv[1]

forceDownload=False
downloadFrom2019=True
showLog=False
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

#================================================================================================================

os.makedirs(
    backtest.get_strategy_path() + f"resultats_algorithme",
    exist_ok=True,
)
file = backtest.get_strategy_path() + f"resultats_algorithme/" + strategy_name.replace("/", "")+".csv"
file2 = backtest.get_strategy_path() + f"resultats_algorithme/" + "_sorted_" + strategy_name.replace("/", "")+".csv"
file3 = backtest.get_strategy_path() + f"resultats_algorithme/" + "_forward_" + strategy_name.replace("/", "")+".csv"

#================================================================================================================
#   FONCTION QUI LANCE LE BACKTEST AVEC LES PARAMETRES D'ENTREES ET ENREGISTRE LE RESULTAT DANS UN FICHIER CSV
#================================================================================================================

elapsed = 0
i=0
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
    date = [start_date, end_date]
    pourcent=round(100*i/count,4)
    start = time.time()
    configs=[]
    for config in backtest.get_configs()['STRATEGIE']:
        configs.append(f"{config}={backtest.get_configs()['STRATEGIE'][config]}")
    print(f"La dernière execution a durée : {elapsed} secondes")
    print(f"Avancement total d'execution : {i}/{count} ({pourcent}%) (Temps restant estimé {round((count-i)*elapsed/60/60, 1)} heures ou {round((count-i)*elapsed/60/60/24, 1)} jours)")
    if ((classement['parametres'] == str(parametres)) & (classement['configs'] == str(configs)) & (classement['date'] == str(date))).any() :
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
        finalBalance, totalTrades, drawDown = backtest.run(params=parametres, showLog=False)
        end = time.time()
        elapsed = end - start
        print("Terminé, résultats:")
        print(finalBalance)
        classement = classement.append(pd.DataFrame({
                        'finalBalance' : [finalBalance],
                        'totalTrades' : [totalTrades],
                        'drawDown' : [drawDown],
                        'startingBalance': [float(backtest.get_configs()['STRATEGIE']['totalInvestment'])],
                        'date' : [date],
                        'configs': [str(configs)],
                        'parametres': [str(parametres)]
                    }), ignore_index=True)
                    
        classement.finalBalance = classement.finalBalance.astype(float)
        classement.totalTrades = classement.totalTrades.astype(int)
        classement.drawDown = classement.drawDown.astype(float)
        classement.drop(classement.columns[classement.columns.str.contains('Unnamed',case = False)],axis = 1, inplace = True)
        
        classement.to_csv(file)
        classement2 = classement.sort_values(by=['finalBalance'], ascending=False)
        classement2 = classement2[classement2.finalBalance >= 0.0]
        #classement2 = classement2.drop_duplicates(subset=['finalBalance'])
        classement2.to_csv(file2)
    return True

#================================================================================================================

algo=0
while algo==0 :
    algo_type=str(input(f"""
        Quel type d'algorithme souhaitez-vous utiliser ?
            - [1] Algorithme pas-à-pas
            - [2] Algorithme dichotomique (WIP)
            - [3] Algorithme optimisation (WIP)
            - [4] Forward-test (WIP)
            - [5] Aide
        """)) 
    try :
        if int(algo_type) == 1 :
            algo=1
            print("Vous avez choisi l'algorithme pas à pas")
        elif int(algo_type) == 2 :
            #algo=2
            print("L'algorithme dichotomique est en cours de développement")
        elif int(algo_type) == 3 :
            #algo=3
            print("L'algorithme optimisation n'est pas disponible pour le moment'")
        elif int(algo_type) == 4 :
            #algo=4
            print("Le forward-test n'est pas disponible pour le moment.")
        elif int(algo_type) == 5 :
            print(f"""Explication des différents algorithmes : 

- Algorithme pas-à-pas : demande une valeur minimale et maximale, ainsi qu'un pas (incrémentation à chaque itération) pour chaque paramètre à faire varier.
Un paramètre ayant min=0.0, max=2.0 et pas=0.5 sera testé avec les valeurs 0.0 ; 0.5 ; 1.0 ; 1.5 et 2.0.
Dans le cas où plusieurs paramètres seraient à faire varier, le nombre d'itération augmente fortement.
Les résultats sont sauvegardés dans {file}

- Algorithme dichotomique : demande une valeur minimale et maximale pour chaque paramètre à faire varier et va procéder par division successive en conservant les meilleurs résultats.
Un paramètre ayant min=0.0, max=2.0 sera testé avec les valeurs 0.0 ; 1.0 et 2.0. Si les résultats sont meilleurs pour 0.0 et 1.0, on testera alors les valeurs 0.0 ; 0.5 ; 1.0, etc.
Dans le cas où plusieurs paramètres seraient à faire varier, le nombre d'itération augmente fortement.
Les résultats sont sauvegardés dans {file}

- Algorithme optimisation : utilise les valeurs déjà présentent dans le fichier {file2} : récupère les meilleurs résultats et fait varier les paramètres à des valeurs proches.
Pour les X premières meilleures valeurs du fichier .csv, pour chaque paramètre : on récupère un maximum et un minimum et on détermine un pas tel que (max-min)/X*2
Les résultats sont sauvegardés dans {file}

- Forward-test : utilise les valeurs déjà présentent dans le fichier {file2} : récupère les meilleurs résultats et teste les mêmes paramètres à des dates différentes pour s'assurer que les paramètres ne sont pas optimisés pour une période précise.
Les résultats sont sauvegardés dans {file3}""")
    except :
        print("Impossible d'interprêter votre résultat, veuillez utiliser : 1, 2, 3, 4 ou 5 pour répondre.\n")
if algo==1 :
    params_algo={}
    print("Récupération des paramètres présents dans le fichier paramètre...")
    for param in backtest.get_params() :
        print("\n================")
        useThisParam=str2bool(input(f"Souhaitez-vous faire varier {param} dans votre algorithme ({backtest.get_params()[param]}) ? [y/n]\n")) 
        if useThisParam==False :
            params_algo[param]={
                                'use' : useThisParam,
                                'current' : float(backtest.get_params()[param]),
                                'min' : float(backtest.get_params()[param]),
                                'max' : float(backtest.get_params()[param]),
                                'pas' : 1.0
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
    print("Enregistrement des données dans : ", file)
    classement = pd.DataFrame([])
    try :
        classement = pd.read_csv(file)
        classement.drop(classement.columns[classement.columns.str.contains('Unnamed',case = False)],axis = 1, inplace = True)
    except :
        classement = classement.append(pd.DataFrame({
                    'finalBalance' : [0],
                    'totalTrades' : [0],
                    'drawDown' : [0],
                    'startingBalance': [1000],
                    'date' : [[0, 0]],
                    'configs': [0],
                    'parametres': [0]
                }), ignore_index=True)
        print(f"Le fichier {file} n'existe pas, nous allons le créer.")

    def giveMeNextParam(params_algo, param_name) :
        nextOne=False
        for param in params_algo :
            if nextOne==True :
                return param
            if param == param_name :
                nextOne=True

    def recursive_function(params_algo, param_name, lastParam) : 
        global count
        if params_algo[param_name]['use']==True :
            params_algo[param_name]['current'] = params_algo[param_name]['min']
        else:
            params_algo[param_name]['current'] = params_algo[param_name]['current'] 
            params_algo[param_name]['min'] = params_algo[param_name]['current']
            params_algo[param_name]['max'] = params_algo[param_name]['current']
            params_algo[param_name]['pas'] = 0
        while float(params_algo[param_name]['current']) <= float(params_algo[param_name]['max']):
            if param_name == lastParam :
                if j==1:
                    parametres={}
                    parametres['params']={}
                    for param1 in params_algo :
                        parametres['params'][param1] = float(params_algo[param1]['current'])
                    launch_backtest(parametres)
                else :
                    count=count+1
            else :
                recursive_function(params_algo, giveMeNextParam(params_algo, param_name), lastParam)
            
            if params_algo[param_name]['use']==True :
                params_algo[param_name]['current']=float(params_algo[param_name]['current'])+float(params_algo[param_name]['pas'])
            else :
                break

    #params_algo
    count=0
    initialParams=params_algo
    for j in range(2):
        firstParam=None
        for params_name in params_algo :
            if firstParam == None :
                firstParam=params_name
            lastParam = params_name 
        recursive_function(params_algo, firstParam, lastParam)
        params_algo=initialParams
elif algo==2 :
    #Algorithme dichotimique
    pass
elif algo==3 :
    #Algorithme optimisation
    pass
elif algo==4 : 
    #Forward test
    pass