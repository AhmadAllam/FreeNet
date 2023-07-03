import os
import sys
import time
import ipaddress
from datetime import datetime
from requests.exceptions import Timeout
import requests as r

try:
    from os import system as s
except ModuleNotFoundError:
    print('\npip install -r req.txt\n')
    sys.exit(1)

s('clear')
cg = '\033[92m'
cp = '\033[35m'
clb = '\033[94m'
cb = '\033[34m'
k = '\033[0m'
clr = '\033[91m'
ver = '@Ver 1.0 LTS'
aaa = datetime.now().strftime(' %d/%m/%y')

print()

try:
    range = input(f'{clb}[ {cp}hint {clb}]{k} enter ip with range to scan like " 192.0.0.0/24 " \n{cg}|\n└──{k}IP ~{cg}#{k} ')
    if range == '':
        print('Focus a little bit, please')
        sys.exit(1)
except:
    print('goodbay')
    sys.exit(1)

try:
    net4 = ipaddress.ip_network(range)
except ValueError as e:
    print(f'\n{clr}error{k}: ' + str(e))
    print()
    sys.exit(1)

v = 0
for x in net4.hosts():
    v = v + 1

print(f'\n{clb} scanning{k}: {range}\n{clb} total host in range {k}: {v}\n')

strt = time.time()
c = 0

filename = "host.txt"
with open(filename, "w") as f:
    for host in net4.hosts():
        h1 = f'http://{host}'
        h2 = h1

        try:
            x = r.get(h2, timeout=5)
            x = x.status_code
            rest = (str(f'{cg}{host}{k}') + ' | live - status ' + str(x))
            result = (str(f'{host}') )
            print (rest)
            c = c + 1
            f.write(result + "\n")
            
        except Timeout:
            print(str(f'{clr}{host}{k}') + ' | dead ')

        except KeyboardInterrupt:
            print('\nCTRL + C goodbay\nexit ...')
            sys.exit(1)

        except:
            print(str(f'{clr}{host}{k}') + ' | error ')

en = time.time()
print()
print(f'time spent: {en-strt} Seconds\n')
print(f'{cp}Hits{k}: {cg}{c}{k}/{v}\n')
