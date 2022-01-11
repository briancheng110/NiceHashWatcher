import json
import requests
import sys
import statistics
import time
from datetime import datetime

# we need 5 things to make a full calculation:
# Hashpower market price, BTC exchange rate, network hashrate, block time, and reward per block

# get BTC to USD exchange rate
WTMPage = json.loads(requests.get('https://whattomine.com/coins/1.json').text)
btcExchange = float(WTMPage['exchange_rate'])

CoinList = ['DASH', 'HNS','ERG', 'XMR', 'BTC', 'AE', 'ETH', 'BEAM', 'ZEC', 'BTG', 'CFX', 'RVN', 'BCD', 'BCH', 'BSV']
marketList = ['USA_E', 'EU', 'USA', 'EU_N']
attributeList = ['ProfitBTC','NativeMined','ExchangeRate','MyHashrate','NetworkHashrate','Difficulty','MarketPrice']
CoinUrlFile = 'File'
CoinFeeFile = 'Fees'
outputFile = 'Output.csv'
loopTime = 90 #looping time in seconds
usdInvestment = 250
btcInvestment = usdInvestment / btcExchange
#btcInvestment = 0.004

#Declare dictonary structure for each coin
CoinData = {}
Orders = {}
priceStats = []

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

for Coin in CoinList:
    CoinData.update({Coin: {'WTMUrl': "", 'NHUrl': "", 'WTMRateScale' : 0, 'difficulty': 0.0, 'volume': 0.0, 'marketPrice' : 100.0, 'marketScale' : 0, 'exchangeRate' : 0.0, 'calcHashRate': 0.0, 'networkHR' : 0, 'blockTime' : 0, 'nativeMined': 0.0, 'blockReward' : 0, 'profitBTC': 0.0, 'profitUSD' : 0.0, 'Fees' : {}} })
    
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
                CoinData[Coin]['WTMUrl'] = 'https://whattomine.com/coins/' + ParsedLine[1] + '.json?fee=0.0&cost=0.0&p=0.0'
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
with open(outputFile, mode='w') as csvOutput:
    csvOutput.write('Time,')
    for Coin in CoinList:
            for Attribute in attributeList:
                csvOutput.write(Coin + '_' + Attribute + ',')
    csvOutput.write('\n')

#file is closed after each operation and re-opened prn -- avoids file locking for other programs

while 0<1:
    Now = datetime.now()
    timeNow = Now.strftime("%x %H:%M:%S")
    print('----------- ' + str(timeNow) + ' -----------')
    for Coin in CoinList:
        NHPage = json.loads(requests.get(CoinData[Coin]['NHUrl']).text)
        scaleFactor = NHPage['stats']['EU']['marketFactor']
        # This section will copy all orders to a new dictionary
        # Looks for 3 orders where rigsCount = 0. This determines minimum price
        #for Coin in CoinList:
        
        priceStats = []
        for Market in marketList:
            Orders = {}
            Orders.update({Market: {}})
            while(True):
                try:
                    NHPage = json.loads(requests.get(CoinData[Coin]['NHUrl']).text)
                except:
                    print("NH page failed to load, retrying")
                else:
                    break
            try:
                CoinData[Coin]['marketScale'] = float(NHPage['stats'][Market]['marketFactor'])
            except KeyError:
                continue
            
            for i in range(len(NHPage['stats'][Market]['orders'])):
                Orders[Market].update({i: {'price': float(NHPage['stats'][Market]['orders'][i]['price']), 'activeRigs': int(NHPage['stats'][Market]['orders'][i]['rigsCount'])}})
                
                if Orders[Market][i]['activeRigs'] > 0:
                    priceStats.append(Orders[Market][i]['price'])
                #print(priceStats)

        # marketPrice is determined here
        priceStats.sort()
        CoinData[Coin]['marketPrice'] = statistics.median(priceStats)
        
        
    # Fill in necessary variables from whattomine.com
    # Also outsource profit calc to WTM
        calcHashrate = (inputMoney / CoinData[Coin]['marketPrice']) * CoinData[Coin]['marketScale']
        CoinData[Coin]['calcHashRate'] = calcHashrate
        CoinData[Coin]['WTMUrl'] += '&hr=' + str(round(calcHashrate / CoinData[Coin]['WTMRateScale'], 2))
        while(True):
            try:
                WTMPage = json.loads(requests.get(CoinData[Coin]['WTMUrl']).text)
            except:
                print("WTM page failed to load, retrying")
            else:
                break

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
        csvOutput.write(str(timeNow) + ',')
        for Coin in CoinList:
            csvOutput.write(str(round(CoinData[Coin]['profitBTC'],8)) + ',')
            csvOutput.write(str(round(CoinData[Coin]['nativeMined'],8)) + ',')
            csvOutput.write(str(round(CoinData[Coin]['exchangeRate'],8)) + ',')
            csvOutput.write(str(CoinData[Coin]['calcHashRate']) + ',')
            csvOutput.write(str(CoinData[Coin]['networkHR']) + ',')
            csvOutput.write(str(CoinData[Coin]['difficulty']) + ',')
            csvOutput.write(str(CoinData[Coin]['marketPrice']) + ',')
        csvOutput.write('\n')
        # explicit buffer flushing unnecessary -- flushed on close

    time.sleep(loopTime)
    
