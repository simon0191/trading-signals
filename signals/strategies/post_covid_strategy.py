from ..models import Signal, OperationType
import requests
import numpy as np
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from urllib.parse import urlencode
from django.utils import timezone
from django.template import Context, Template
import base64
from io import BytesIO
from matplotlib.figure import Figure
import logging

logger = logging.getLogger(__name__)
# TOP100_MARKET_CAP = ["GOOG", "GOOGL", "CIB"]
TOP100_MARKET_CAP = ["MSFT", "AAPL", "AMZN", "GOOG", "GOOGL", "BABA", "FB", "BRK.B", "BRK.A", "V", "JNJ", "WMT", "JPM", "PG", "CHT", "MA", "TSM", "UNH", "INTC", "VZ", "TBB", "TBC", "T", "BAC", "HD", "KO", "MRK", "PFE", "NVS", "DIS", "PEP", "XOM", "CSCO", "CMCSA", "TM", "ORCL", "NFLX", "NVDA", "CHL", "CVX", "ADBE", "ABT", "SAP", "LLY", "CRM", "MCD", "WFC", "MDT", "NKE", "BMY", "COST", "AMGN", "TMO", "PYPL", "NEE", "ABBV", "PM", "AZN", "ASML", "AMT", "SNY", "ACN", "HSBC", "HSBC/PA", "NVO", "IBM", "TMUS", "TSLA", "LMT", "AVGO", "DHR", "HON", "LIN", "UNP", "TXN", "C", "CHTR", "GSK", "TOT", "GILD", "RY", "SBUX", "BTI", "BA", "MMM", "UPS", "BP", "QCOM", "BUD", "CVS", "TD", "DEO", "RDS.A", "FIS", "AXP", "MO", "MDLZ", "SNE", "HDB", "BLK", "ADR", "CIB"]
COVID_CRASH = '2020-02-19'

class PostCovidStrategy:

  def calc_indicators(self, symbol, stock_data):
    last_min = stock_data['min'].last_valid_index()
    local_mins = stock_data['min'].dropna()
    bottom = min(stock_data['minmin'][local_mins.index[-1]], stock_data['minmin'][local_mins.index[-2]])

    #bottom = min(stock_data[COVID_CRASH:]['close'])
    start_trimester_pre_covid = (date.fromisoformat(COVID_CRASH) - relativedelta(months=3)).strftime("%Y-%m-%d")
    top = max(stock_data[start_trimester_pre_covid:]['close'])

    curr = stock_data['close'][-1]
    #                  (150 - 100)/100 =
    potential_gain = ((top - curr)/curr)
    potential_loss = ((curr - bottom)/curr)

    return {
      'bottom': bottom,
      'top': top,
      'curr': curr,
      'potential_gain': potential_gain,
      'potential_loss': potential_loss
    }

  def rate_stock(self, symbol, stock_data):
    indicators = self.calc_indicators(symbol, stock_data)

    if indicators['potential_gain']/indicators['potential_loss'] >= 3:
      return "GOOD"
    if indicators['potential_gain']/indicators['potential_loss'] >= 2:
      return "MAYBE"

    return "BAD"

  def find_post_covid_prospects(self, stock_list):
    initial_date = (date.fromisoformat(COVID_CRASH) - relativedelta(years=1)).strftime("%Y-%m-%d")

    prospects = []
    for i, symbol in enumerate(stock_list):
      prices_df = self.get_prices(symbol, {'from': initial_date})
      if prices_df.empty:
        continue

      enriched_data = self.enrich_stock_data(prices_df)
      rate =self. rate_stock(symbol, enriched_data)
      indicators = self.calc_indicators(symbol, enriched_data)
      if rate in ["MAYBE", "GOOD"]:
        prospects.append((symbol, rate, indicators, enriched_data))
        print("✓", end="")
      else:
        print("𝙭", end="")
    print("")
    print(f"{len(prospects)}/{len(stock_list)} prospects found")
    return prospects

  def enrich_stock_data(self, df):

    df['5mean'] = df['close'].rolling(5).mean()
    df['20mean'] = df['close'].rolling(20).mean()
    df['50mean'] = df['close'].rolling(50).mean()
    df['90mean'] = df['close'].rolling(90).mean()
    df['min'] = df['5mean'][(df['5mean'].shift(1) > df['5mean']) & (df['5mean'].shift(-1) > df['5mean'])]
    df['minmin'] = df['close'].rolling(5).min()
    df['max'] = df['5mean'][(df['5mean'].shift(1) < df['5mean']) & (df['5mean'].shift(-1) < df['5mean'])]
    df['maxmax'] = df['close'].rolling(5).max()

    return df

  def get_prices(self, symbol, opts = {}, cache = {}):
    if symbol in cache:
      return cache[symbol]

    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?serietype=line"
    if len(opts.keys()):
      url += f"&{urlencode(opts)}"

    hist_prices = requests.get(url).json()
    if len(hist_prices.keys()) == 0:
      return pd.DataFrame.from_dict({})

    hist_prices = hist_prices['historical']
    prices_df = pd.DataFrame.from_dict(hist_prices)
    prices_df = prices_df.set_index('date')
    cache[symbol] = prices_df
    return cache[symbol]

  def labeled_hline(self, plt, y, xmin, xmax, label):
    plt.hlines(y=y, xmin=xmin, xmax=xmax)
    plt.text(xmin, y, label, ha='right', va='center')

  def plot_prospect(self, symbol, data, indicators):
    # Generate the figure **without using pyplot**.
    fig = Figure(figsize=(20, 10))
    ax = fig.subplots()

    ax.set_title(symbol)

    data['close'].plot(ax=ax)
    data['5mean'].plot(ax=ax)
    data['20mean'].plot(ax=ax)
    data['50mean'].plot(ax=ax)
    data['90mean'].plot(ax=ax)

    ax.scatter(data.index, data['min'], c='r')
    ax.scatter(data.index, data['max'], c='g')
    #ax.xticks(rotation=70)
    ax.legend(data.columns)
    #
    ax.vlines(COVID_CRASH, min(data['close']), max(data['close']))
    for ind in ['bottom', 'top']:
      self.labeled_hline(ax, indicators[ind], data.index[0], data.index[-1], ind)

    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return data

  def gen_analysis_html(self, prospect):
    ticker, _, indicators, data = prospect
    img_b64 = self.plot_prospect(ticker, data, indicators)
    template = Template("""
    <img src='data:image/png;base64,{{ img_b64 }}'/>
    """ )
    context = Context({"ticker": ticker, "img_b64": img_b64})
    return template.render(context)

  def run(self, save=False):
    logger.info('Running POST_COVID strategy...')
    prospects = self.find_post_covid_prospects(TOP100_MARKET_CAP)

    signals = []
    for (ticker, rate, indicators, data) in prospects:
      signal = Signal(
        ticker=ticker,
        operation_type=OperationType.BUY,
        potential_gain=indicators['potential_gain'],
        potential_loss=indicators['potential_loss'],
        analysis=self.gen_analysis_html((ticker, rate, indicators, data)),
        created_at=timezone.now())
      if save:
        signal.save()
      signals.append(signal)

    return signals
