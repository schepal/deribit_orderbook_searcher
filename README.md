# Deribit Orderbook Searcher

Over the past few weeks, several traders on Deribit have made enourmous trades through the use of passive limit orders. Although a significant portion of institutional crypto options trading occurs OTC or through the Paradigm RFQ venue, there's still some sophisticated players who tap into on-screen liquidity. 

Recall a limit order is an advertisement to the market showing where a trader is willing to buy or sell a particular security. In some cases, the trader may post misleading limit orders (ie: spoofing) to confuse the market, however, in many circumstances passive limit orders are prices at which investors would be happy to transact. As a result we can get further insight on how traders may be feeling about the market by analyzing the depth of the orderbook across each liquid option for a particular crypto. 

The motivation to create this tool was twofold:
1. In many cases traders may wish to hide behind limit orders. Their goal would be to get orders filled with less attention (even though their execution price would likely be better by going OTC or trading through Paradigm's RFQ venue). In this case the trader may value his privacy and doesn't want to draw uncessary attention. If there's a large passive limit order just sitting there then this tool will be able to pick it up.
2. On a collective we can analyze the aggregate orderbook imbalance of calls and puts. This can be used to assess overall investor demand across different options and is another datapoint to make trading decisions. 

Given this tool has to search through each individual option trading on Deribit, the underlying source code utilizes a helpful library called [`boosted_requests`](https://github.com/singhsidhukuldeep/request-boost) which parallelizes the GET requests into multiple steps.


