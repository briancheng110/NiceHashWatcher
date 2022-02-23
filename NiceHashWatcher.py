from memory_profiler import profile
from sys import exit
import pdb
import json
import requests
import sys
import statistics
import time
from datetime import datetime
from scipy.stats import *

# we need 5 things to make a full calculation:
# Hashpower market price, BTC exchange rate, network hashrate, block time, and reward per block

CoinList = ['DASH', 'HNS','ERG', 'XMR', 'BTC', 'AE', 'ETH', 'BEAM', 'ZEC', 'BTG', 'CFX', 'RVN', 'BCD', 'BCH', 'BSV']
marketList = ['USA_E', 'EU', 'USA', 'EU_N']
attributeList = [
    'ProfitBTC',
    'NativeMined',
    'ExchangeRate',
    'MyHashrate',
    'NetworkHashrate',
    'Difficulty'
]
market_stat_attribs = [
    'MarketPrice',
    'MeanMarketPrice',
    'SkewMarketPrice',
    'KurtosisMarketPrice',
    'SDMarketPrice',
    'LowerQuartileMarketPrice',
    'UpperQuartileMarketPrice',
    'MinMarketPrice'
]

CoinUrlFile = 'File'
CoinFeeFile = 'Fees'
outputFile = 'Output.csv'
loopTime = 15 #looping time in seconds
usdInvestment = 250

#Declare dictonary structure for each coin
CoinData = {}
Orders = {}
priceStats = {}
market_stats = {}

# safely retry HTML requests and parse as json
def safeHTMLGet(Url):
    while(True):
        try:
            page = requests.get(Url)
        except:
            print("Failed to fetch " + Url + ', retrying...')
        else:
            # sometimes NH sends us back garbage data, need secondary check
            if page.status_code == 200:
                break
        time.sleep(5) # prevent spamming server with requests
        
    pageVar = json.loads(page.text)
    return pageVar


def deductFees(targetLocation, Coin, Amount):
    for FeeId in list(CoinData[Coin]['Fees'].keys()):
        feeType = CoinData[Coin]['Fees'][FeeId]['feeType']
        feeValue = CoinData[Coin]['Fees'][FeeId]['feeValue']
        feeLocation = CoinData[Coin]['Fees'][FeeId]['feeLocation']
        if feeLocation == targetLocation:
            if feeType == 'Pct':
                Amount *= feeValue
            if feeType == 'Fixed':
                Amount -= feeValue
                
    return Amount


if __name__ == '__main__':
    # main ---------------------------------------------------------------------------------------------------------------------------------------
    # get BTC to USD exchange rate
    WTMPage = safeHTMLGet('https://whattomine.com/coins/1.json')
    btcExchange = float(WTMPage['exchange_rate'])
    #btcInvestment = usdInvestment / btcExchange
    btcInvestment = 0.006

    for Coin in CoinList:
        CoinData.update({Coin: {'MeanMarketPrice': 0.0, 'SkewMarketPrice': 0, 'KurotisisMarketPrice': 0, 'SDMarketPrice': 0, 'WTMUrl': "", 'LowerQuartileMarketPrice':0, 'UpperQuartileMarketPrice':0, 'WTMUrl_Base': "", 'NHUrl': "", 'WTMRateScale' : 0, 'difficulty': 0.0, 'volume': 0.0, 'marketPrice' : 100.0, 'marketScale' : 0, 'exchangeRate' : 0.0, 'calcHashRate': 0.0, 'networkHR' : 0, 'blockTime' : 0, 'nativeMined': 0.0, 'blockReward' : 0, 'profitBTC': 0.0, 'profitUSD' : 0.0, 'Fees' : {}} })
        
    # read file for urls for each coin
    with open(CoinUrlFile) as File:
        LineTotal = sum(1 for line in File)
        File.seek(0)
        
        for i in range(LineTotal):
            Line = File.readline()
            
            # If line is a comment, skip entirely
            if Line[0] == '#':
                continue

            ParsedLine = Line.split(',')
        
            for Coin in CoinList:
                if ParsedLine[0] == Coin:
                    CoinData[Coin]['WTMUrl_Base'] = 'https://whattomine.com/coins/' + ParsedLine[1] + '.json?fee=0.0&cost=0.0&p=0.0'
                    CoinData[Coin]['NHUrl'] = 'https://api2.nicehash.com/main/api/v2/hashpower/orderBook?algorithm=' + ParsedLine[2].strip().upper()
                    CoinData[Coin]['WTMRateScale'] = 10 ** int(ParsedLine[3])

    # Read in fees for each coin
    with open(CoinFeeFile) as File:
        LineTotal = sum(1 for line in File)
        File.seek(0)
        feeId = 0
        
        for i in range(LineTotal):
            Line = File.readline()
            
            if Line == '':
                break
            
            # If line is a comment or blank line, skip entirely
            if Line[0] == '#' or Line[0] == '\n':
                continue
            elif Line[0] == ':': # denotes new section
                Section = Line[1:].strip()
                while True:
                    Line = File.readline().strip()
                    if Line[0] == '#' or Line[0] == '\n':
                        continue
                    if Line == '-':
                        break
                    ParsedLine = Line.split(',') # read the line, strip the newline, and split into list
                    if Section == 'Global':
                        for Coin in CoinList:
                            CoinData[Coin]['Fees'].update({feeId: {'feeName': ParsedLine[0], 'feeType': ParsedLine[1], 'feeValue': float(ParsedLine[2]), 'feeLocation': ParsedLine[3]}})
                            if CoinData[Coin]['Fees'][feeId]['feeType'] == 'Pct':
                                CoinData[Coin]['Fees'][feeId]['feeValue'] = (100 - CoinData[Coin]['Fees'][feeId]['feeValue']) / 100
                    else:
                        
                        CoinData[Section]['Fees'].update({feeId: {'feeName': ParsedLine[0], 'feeType': ParsedLine[1], 'feeValue': float(ParsedLine[2]), 'feeLocation': ParsedLine[3]}})
                        if CoinData[Section]['Fees'][feeId]['feeType'] == 'Pct':
                            CoinData[Section]['Fees'][feeId]['feeValue'] = (100 - CoinData[Section]['Fees'][feeId]['feeValue']) / 100          
                    feeId += 1
            
    # Deduct investment fees
    # inputMoney is the initial investment minus fees. Investment is preserved to calculate overall profit/loss
    # Do this outside the loop to prevent repeatedly deducting fees
    inputMoney = deductFees('Investment', Coin, btcInvestment)
    print(inputMoney)        


        
    # We are ready to begin pulling and calculating
    # Enter infinite loop to repeatedly pull data from NH and WTM
    # Also perform 1 time file setup

    while(True):
        try:
            with open(outputFile, mode='a') as csvOutput:
                csvOutput.write('Time,')
                for x in CoinList:
                        for Attribute in attributeList:
                            csvOutput.write(x + '_' + Attribute + ',')
                        for Market in marketList:
                            for Item in market_stat_attribs:
                                csvOutput.write(x + '_' + Item + '_' + Market + ',')

                csvOutput.write('\n')
        except PermissionError:
            print("File is open in another program, waiting 10s to retry")
        else:
            break


    #file is closed after each operation and re-opened prn -- avoids file locking for other programs

    while(True):
        Now = datetime.now()
        timeNow = Now.strftime("%x %H:%M:%S")
        print('----------- ' + str(timeNow) + ' -----------')
        with open(outputFile, mode='a') as csvOutput:
            csvOutput.write(str(timeNow) + ',')
        for Coin in CoinList:
            NHPage = safeHTMLGet(CoinData[Coin]['NHUrl'])
            scaleFactor = NHPage['stats']['EU']['marketFactor']
            # This section will copy all orders to a new dictionary
           
            priceStats = {}
            for Market in marketList:
                Orders = {}
                Orders.update({Market: {}})
                priceStats.update({Market: []})
                NHPage = safeHTMLGet(CoinData[Coin]['NHUrl'])

                try:
                    CoinData[Coin]['marketScale'] = float(NHPage['stats'][Market]['marketFactor'])
                    totalMarketSpeed = float(NHPage['stats'][Market]['totalSpeed'])
                except KeyError:
                    continue

                order_count = len(NHPage['stats'][Market]['orders'])
                for i in range(order_count):
                    Orders[Market].update({i: {
                       'price': float(NHPage['stats'][Market]['orders'][i]['price']),
                       'speed': float(NHPage['stats'][Market]['orders'][i]['payingSpeed']),
                       'activeRigs': int(NHPage['stats'][Market]['orders'][i]['rigsCount'])

                    }})
                    
                    if Orders[Market][i]['activeRigs'] > 0:
                        for x in range(Orders[Market][i]['activeRigs']):
                            priceStats[Market].append(Orders[Market][i]['price'])

            market_stats = {}
            for Market in marketList:
                market_stats.update({Market: {}})
                try:
                    if len(priceStats) == 1:
                        market_stats[Market].update({'marketPrice': priceStats[0]})
                        market_stats[Market].update({'MeanMarketPrice': priceStats[0]})
                        market_stats[Market].update({'SkewMarketPrice': priceStats[0]})
                        market_stats[Market].update({'KurtosisMarketPrice': 0})
                        market_stats[Market].update({'SDMarketPrice': priceStats[0]})
                        market_stats[Market].update({'LowerQuartileMarketPrice': priceStats[0]})
                        market_stats[Market].update({'UpperQuartileMarketPrice': priceStats[0]})
                        market_stats[Market].update({'MinMarketPrice': priceStats[0]})
                    else:
                        data_array = priceStats[Market]
                        quartiles = statistics.quantiles(data_array)
                        market_stats[Market].update({'marketPrice': quartiles[1]})
                        market_stats[Market].update({'MeanMarketPrice': statistics.mean(data_array)})
                        market_stats[Market].update({'SkewMarketPrice': skew(data_array)})
                        market_stats[Market].update({'KurtosisMarketPrice': kurtosis(data_array)})
                        market_stats[Market].update({'SDMarketPrice': statistics.stdev(data_array)})
                        market_stats[Market].update({'LowerQuartileMarketPrice': quartiles[0]})
                        market_stats[Market].update({'UpperQuartileMarketPrice': quartiles[2]})
                        market_stats[Market].update({'MinMarketPrice': min(data_array)})
                except statistics.StatisticsError:
                    continue
            
        # Fill in necessary variables from whattomine.com
        # Also outsource profit calc to WTM
            calcHashrate = (inputMoney / CoinData[Coin]['marketPrice']) * CoinData[Coin]['marketScale']
            CoinData[Coin]['calcHashRate'] = calcHashrate
            CoinData[Coin]['WTMUrl'] = CoinData[Coin]['WTMUrl_Base'] + '&hr=' + str(round(calcHashrate / CoinData[Coin]['WTMRateScale'], 2))
            WTMPage = safeHTMLGet(CoinData[Coin]['WTMUrl'])

            CoinData[Coin]['exchangeRate'] = float(WTMPage['exchange_rate'])

            # Special clause for BTC -- set to 1
            if Coin == 'BTC':
                CoinData[Coin]['exchangeRate'] = 1

            CoinData[Coin]['networkHR'] = float(WTMPage['nethash'])
            CoinData[Coin]['blockTime'] = float(WTMPage['block_time'])
            CoinData[Coin]['blockReward'] = float(WTMPage['block_reward'])
            CoinData[Coin]['difficulty'] = float(WTMPage['difficulty'])
            CoinData[Coin]['volume'] = float(WTMPage['exchange_rate_vol'])
            
            #deduct fees from native currency
            nativeMined = float(WTMPage['estimated_rewards'].replace(',',''))
            nativeMined = deductFees('Native', Coin, nativeMined)
            CoinData[Coin]['nativeMined'] = nativeMined

            #deduct fees from final amount    
            btcMined = nativeMined * CoinData[Coin]['exchangeRate']
            btcMined = deductFees('Final', Coin, btcMined)
            
            CoinData[Coin]['profitBTC'] = btcMined - btcInvestment
            CoinData[Coin]['profitUSD'] = (btcMined - btcInvestment) * btcExchange
            print(Coin, 'Profit: ' + str(round(CoinData[Coin]['profitBTC'], 8)), CoinData[Coin]['marketPrice'], round(CoinData[Coin]['profitBTC'] / btcInvestment * 100, 2), calcHashrate)

        # write current iteration data, then close



            with open(outputFile, mode='a') as csvOutput:
                csvOutput.write(str(round(CoinData[Coin]['profitBTC'],8)) + ',')
                csvOutput.write(str(round(CoinData[Coin]['nativeMined'],8)) + ',')
                csvOutput.write(str(round(CoinData[Coin]['exchangeRate'],8)) + ',')
                csvOutput.write(str(CoinData[Coin]['calcHashRate']) + ',')
                csvOutput.write(str(CoinData[Coin]['networkHR']) + ',')
                csvOutput.write(str(CoinData[Coin]['difficulty']) + ',')

                for Market in marketList:
                    if len(market_stats[Market]) == 0:
                        csvOutput.write('0,0,0,0,0,0,0,')
                    else:
                        csvOutput.write(str(market_stats[Market]['marketPrice']) + ',')
                        csvOutput.write(str(market_stats[Market]['MeanMarketPrice']) + ',')
                        csvOutput.write(str(market_stats[Market]['SkewMarketPrice']) + ',')
                        csvOutput.write(str(market_stats[Market]['KurtosisMarketPrice']) + ',')
                        csvOutput.write(str(market_stats[Market]['SDMarketPrice']) + ',')
                        csvOutput.write(str(market_stats[Market]['LowerQuartileMarketPrice']) + ',')
                        csvOutput.write(str(market_stats[Market]['UpperQuartileMarketPrice']) + ',')
                        csvOutput.write(str(market_stats[Market]['MinMarketPrice']) + ',')
                    
    ##            pdb.set_trace()
            # explicit buffer flushing unnecessary -- flushed on close

        with open(outputFile, mode='a') as csvOutput:
            csvOutput.write('\n')
    ##    time.sleep(loopTime)
        sys.exit()
        
