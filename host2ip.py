import socket
import signal
import sys

RED = "\033[31m"
CC = "\033[0m"

def signal_handler(sig, frame):
    print(f'\n{RED}Goodbye!{CC}')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("")

with open("host.txt", "r") as reader, open("ip.txt", "w") as out:
    for host in reader.read().splitlines():
        try:
            ip = socket.gethostbyname(host)
        except socket.gaierror:
            ip = "no ip"
        
        out.write(ip + "\n")
        print(f'{host}: {ip}')

print("")
print("*** Great, now open the ip file ***")
print("MyTelegram")
print("@echo_Allam")