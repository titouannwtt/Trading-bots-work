# main_dev_bots

Execute la commande:  python3 bot_live.py bot-template/

Créer un dossier copie de bot-template que tu nommeras "bot-strategie1" pour chaque stratégie.
Au sein du dossier "bot-strategie1" tu trouveras un fichier credentials.json où tu devras mettre tes clés API.

Pour lancer le bot, utilise la commande : python3 bot_live.py bot-strategie1/

Tu n'as pas à modifier le fichier bot_live.py, toute ta stratégie est modifiable directement grâce aux fichiers : config.cfg, parametres.cfg, strategy.py et pair_list.json

Le fichier bot_live.py est commun à toutes tes stratégies. Il récupère les spécificités de ta stratégie dans les fichiers présents dans le dossier bot-strategie1/.

Voici mon crontab (commande : crontab -e) :
```
0 * * * * python3 ENV-PROD/bot_live.py super-reversal-duo/ >> /home/moutonneux/ENV-PROD/super-reversal-duo/data/logs-executions.log 2>&1
0 * * * * python3 ENV-PROD/bot_live.py super-reversal/ >> /home/moutonneux/ENV-PROD/super-reversal/data/logs-executions.log 2>&1
*/15 * * * * python3 ENV-PROD/bot_live.py miracle/ >> /home/moutonneux/ENV-PROD/miracle/data/logs-executions.log 2>&1
*/15 * * * * python3 ENV-PROD/bot_live.py miracle-mono/ >> /home/moutonneux/ENV-PROD/miracle-mono/data/logs-executions.log 2>&1
5 */2 * * * python3 ENV-PROD/dashbot/dashbot.py
```
