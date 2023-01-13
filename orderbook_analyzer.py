import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import requests
from request_boost import boosted_requests


class AnalyzeBook:
    """
    The purpose of this class is to analyze the orderbook depth of every listed option trading on Deribit.
    """

    def __init__(self, asset):
        """
        asset: str
            Initialize asset type as either "BTC" or "ETH"
        """
        self.asset = asset.upper()
        self.url_base = "https://www.deribit.com/api/v2/public/"

    def get_instruments(self):
        """
        Gets list of all tradeable options with associated URL links
        """
        x = requests.get(
            self.url_base
            + "get_instruments?currency="
            + str(self.asset)
            + "&expired=false&kind=option"
        )
        x = pd.DataFrame(x.json()["result"])[["instrument_name"]]
        inst_list = list(x.instrument_name)
        x["instrument_url"] = [
            self.url_base + "get_order_book?instrument_name=" + str(inst_list[i])
            for i in range(len(inst_list))
        ]
        return x

    def get_all_data(self):
        """
        Parallelize GET requests from Deribit API using `request-boost` library
        """
        df = self.get_instruments()
        urls = list(df.instrument_url)
        results = boosted_requests(
            urls=urls,
            no_workers=16,
            max_tries=5,
            timeout=5,
            headers=None,
            verbose=True,
            parse_json=True,
        )
        return results

    def extract_data(self, manual=False, instrument_name=np.nan):
        """
        Used to parse data from the `get_all_data` method

        manual: bool
            If set to False, all options downloaded will be analyzed
            If set to True, only the specified option will be analyzed
        instrument_name: str
            If manual set to True, then user needs to input an option name
        """
        # If set to False, then all data will be retrieved
        if manual == False:
            r = self.get_all_data()
        # Otherwise only a single option will be retrieved
        else:
            url = self.get_instruments()
            d = list(url[url.instrument_name == instrument_name].instrument_url)[0]
            r = [requests.get(d).json()]

        store = []
        for i in range(len(r)):
            s = r[i]["result"]
            bids, asks = pd.DataFrame(s["bids"]), pd.DataFrame(s["asks"])
            col_name = ["coin_price", "quantity", "usd_price"]
            # If the bid or ask dataframes are empty then assign empty list
            if len(bids) == 0:
                bids = []
            elif len(asks) == 0:
                asks = []
            else:
                # Convert the price of option into USD and calculate rolling totals
                bids["usd_price"] = bids.iloc[:, 0] * s["underlying_price"]
                bids.columns = col_name
                bids["total_usd"] = bids.usd_price * bids.quantity
                bids["cumulative_usd"] = bids.total_usd.cumsum()

                asks["usd_price"] = asks.iloc[:, 0] * s["underlying_price"]
                asks.columns = col_name
                asks["total_usd"] = asks.usd_price * asks.quantity
                asks["cumulative_usd"] = asks.total_usd.cumsum()

            store.append([s["instrument_name"], bids, asks])

            # If only looking at single option then also include the mark price
            if manual == True:
                store.append(s["mark_price"])
        return store

    def clean_data(self, top_book=False, levels=5):
        """
        Used to clean the parsed data from `extract_data` method.

        top_book: bool
            If set to False, then the entire orderbook depth will be analyzed
            If set to True, then only the specified orderbook depth will be analyzed
        levels: int
            If `top_book` set to True, then user must specify the number of levels to use
            for analyzing orderbook depth. For example suppose we select a level of 4.
            If an orderbook had the following bids as follows: 0.30, 0.25, 0.20, 0.10, 0.05,
            then only the first four bids would be included in our analysis.
        """
        store = self.extract_data()
        df = []

        for i in range(len(store)):
            s = store[i]
            """
            If either the bid or ask lists are empty then we will skip this option.
            The goal here is to analyze listings with liquidity on both sides of the book,
            therefore, we must remove these illiquid options from our analysis.
            """
            if (len(s[1]) == 0) or (len(s[2]) == 0):
                pass
            else:
                # If set to True, then the model will only look at options up to the user specified depth in levels
                if top_book == True:
                    df.append(
                        [
                            s[0],
                            s[1].head(levels).total_usd.sum() / 1000,
                            s[2].head(levels).total_usd.sum() / 1000,
                        ]
                    )
                # Otherwise the model will simply return the entire orderbook depth
                else:
                    df.append(
                        [
                            s[0],
                            s[1].total_usd.sum() / 1_000,
                            s[2].total_usd.sum() / 1_000,
                        ]
                    )
        r = pd.DataFrame(df)
        r.columns = ["product_name", "bids_thousands", "asks_thousands"]
        return r

    def plot_book(self, instrument_name, savefig=False):
        """
        Plots the orderbook depth of a particular option listing

        instrument_name: str
            Specify the instrument name
        savefig: bool
            Select True to save the plot
        """

        x = self.extract_data(manual=True, instrument_name=instrument_name)

        title, bids, asks = x[0]

        # Ensure only options with liquidity are selected
        if (len(bids) == 0) or (len(asks) == 0):
            print("Bid or Ask Orderbook Empty - choose another option")
            return

        # Extract the current mark price of the option
        mark = x[1]
        plt.figure(figsize=(10, 5))
        plt.plot(
            bids.coin_price,
            bids.cumulative_usd / 1000,
            label="USD Bid Depth",
            marker="x",
        )
        plt.plot(
            asks.coin_price,
            asks.cumulative_usd / 1000,
            label="USD Ask Depth",
            marker="x",
        )
        plt.axvline(mark, label="Mark Price: " + str(round(mark, 5)),linestyle="--", c="r", alpha=0.50)
        plt.title(title + " Order-Book")
        plt.ylabel("USD (Thousands)")
        plt.xlabel(self.asset.split("-")[0])
        plt.legend()
        if savefig==True:
            plt.savefig(str(title) + ".jpeg", dpi=500)
        plt.show()

    def get_single_book(self, instrument_name):
        """
        Extracts the full bid and ask orderbooks for a particular option

        instrument_name: str
            Specify the instrument name
        """
        x = self.extract_data(manual=True, instrument_name=instrument_name)[0]
        return x[1], x[2]
