import pandas as pd
from binance.spot import Spot

#  注意，此处端口要用587,465端口是ssl使用的（现在有的服务器发件端口是关闭的）。
from mail.MyEmail import MailClient

s = MailClient('smtp.qq.com', 587, '664527879@qq.com', 'aqfnfomlnrtjbdea')
s.set_keepalive(False)
#要发送的账号、标题、内容
s.send('664527879@qq.com', '测试', '测试邮件 From QQ')


# urlopen('https://www.howsmyssl.com/a/check').read()
proxies = { 'https': 'http://127.0.0.1:7890' }

# a = np.random.randn(5)
# print("a is an array:")
# print(a)
# s = Series(a)
# print("s is a Series:")
# print(s)
# response = requests.get("https://api.binance.com/api/v3/time")
# print(response)
# print(urlopen('https://testnet.binance.vision').read())

client = Spot(key='Dq06oObkJx6tEvlqcfEFR0BEm2bHmevKnr0YfouvCIa8Wshr3yrMWKeKeKjUzsfH', secret= 'pGQiPo2sc8gxkX9XeYcgdM86kpKkd82AswZfRJyU42OenjNeNikqNj1ILeFBs7ta', proxies=proxies, timeout=10000)


# Get klines of BTCUSDT at 1m interval
source = client.klines("LUNAUSDT", "1m", limit=10)
columnList = ['data', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume',
              'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore']
data = pd.DataFrame(source, columns=columnList, dtype=float)
data['data'] = pd.to_datetime(data['data'], unit='ms')
data.set_index('data',inplace=True)
print(data)

# print(client.klines("APEUSDT", "1m", limit = 10))
# # Get last 10 klines of BNBUSDT at 1h interval
# print(client.klines("BNBUSDT", "1h", limit=10))


# cerebro = bt.Cerebro()
# print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
#
# cerebro.run()
#
# print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())