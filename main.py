import sys
import os
import requests
import time
import threading
# import pymysql
import logging
import time
from datetime import datetime
from datetime import date
import pandas as pd
# import prettytable as pt
from requests import exceptions


def geturl(url):
    requests.adapters.DEFAULT_RETRIES = 1
    s = requests.session()
    s.keep_alive = False
    try:
        t1 = time.time()
        response = requests.get(url, timeout=10)
        t2 = time.time()
    except exceptions.RequestException as e:
        geturl(url)
    except exceptions.HTTPError as e:
        print("http错误")
    except exceptions.ConnectionError as e:
        print("连接错误")
    except exceptions.ProxyError as e:
        print("代理错误")
    else:
        # print('请求耗时%ss' % (t2 - t1))
        if response.status_code == 200:
            json_r = response.json()
            return json_r
        else:
            print("请求错误：" + str(response.status_code) + str(response.reason) + str(url))


# 获取合约名称, 合约类型，交割日期，合约币种。并且去除USDT本位合约
def get_contract_info():
    codeId = []
    alias = []
    delivery = []
    base_currency = []
    today = datetime.today()
    i = 0
    url = 'https://www.okex.com/api/futures/v3/instruments'
    json_r = geturl(url)
    if not (json_r is None):
        while i < len(json_r):
            if json_r[i]["quote_currency"] == "USD":
                codeId.append(json_r[i]["instrument_id"])
                alias.append(json_r[i]["alias"])
                delivery_date = datetime.strptime(json_r[i]["delivery"], '%Y-%m-%d')
                interval = float((delivery_date - today).days)
                if interval == 0:
                    interval = 1
                delivery.append(interval)
                base_currency.append(json_r[i]["base_currency"])
            i = i + 1
        # dataframe = pd.DataFrame({'Contract ID': codeId, 'Code': alias, 'Delivery Date': delivery, 'Base Currency': base_currency})
        # dataframe.to_csv(r"C:\Users\marti\PycharmProjects\monitor\venv\future.csv", sep=',')

        return codeId, alias, delivery, base_currency


# 获取合约币种现货价格并生成词典
def get_spot_price():
    instrument_id = ['BTC', 'LTC', 'ETH', 'ETC', 'XRP', 'EOS', 'BCH', 'BSV', 'TRX']
    i = 0
    j = 0
    spot_price = []
    dict = {}
    while i < len(instrument_id):
        url = 'https://www.okex.com/api/spot/v3/instruments/' + instrument_id[i] + '-USDT/trades'
        json_r = geturl(url)
        if not (json_r is None):
            dict[instrument_id[i]] = float(json_r[0]["price"])
            i = i + 1

    codeId, alias, delivery, base_currency = get_contract_info()
    while j < len(base_currency):
        spot_price.append(dict[base_currency[j]])
        j = j + 1
    return spot_price


# 获取每个合约的价格
def get_future_price():
    codeId, alias, delivery, base_currency = get_contract_info()
    i = 0
    future_price = []
    while i < len(codeId):
        url = 'https://www.okex.com/api/futures/v3/instruments/' + codeId[i] + '/ticker'
        json_r = geturl(url)
        if not (json_r is None):
            future_price.append(float(json_r["last"]))
        i = i + 1
    return future_price


# 计算合约溢价及溢价百分比
def calculate_premium():
    future_price = get_future_price()
    spot_price = get_spot_price()
    codeId, alias, delivery, base_currency = get_contract_info()
    premium = []
    premium_in_perct = []
    annualized_return = []
    #四次买卖手续费损失
    fee = (1-0.0015) * (1-0.0015) * (1-0.0005) * (1-0.0005)
    i = 0
    while i < len(future_price):
        diff = future_price[i] - spot_price[i]
        if abs(diff) < 1:
            diff = round(diff, 4)
        else:
            diff = round(diff, 1)
        premium.append(diff)
        premium_in_perct.append(round(((future_price[i] - spot_price[i])/spot_price[i]*fee*100), 1))
        annualized_return.append(round((future_price[i] - spot_price[i])/spot_price[i]*fee*100/delivery[i]*365, 1))
        i = i + 1
    return premium, premium_in_perct, annualized_return


def to_txt():
    print("%s 开始TXT线程" % time.ctime())
    url_1 = 'https://www.okex.com/api/spot/v3/instruments/BTC-USDT/trades'
    url_2 = 'https://www.okex.com/api/spot/v3/instruments/ETH-USDT/trades'
    url_3 = 'https://www.okex.com/api/spot/v3/instruments/OKB-USDT/trades'
    # huobi法币交易盘口价格
    url_4 = 'https://otc-api.eiijo.cn/v1/data/trade-market?coinId=2&currency=1&tradeType=sell&currPage=1&payMethod=0&country=37&blockType=general&online=1'
    # USD汇率
    url_5 = 'http://www.apilayer.net/api/live?access_key=2fc9d3a4761e1c3cacbd2f6e0f6f205f&format=1&currencies=CNY'
    # 多空比数据 type 0-5分钟 1-1小时 2-24小时
    url_6 = 'https://www.okex.com/v3/futures/pc/market/longShortPositionRatio/BTC?t=&unitType=0'
    # 持仓量及交易量数据
    url_7 = 'https://www.okex.com/v3/futures/pc/market/openInterestAndVolume/BTC?t=&unitType=1'

    json_r1 = geturl(url_1)
    json_r2 = geturl(url_2)
    json_r3 = geturl(url_3)
    json_r4 = geturl(url_4)
    json_r5 = geturl(url_5)
    json_r6 = geturl(url_6)
    json_r7 = geturl(url_7)

    if (not (json_r1 is None)) & (not (json_r2 is None)) & (not (json_r3 is None)) & (not (json_r4 is None)) & (not (json_r5 is None)) & (not (json_r6 is None)) & (not (json_r7 is None)):
        btcprice = json_r1[0]["price"]
        ethprice = json_r2[0]["price"]
        okbprice = json_r3[0]["price"]

        usdtprice = float(json_r4['data'][0]['price'])
        usdprice = float(json_r5["quotes"]["USDCNY"])
        usdtpremium = round(usdtprice - usdprice, 2)
        usdtpremiumprect = round((usdtpremium / usdprice) * 100, 2)

        btcratio = json_r6["data"]["ratios"][-1]
        lowerline = 0.89
        upperline = 1.69

        btcfuturevolume = int(json_r7["data"]["openInterests"][-1])
        prebtcfuturevolume = int(json_r7["data"]["openInterests"][-2])
        btcfuturevolumechange = round((btcfuturevolume - prebtcfuturevolume) * 100 / prebtcfuturevolume, 2)

        file = r'C:\Users\marti\Documents\AJAX TEST\test.txt'
        with open(file, 'w+') as f:
            f.write("<h3 id=\"btcprice\">" + btcprice + "</h3>" + "\n" +
                    "<h3 id=\"ethprice\">" + ethprice + "</h3>" + "\n" +
                    "<h3 id=\"okbprice\">" + okbprice + "</h3>" + "\n" +
                    "<h3 id=\"usdtprice\">" + str(usdtprice) + "</h3>" + "\n" +
                    "<h3 id=\"usdtpremium\">" + str(usdtpremium) + "</h3>" + "\n" +
                    "<h3 id=\"usdtpremiumprect\">" + str(usdtpremiumprect) + "%</h3>" + "\n" +
                    "<h3 id=\"btcratio\">" + str(btcratio) + "</h3>" + "\n" +
                    "<h3 id=\"lowerline\">Buy at " + str(lowerline) + "</h3>" + "\n" +
                    "<h3 id=\"upperline\">Sell at " + str(upperline) + "</h3>" + "\n" +
                    "<h3 id=\"btcfuturevolume\">" + str(btcfuturevolume) + "</h3>" + "\n" +
                    "<h3 id=\"btcfuturevolumechange\">" + str(btcfuturevolumechange) + "%</h3>" + "\n"
                    )
        print("%s txt完成" % time.ctime())


'''
def print_table():
    tb = pt.PrettyTable()
    # tb.field_names = ["Code", "Type", "Spot Price", "Contract Price","Premium","Premium %","Annualized Return"]
    codeId, alias, delivery, base_currency = get_contract_info()
    premium, premium_in_perct, annualized_return = calculate_premium()
    future_price = get_future_price()
    spot_price = get_spot_price()
    tb.add_column("code", codeId)
    tb.add_column("type", alias)
    tb.add_column("future_price", future_price)
    tb.add_column("spot_price", spot_price)
    tb.add_column("premium", premium)
    tb.add_column("premium %", premium_in_perct)
    tb.add_column("annualized_return %", annualized_return)
    print(tb)
'''


def export_to_csv():
    print("%s 开始CSV线程" % time.ctime())
    codeId, alias, delivery, base_currency = get_contract_info()
    premium, premium_in_perct, annualized_return = calculate_premium()
    future_price = get_future_price()
    spot_price = get_spot_price()
    if len(codeId) * 6 == (len(alias) + len(future_price) + len(spot_price) + len(premium) + len(premium_in_perct) + len(annualized_return)):

        df = pd.DataFrame()
        df['code'] = codeId
        df['type'] = alias
        df['future'] = future_price
        df['spot'] = spot_price
        df['prium'] = premium
        df['prium%'] = premium_in_perct
        df['annual%'] = annualized_return

        df.set_index('code', inplace=True)
        df.to_csv(r'C:\Users\marti\Documents\AJAX TEST\future.csv')
        print("%s csv完成" % time.ctime())
    else:
        print("%s 数据不完整" % time.ctime())


def txt_loop():
    while True:
        to_txt()
        export_to_csv()


def csv_loop():
    while True:
        export_to_csv()
        time.sleep(10)

# export_to_csv()
# to_txt()
txt_loop()


