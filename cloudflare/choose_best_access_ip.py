import logging
import time

import requests
import sys
import random

import timer

BestPingNumbers = 5
BestSpeedNumbers = 1
YourHost = 'www.example.com' #should replace to yourself domain#

logging.basicConfig(
    filename='update_cf_ip.log',
    level=logging.INFO,
    format='%(levelname)s:%(asctime)s:%(message)s'
)

headers={
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua": "\"Google Chrome\";v=\"89\", \"Chromium\";v=\"89\", \";Not A Brand\";v=\"99\"",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "sec-ch-ua-mobile": "?0",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-requested-with": "XMLHttpRequest",
    "cookie": "_ga=GA1.2.1316038922.1614966873; __cfduid=df224a84bd4ee9a0fec6540963c1382661617814813"
  }


iplist = requests.get("https://ip.flares.cloud/ip_list.csv", headers=headers)
if iplist.status_code != 200:
    logging.info("get ip list fail, ", iplist.headers)
    sys.exit(0)

logging.debug(iplist.text)
ips = iplist.text.split()
logging.info("cf ip list, %r", ips)

headers['origin'] = 'https://ip.flares.cloud'
headers['referer'] = 'https://ip.flares.cloud/'
def genPingRequest(dip):
    nip = dip.replace('.', '-')
    headers['authority'] = '{}.ip.flares.cloud'.format(nip)

    url = 'https://{}.ip.flares.cloud/cdn-cgi/trace?{}'
    return url.format(nip, random.random())

def pingAll(iplist):
    t = timer.Timer()
    x = {}
    for ip in iplist:
        try:
            t.start()
            r = requests.get(genPingRequest(ip), headers=headers, timeout=2)
            t.stop()
            x[ip] = t.elapsed
            logging.info("ping %s elapsed %f", ip, t.elapsed)
            t.reset()
        except Exception as e:
            logging.error("try %s ping error, %r", ip, e)
            t.stop()
            t.reset()
            continue

    return x

def genSpeedRequest(dip):
    nip = dip.replace('.', '-')
    headers['authority'] = '{}.ip.flares.cloud'.format(nip)

    url = 'https://{}.ip.flares.cloud/img/m.webp?{}'
    return url.format(nip, random.random())

def downloadAll(iplist):
    t = timer.Timer()
    x = {}
    for ip in iplist:
        try:
            t.start()
            r = requests.get(genSpeedRequest(ip), headers=headers, timeout=10)
            t.stop()
            if r.status_code == 200:
                x[ip] = t.elapsed
            else:
                logging.warning("download %s error, %r", ip, r)
            logging.info("test speed %s elapsed %f", ip, t.elapsed)
            t.reset()
        except Exception as e:
            logging.error("try %s download error, %r", ip, e)
            t.stop()
            t.reset()
            continue

    return x

pings = pingAll(ips)
pingResult = sorted(pings.items(), key=lambda d: d[1])
logging.info("best ping result, %r", pingResult[:BestPingNumbers])

bestPing = [ x[0] for x in pingResult[:BestPingNumbers] ]
downloads = downloadAll(bestPing)
downloadResult = sorted(downloads.items(), key=lambda d: d[1])
logging.info("best speed resutl, %r", downloadResult[:BestSpeedNumbers])
print(downloadResult[:BestSpeedNumbers])

import subprocess
st = subprocess.getstatusoutput(r'''LANG=C LC_ALL=C sudo sed -i '' '/{}$/d' /etc/hosts'''.format(YourHost))
logging.info("del host %r", st)

resolve = [ "{} {}".format(x[0][:-1] + '2', YourHost) for x in downloadResult[:2] ]
txt = '\n'.join(resolve)
st = subprocess.getstatusoutput(r"""echo '{}' | sudo tee -a /etc/hosts""".format(txt))
logging.info("add new %s host %r", txt, st)
