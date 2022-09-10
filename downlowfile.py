import os

from urllib.request import urlretrieve

time = ['2021-05', '2021-06', '2021-07', '2021-08', '2021-09', '2021-10', '2021-11', '2021-12',
        '2022-01', '2022-02', '2022-03', '2022-04', '2022-05', '2022-06', '2022-07' ]
# time = ['2021-05', '2021-06', '2021-07', '2021-08', '2021-09', '2021-10', '2021-11', '2021-12',
#         '2022-01', '2022-02', '2022-03', '2022-04']
import socket
socket.setdefaulttimeout(30.0)
coin = 'ETH'

for t in time:
    image_url = ("https://data.binance.vision/data/spot/monthly/klines/%sUSDT/1h/%sUSDT-1h-%s.zip" % (coin, coin, t))
    print(image_url)
    urlretrieve(image_url, ('D:\学习\区块链\\biandata\%s\%sUSDT-1h-%s.zip' % (coin.lower(), coin, t)))  # 将什么文件存放到什么位置
