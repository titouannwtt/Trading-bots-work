#Execute this file with : 
# - python3 bot_backtest.py miracle/
# - python3 bot_backtest.py super-reversal/
import json
import sys
import warnings
from datetime import datetime
sys.path.append("dependencies") # noqa

import matplotlib.dates as mpl_dates
import matplotlib.pyplot as plt
import pandas as pd
import requests

from backtesting import Backtesting
from custom_indicators import CustomIndocators as ci
from mouton_backtest import Backtest

warnings.simplefilter("ignore")

# ===================================

downloadFrom2019 = True
forceDownload = False

# ===================================

backtest = Backtest(
    strategy_name=sys.argv[1],

    start_date = "2022-05-01T00:00:00",
    end_date   = "2022-09-26T00:00:00",

    forceDownload=forceDownload,
    downloadFrom2019=downloadFrom2019,
    showLog=True,
    startingBalance=100.0,

)
print(backtest.run())