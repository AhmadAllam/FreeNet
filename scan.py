# color settings
CN = "\033[K"
Y1 = "\033[33m"
RED = "\033[31m"
GREEN = "\033[32m"
CC = "\033[0m"

# Scan settings
DEFAULT_DEEP = 2
DEFAULT_MODE = "direct"
DEFAULT_PORT = 80
DEFAULT_THREADS = 8
DEFAULT_IGNORE_REDIRECT_LOCATION = ""
DEFAULT_METHOD = "HEAD"
DEFAULT_PROXY = None

INJECT_SERVER_NAME_INDICATION = "twitter.com"
INJECT_TIMEOUT = 5
INJECT_SHOW_LOG = False

#______________________Script____________________
import os
import re
import sys
import ssl
import json
import queue
import socket
import argparse
import requests
import threading
import signal

lock = threading.RLock()

def get_value_from_list(data, index, default=""):
    return data[index] if index < len(data) else default

def log(value):
    with lock:
        print(f"{CN}{value}{CC}")

def log_replace(value):
    sys.stdout.write(f"{CN}{value}{CC}\r")
    sys.stdout.flush()

def signal_handler(sig, frame):
    print(f'\n{RED}Goodbye!{CC}')  
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class BugScanner:
    brainfuck_config = {
        "ProxyRotator": {"Port": "3080"},
        "Inject": {
            "Enable": True,
            "Type": 2,
            "Port": "8989",
            "Rules": {},
            "Payload": "",
            "MeekType": 0,
            "ServerNameIndication": "twitter.com",
            "Timeout": 5,
            "ShowLog": False,
        },
        "PsiphonCore": 4,
        "Psiphon": {
            "CoreName": "psiphon-tunnel-core",
            "Tunnel": 1,
            "Region": "",
            "Protocols": [
                "FRONTED-MEEK-HTTP-OSSH",
                "FRONTED-MEEK-OSSH",
            ],
            "TunnelWorkers": 6,
            "KuotaDataLimit": 4,
            "Authorizations": [""],
        },
    }
    scanned = {"direct": {}, "ssl": {}, "proxy": {}}

    def request(self, method, hostname, port, proxy=None):
        try:
            url = f"{('https' if port == 443 else 'http')}://{hostname if port == 443 else f'{hostname}:{port}'}"
            log_replace(f"{method} {url}")
            return requests.request(method, url, proxies=proxy, timeout=5, allow_redirects=False)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            return None

    def resolve(self, hostname):
        try:
            cname, hostname_list, host_list = socket.gethostbyname_ex(hostname)
        except (socket.gaierror, socket.herror):
            return
        for i in range(len(hostname_list)):
            yield get_value_from_list(host_list, i, host_list[-1]), hostname_list[i]
        yield host_list[-1], cname

    def get_response(self, method, hostname, port, proxy=None):
        if proxy:
            return self.request(method, hostname, port, {"http": f"http://{proxy}", "https": f"http://{proxy}"})
        return self.request(method, hostname, port)

    def get_direct_response(self, method, hostname, port):
        if f"{hostname}:{port}" in self.scanned["direct"]:
            return None
        response = self.get_response(method, hostname, port)
        if response:
            self.scanned["direct"][f"{hostname}:{port}"] = {
                "status_code": response.status_code,
                "server": response.headers.get("server", ""),
            }
            return self.scanned["direct"][f"{hostname}:{port}"]
        return None

    def get_sni_response(self, hostname, deep):
        server_name_indication = ".".join(hostname.split(".")[0 - deep:])
        if server_name_indication in self.scanned["ssl"]:
            return None
        with lock:
            self.scanned["ssl"][server_name_indication] = None
        try:
            log_replace(server_name_indication)
            socket_client = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2).wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=server_name_indication)
            socket_client.settimeout(5)
            socket_client.connect(("httpbin.org", 443))
            response = {"status": "True", "server_name_indication": server_name_indication}
        except:
            response = {"status": "", "server_name_indication": server_name_indication}
        finally:
            self.scanned["ssl"][server_name_indication] = response
            return response

    def get_proxy_response(self, method, hostname, port, proxy):
        if f"{hostname}:{port}" in self.scanned["proxy"]:
            return None
        response = self.get_response(method, hostname, port, proxy)
        if response and response.headers.get("location") != self.ignore_redirect_location:
            self.scanned["proxy"][f"{hostname}:{port}"] = {
                "proxy": proxy,
                "method": method,
                "url": response.url,
                "status_code": response.status_code,
                "headers": response.headers,
            }
            return self.scanned["proxy"][f"{hostname}:{port}"]
        return None

    def print_result(self, host, hostname, port=None, status_code=None, server=None, sni=None):
        color = Y1
        server_str = f"{server:<20}" if server else " " * 20
        status_code_str = f"{status_code:<4}" if status_code else " " * 4
        hostname_str = f"{hostname}" if hostname else " "
        
        if server and server.lower().startswith("cloud"):
            color = GREEN
            with open("cloud.txt", "a+") as f:
                f.seek(0)
                if hostname not in f.read():
                    f.write(f"{hostname}\n")
        elif server and server.lower().startswith("apache"):
            with open("apache.txt", "a+") as f:
                f.seek(0)
                if hostname not in f.read():
                    f.write(f"{hostname}\n")
        elif server and server.lower().startswith("nginx"):
            with open("nginx.txt", "a+") as f:
                f.seek(0)
                if hostname not in f.read():
                    f.write(f"{hostname}\n")
        elif server and server.lower().startswith("awselb"):
            with open("awselb.txt", "a+") as f:
                f.seek(0)
                if hostname not in f.read():
                    f.write(f"{hostname}\n")
        else:
            with open("other.txt", "a+") as f:
                f.seek(0)
                if hostname not in f.read():
                    f.write(f"{hostname}\n")

        log(f"{color}{host:<15} {status_code_str} {server_str} {f'  {sni:<4}' if sni else '    '}  {hostname_str}{CC}")

    def print_result_proxy(self, response):
        if response is None:
            return
        data = [f"{response['proxy']} -> {response['method']} {response['url']} ({response['status_code']})"]
        data.extend([f"|   {key}: {val}" for key, val in response['headers'].items()])
        log("\n".join(data) + "\n")

    def scan(self):
        while True:
            for host, hostname in self.resolve(self.queue_hostname.get()):
                if self.mode == "direct":
                    response = self.get_direct_response(self.method, hostname, self.port)
                    if response:
                        self.print_result(host, hostname, port=self.port, status_code=response["status_code"], server=response["server"])
                elif self.mode == "ssl":
                    response = self.get_sni_response(hostname, self.deep)
                    if response:
                        self.print_result(host, response["server_name_indication"], sni=response["status"])
                elif self.mode == "proxy":
                    response = self.get_proxy_response(self.method, hostname, self.port, self.proxy)
                    self.print_result_proxy(response)
            self.queue_hostname.task_done()

    def start(self, hostnames):
        if self.mode == "direct":
            self.print_result("host", "hostname", status_code="code", server="server")
            self.print_result("----", "--------", status_code="----", server="------")
        elif self.mode == "ssl":
            self.print_result("host", "hostname", sni="sni")
            self.print_result("----", "--------", sni="---")

        self.queue_hostname = queue.Queue()
        for hostname in hostnames:
            self.queue_hostname.put(hostname)

        for _ in range(min(self.threads, self.queue_hostname.qsize())):
            thread = threading.Thread(target=self.scan)
            thread.daemon = True
            thread.start()

        self.queue_hostname.join()

        if self.output is not None and self.mode == "direct" and len(self.brainfuck_config["Inject"]["Rules"]):
            if os.name == "nt":
                self.brainfuck_config["Psiphon"]["CoreName"] += ".exe"
            with open(f"config.{self.output}.json", 'w', encoding='utf-8') as f:
                dump = json.dumps(self.brainfuck_config, indent=4, ensure_ascii=False)
                data = re.sub('\n +', lambda match: '\n' + '\t' * int((len(match.group().strip('\n')) / 4)), dump)
                f.write(data)

def main():
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=52))
    parser.add_argument("-d", "--deep", help="subdomain deep", dest="deep", type=int, default=DEFAULT_DEEP)
    parser.add_argument("-m", "--mode", help="direct, proxy, ssl", dest="mode", type=str, default=DEFAULT_MODE)
    parser.add_argument("-o", "--output", help="output file name", dest="output", type=str)
    parser.add_argument("-p", "--port", help="target port", dest="port", type=int, default=DEFAULT_PORT)
    parser.add_argument("-t", "--threads", help="threads", dest="threads", type=int, default=DEFAULT_THREADS)
    parser.add_argument("-I", "--ignore-redirect-location", help="ignore redirect location for --mode proxy", dest="ignore_redirect_location", type=str, default=DEFAULT_IGNORE_REDIRECT_LOCATION)
    parser.add_argument("-M", "--method", help="http method", dest="method", type=str, default=DEFAULT_METHOD)
    parser.add_argument("-P", "--proxy", help="proxy.example.com:8080", dest="proxy", type=str)

    args = parser.parse_args()
    if args.mode == "proxy" and not args.proxy:
        parser.print_help()
        return

    bugscanner = BugScanner()
    bugscanner.deep = args.deep
    bugscanner.ignore_redirect_location = args.ignore_redirect_location
    bugscanner.method = args.method.upper()
    bugscanner.mode = args.mode
    bugscanner.output = args.output
    bugscanner.port = args.port
    bugscanner.proxy = args.proxy
    bugscanner.threads = args.threads
    
    with open("host.txt") as f:
        hostnames = f.read().splitlines()
    
    bugscanner.start(hostnames)

if __name__ == "__main__":
    main()

print("                                ")
print("********************* finished********************")