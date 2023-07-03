#python script
import socket

def IpTara():
    site = raw_input("Enter the site now: ")
    try:
        ip = socket.gethostbyname(site)
        print(site + " IP address: " + ip)
    except Exception:
        print(site + " IP address not found.")
        return

    prefix = ip.rfind(".")
    subnet = ip[:prefix+1]
    filename = "host.txt"
    with open(filename, "w") as f:
        for i in range(256):
            addr = subnet + str(i)
            try:
                hostname = socket.gethostbyaddr(addr)[0]
                print(hostname)
                f.write(hostname + "\n")
            except Exception:
                print(addr + " does not have a hostname.")
                
IpTara()