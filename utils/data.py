import logging

from multiprocessing.pool import ThreadPool
from typing import List

import investpy
import pandas as pd
import numpy as np
import yfinance as yf

logger = logging.getLogger('pt_logger.Stock')
yf.pdr_override()


def get_price_data_ticker(ticker: str, start_date: np.datetime64, end_date: np.datetime64) -> pd.DataFrame:
    """
    Gets price data for ticker for specified period

    Args:
        ticker (str): String ticker in format that is acceptable to Yahoo Finance
        start_date (np.datetime64): Start date to get price data
        end_date (np.datetime64): End date to get price data

    Returns:
        pd.DataFrame: Dataframe containing open, close, high, low, split, dividend data for ticker from start_date to end_date
    """

    logger.debug(f'-------  Ticker is {ticker}  -------')
    try:
        ticker_type = ticker.split('.')[1]
    except:
        ticker_type = None
    if ticker_type == 'LOAN':
        dl_data = pd.DataFrame(
            {'Date': pd.date_range(start_date, end_date)})
        dl_data['Close'] = -1
        dl_data['Stock Splits'] = 0
        dl_data['Dividends'] = 0
        dl_data.set_index('Date', inplace=True)
    elif ticker_type == 'FUND':
        try:
            isin = ticker.split('.')[0]
            fund_search = investpy.search_funds(by='isin', value=isin)
            name = fund_search.at[0, 'name']
            country = fund_search.at[0, 'country']
            dl_data = investpy.get_fund_historical_data(
                fund=name, country=country, from_date=start_date.strftime('%d/%m/%Y'), to_date=end_date.strftime('%d/%m/%Y'))
            dl_data.drop('Currency', axis=1, inplace=True)
            dl_data['Stock Splits'] = 0
            dl_data['Dividends'] = 0
        except RuntimeError:
            print(f'-------  No fund found for ISIN: {isin} -------')
            dl_data = pd.DataFrame()
    else:
        try:
            dl_data = yf.Ticker(ticker).history(
                start=start_date, end=end_date, auto_adjust=False, rounding=False, debug=True)
            logger.debug(
                f'{ticker}: Start: {start_date.date()} | End: {end_date.date()}')
        except KeyError:
            print(f'-------  Ticker {ticker} not found -------')
            dl_data = pd.DataFrame()
        except RuntimeError:
            print(f'-------  Yahoo! Finance is not working. Please try again -------')
    return dl_data


def get_price_data(tickers: List, start_dates: List, end_dates: List) -> pd.DataFrame:
    """
    Gets price data for a list of tickers for period specified

    Args:
        tickers (List): String list of tickers in format that is acceptable to Yahoo Finance
        startdate (np.datetime64): Start date to get price data
        end_date (np.datetime64): End date to get price data

    Returns:
        pd.DataFrame: Dataframe containing open, close, high, low, split, dividend data for each ticker from start_date to end_date
    """
    try:
        with ThreadPool(processes=len(tickers)) as pool:
            all_data = pool.starmap(get_price_data_ticker, zip(
                tickers, start_dates, end_dates))
            logger.debug('Obtained data, concatenating')
            concat_data = pd.concat(
                all_data, keys=tickers, names=['Ticker', 'Date'])
    except ValueError:
        raise ValueError('Please provide at least one ticker')
    return concat_data


def get_name(ticker: str) -> str:
    """
    Gets name of ticker

    Args:
        ticker (str): String ticker in format that is acceptable to Yahoo Finance

    Returns:
        str: Full name of stock based on ticker
    """

    logger.debug(f'Getting name for {ticker}')
    try:
        stock = yf.Ticker(ticker)
        try:
            name = stock.info['longName']
        except (IndexError, KeyError) as e:
            print(f'-------  Ticker {ticker} not found -------')
            name = "NA"
    except (ValueError, AttributeError):
        print(f'-------  Ticker {ticker} not found -------')
        name = "NA"
    return name


if __name__ == '__main__':
    # data.append(investpy.get_fund_information(
    #     fund='Vanguard International Shares Index Fund', country='australia'))
    isin = 'AU60VAN00030'
    data = investpy.search_funds(by='isin', value=isin)
    name = data.at[0, 'name']
    country = data.at[0, 'country']
    df = investpy.get_fund_historical_data(
        fund=name, country=country, from_date='1/1/2018', to_date='31/12/2018')
