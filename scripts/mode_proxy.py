import os
import sys
import socket
import argparse
import threading
import time
import signal
import asyncio
import aiohttp
import aiofiles
from asyncio_throttle import Throttler
import concurrent.futures

import logging
logging.getLogger("aiohttp").setLevel(logging.ERROR)

# --- CONFIGURABLE_SETTINGS ---
# Colors for output display
CN = "\033[K"
Y1 = "\033[33m"
RED = "\033[31m"
GREEN = "\033[32m"
WHITE = "\033[97m"
CC = "\033[0m"

# Default input file for hosts (expected to be IPs for proxies)
DEFAULT_HOSTS_FILE = "BugHosts/All_Hosts.txt"

# Default number of concurrent operations (async tasks)
DEFAULT_THREADS = 100

# Default target URL to test proxy connectivity
DEFAULT_TARGET_URL = "http://www.google.com/generate_204"

# Default ports to test for open proxies (comma separated string)
DEFAULT_PROXY_PORTS_STR = "80,8080,3128,8000,8888"

# Socket timeout in seconds for individual requests
SOCKET_TIMEOUT_SECONDS = 5 

# Directory for output files
OUTPUT_DIRECTORY = "BugHosts"

# Output file name for open proxies
OUTPUT_OPEN_PROXIES_FILE = "open_proxies.txt"
# --- END_CONFIGURABLE_SETTINGS ---

lock = threading.RLock() 
last_stats_message = ""
shutdown_event = None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def log(value):
    global last_stats_message
    with lock:
        sys.stdout.write(f"{CN}\r")
        print(f"{value}{CC}")
        sys.stdout.flush()
        if last_stats_message:
            sys.stdout.write(f"{CN}{last_stats_message}{CC}\r")
            sys.stdout.flush()

def log_replace(value):
    global last_stats_message
    with lock:
        last_stats_message = value
        sys.stdout.write(f"{CN}{value}{CC}\r")
        sys.stdout.flush()

def signal_handler(sig, frame):
    global shutdown_event
    print(f'\n{RED}Goodbye! Attempting graceful shutdown...{CC}')
    if shutdown_event:
        shutdown_event.set()

signal.signal(signal.SIGINT, signal_handler)

class ProxyHunter:
    def __init__(self):
        self.open_proxies = set()
        self.scanned_count = 0
        self.failed_tests = 0
        self.total_proxy_tests = 0
        self.output_file_path = os.path.join(OUTPUT_DIRECTORY, OUTPUT_OPEN_PROXIES_FILE)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.scan_active = True
        self.semaphore = None

    async def _request_aiohttp_proxy(self, url, session, proxy_url, timeout, verify_ssl):
        try:
            async with session.get(url, proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=timeout), allow_redirects=False, ssl=verify_ssl, headers=self.headers) as response:
                await response.read()
                return response
        except (aiohttp.ClientError, asyncio.TimeoutError, socket.gaierror):
            return None
        except Exception:
            return None

    async def test_proxy_on_host(self, hostname, port, target_url, session, semaphore):
        global shutdown_event
        await asyncio.sleep(0)
        if shutdown_event.is_set():
            return

        async with semaphore:
            await asyncio.sleep(0)
            if shutdown_event.is_set():
                return

            is_success = False
            proxy_type = "UNKNOWN"
            status_code = ""
            full_proxy_address = f"{hostname}:{port}"

            try:
                proxy_url = f"http://{full_proxy_address}"
                response = await self._request_aiohttp_proxy(target_url, session, proxy_url, timeout=SOCKET_TIMEOUT_SECONDS, verify_ssl=False)
                
                if response:
                    status_code = str(response.status)
                    # Common success codes for a working proxy
                    if response.status in [200, 204, 301, 302, 403]: 
                        is_success = True
                        proxy_type = "HTTP"
                else:
                    status_code = f"HTTP_ERR"

            except Exception: 
                status_code = f"HTTP_EXC"

            if not is_success: 
                # Try CONNECT method for SOCKS/HTTPS proxies
                sock = None
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    await asyncio.wait_for(
                        asyncio.to_thread(sock.settimeout, SOCKET_TIMEOUT_SECONDS),
                        timeout=SOCKET_TIMEOUT_SECONDS
                    )
                    
                    proxy_ip = await asyncio.wait_for(
                        asyncio.to_thread(socket.gethostbyname, hostname),
                        timeout=3 
                    )
                    await asyncio.wait_for(
                        asyncio.to_thread(sock.connect, (proxy_ip, port)),
                        timeout=SOCKET_TIMEOUT_SECONDS
                    ) 

                    connect_target_host = target_url.replace("http://", "").replace("https://", "").split('/')[0]
                    connect_request = f"CONNECT {connect_target_host}:443 HTTP/1.1\r\nHost: {hostname}\r\n\r\n"
                    await asyncio.wait_for(
                        asyncio.to_thread(sock.sendall, connect_request.encode()),
                        timeout=SOCKET_TIMEOUT_SECONDS
                    ) 

                    response_data = await asyncio.wait_for(
                        asyncio.to_thread(sock.recv, 4096),
                        timeout=SOCKET_TIMEOUT_SECONDS
                    ) 
                    response_data = response_data.decode(errors='ignore')

                    if "200 Connection established" in response_data:
                        is_success = True
                        proxy_type = "CONNECT_TUNNEL"
                        status_code = "200"
                    elif response_data:
                        first_line = response_data.split('\r\n')[0]
                        if len(first_line.split(' ')) > 1:
                            status_code = first_line.split(' ')[1]
                        else:
                            status_code = "Malformed Response"
                    else:
                        status_code = "No Response"

                except (socket.error, socket.timeout, asyncio.TimeoutError) as e:
                    status_code = f"SOCK_ERR"
                except Exception as e:
                    status_code = f"EXC"
                finally:
                    if sock:
                        await asyncio.to_thread(sock.close) 

            with lock: 
                self.scanned_count += 1
                if is_success:
                    log(f"{GREEN}{full_proxy_address:<25} | {proxy_type:<10} | {status_code:<5}{CC}")
                    self.open_proxies.add(full_proxy_address)
                else:
                    self.failed_tests += 1

    async def save_open_proxies(self):
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
        async with aiofiles.open(self.output_file_path, "w") as f:
            for entry in sorted(list(self.open_proxies)):
                await f.write(f"{entry}\n")

    def _live_stats_updater(self):
        global total_scan_items 
        global shutdown_event 
        
        while self.scan_active and not shutdown_event.is_set(): 
            with lock:
                stats_message = (
                    f"{Y1}Scanning Progress:{CC} {self.scanned_count}/{self.total_proxy_tests} | "
                    f"{GREEN}Open Proxies:{len(self.open_proxies)}{CC} | "
                    f"{RED}Failed:{self.failed_tests}{CC}"
                )
                log_replace(stats_message)
            time.sleep(0.5)
        sys.stdout.write(f"{CN}\r")
        sys.stdout.flush()

    def print_stats(self, start_time):
        elapsed_time = time.time() - start_time
        label_width = 28 

        print(f"\n{Y1}{'=' * 40}{CC}")
        print(f"{Y1}{'Proxy Scan Summary':^40}{CC}")
        print(f"{Y1}{'=' * 40}{CC}")

        print(f"{Y1}{'Open Proxies Found':<28}: {len(self.open_proxies)}{CC}")
        print(f"{Y1}{'Total Proxy Tests':<28}: {self.total_proxy_tests}{CC}")
        print(f"{Y1}{'Failed Proxy Tests':<28}: {self.failed_tests}{CC}")

        print(f"{Y1}{'Time Elapsed':<28}: {elapsed_time:.2f} seconds{CC}")
        print(f"{Y1}{'Saved to':<28}: {os.path.basename(self.output_file_path)}{CC}")
        print(f"{Y1}{'=' * 40}{CC}")

    async def start_scan(self, hostnames, proxy_ports, target_url, threads):
        start_time = time.time()
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
        
        proxy_len = 25
        type_len = 10
        code_len = 5
        log(f"{Y1}{'Proxy':<{proxy_len}} | {'Type':<{type_len}} | {'Code':<{code_len}}{CC}")
        log(f"{Y1}{'-'*proxy_len} | {'-'*type_len} | {'-'*code_len}{CC}")

        self.total_proxy_tests = len(hostnames) * len(proxy_ports)
        global total_scan_items
        total_scan_items = self.total_proxy_tests

        self.semaphore = Throttler(threads) 

        stats_thread = threading.Thread(target=self._live_stats_updater)
        stats_thread.daemon = True
        stats_thread.start()

        session = None 
        try:
            session = aiohttp.ClientSession(headers=self.headers, trust_env=True)
            async with session: 
                scan_tasks = []
                for hostname in hostnames:
                    for port in proxy_ports:
                        scan_tasks.append(
                            self.test_proxy_on_host(hostname, port, target_url, session, self.semaphore)
                        )
                await asyncio.gather(*scan_tasks, return_exceptions=True)

        except asyncio.CancelledError:
            log(f"{Y1}Scan interrupted. Attempting graceful shutdown...{CC}")
        finally:
            self.scan_active = False 

            if stats_thread.is_alive():
                stats_thread.join(timeout=2)
            await self.save_open_proxies() 
            self.print_stats(start_time)

async def amain():
    global shutdown_event
    shutdown_event = asyncio.Event() 

    clear_screen()
    parser = argparse.ArgumentParser(
        description="Proxy Hunter: Scans for open HTTP/CONNECT proxies.",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=52)
    )
    parser.add_argument("-f", "--file", help=f"Input file name (default: {DEFAULT_HOSTS_FILE})", type=str, default=DEFAULT_HOSTS_FILE)
    parser.add_argument("-t", "--threads", help=f"Number of concurrent operations (async tasks, default: {DEFAULT_THREADS})", type=int, default=DEFAULT_THREADS)
    parser.add_argument("--target-url", help=f"Target URL to test connectivity through proxies (default: {DEFAULT_TARGET_URL})", type=str, default=DEFAULT_TARGET_URL)
    parser.add_argument("-p", "--proxy-ports", help=f"Target ports for proxy hunting (comma separated, default: {DEFAULT_PROXY_PORTS_STR})", type=str, default=DEFAULT_PROXY_PORTS_STR)

    global args
    
    if len(sys.argv) == 1:
        print(f"{Y1}--- Proxy Scanner ---{CC}\n")
        
        # File Input (Default)
        val_file = DEFAULT_HOSTS_FILE
        
        # Threads Input
        val_threads = input(f"{GREEN}Enter threads (default: {DEFAULT_THREADS}):\n{CC}").strip()
        if not val_threads: val_threads = str(DEFAULT_THREADS)

        # Target URL
        val_url = input(f"{GREEN}Enter target URL for testing (default: {DEFAULT_TARGET_URL}):\n{CC}").strip()
        if not val_url: val_url = DEFAULT_TARGET_URL
        
        # Ports Input
        val_ports = input(f"{GREEN}Enter proxy ports (default: {DEFAULT_PROXY_PORTS_STR}):\n{CC}").strip()
        if not val_ports: val_ports = DEFAULT_PROXY_PORTS_STR

        args = argparse.Namespace(
            file=val_file,
            threads=int(val_threads),
            target_url=val_url,
            proxy_ports=val_ports
        )
    else:
        args = parser.parse_args()

    hunter = ProxyHunter()

    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)

    all_hosts = set()
    if os.path.exists(args.file):
        async with aiofiles.open(args.file, 'r') as f:
            content = await f.read()
            all_hosts = set(content.splitlines())
    else:
        print(f"{RED}Input hosts file '{args.file}' does not exist. Please create it.{CC}")
        sys.exit(1)

    hostnames_to_scan = list(all_hosts)

    if not hostnames_to_scan:
        print(f"{RED}No hosts to scan. Please add hosts to your input file.{CC}")
        sys.exit(0)

    proxy_ports_list = []
    try:
        proxy_ports_list = list(map(int, args.proxy_ports.split(',')))
    except ValueError:
        print(f"{RED}Invalid port format for --proxy-ports. Please use comma-separated integers (e.g., 8080,3128).{CC}")
        sys.exit(1)

    try:
        await hunter.start_scan(
            hostnames_to_scan,
            proxy_ports_list,
            args.target_url,
            args.threads
        )
    finally:
        hunter.scan_active = False 
        current_loop = asyncio.get_running_loop()
        pending_tasks = [task for task in asyncio.all_tasks(current_loop) 
                         if task is not asyncio.current_task()]
        if pending_tasks:
            for task in pending_tasks:
                task.cancel()
            try:
                await asyncio.wait_for(asyncio.gather(*pending_tasks, return_exceptions=True), timeout=5)
            except asyncio.TimeoutError:
                log(f"{RED}Timeout waiting for pending tasks to finish. Some tasks may still be active.{CC}")
            except Exception as e:
                log(f"{RED}Error during final async task cleanup: {e}{CC}")

if __name__ == "__main__":
    try:
        asyncio.run(amain(), debug=False) 
    except KeyboardInterrupt:
        pass 
    except Exception as e:
        print(f"{RED}An unexpected error occurred: {e}{CC}")
    finally:
        try:
            loop = asyncio.get_event_loop()
            if hasattr(loop, '_default_executor') and isinstance(loop._default_executor, concurrent.futures.ThreadPoolExecutor):
                loop._default_executor.shutdown(wait=True, cancel_futures=True)
        except RuntimeError:
            pass
        except Exception as e:
            print(f"{RED}Error during ThreadPoolExecutor shutdown: {e}{CC}")
