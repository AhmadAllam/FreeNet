import os
import sys
import ssl
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

# Default input file for hosts
DEFAULT_HOSTS_FILE = "BugHosts/All_Hosts.txt"

# Default subdomain depth for SSL mode (e.g., example.com for depth 2 from sub.example.com)
DEFAULT_DEEP = 2

# Default number of concurrent operations (async tasks)
DEFAULT_THREADS = 100

# Socket timeout in seconds for individual requests
SOCKET_TIMEOUT_SECONDS = 5 

# Directory for output files
OUTPUT_DIRECTORY = "BugHosts"

# Output file names for SSL mode
OUTPUT_CLOUD_HOSTS_FILE = "cloud_hosts.txt"
OUTPUT_OTHER_HOSTS_FILE = "other_hosts.txt"
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

class SSLScanner:
    def __init__(self):
        self.scanned_ssl = set()
        self.cloud_hosts = set()
        self.other_hosts = set()
        self.failed_scans = 0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.scanned_count = 0
        self.live_cloud_hosts_count = 0
        self.live_other_hosts_count = 0
        self.live_failed_scans = 0
        self.scan_active = True
        self.cloud_hosts_output_path = os.path.join(OUTPUT_DIRECTORY, OUTPUT_CLOUD_HOSTS_FILE)
        self.other_hosts_output_path = os.path.join(OUTPUT_DIRECTORY, OUTPUT_OTHER_HOSTS_FILE)
        self.semaphore = None 

    async def _resolve_single_async(self, hostname):
        try:
            cname, _, host_list = await asyncio.wait_for(
                asyncio.to_thread(socket.gethostbyname_ex, hostname),
                timeout=3 
            )
            return hostname, [(host, cname if host == host_list[-1] else hostname) for host in host_list]
        except (socket.gaierror, socket.herror, asyncio.TimeoutError):
            return hostname, [(None, "DNS Failed")]
        except Exception:
            return hostname, [(None, "DNS Failed")]

    async def resolve(self, hostnames):
        results = {}
        dns_semaphore = asyncio.Semaphore(50)
        tasks = []
        for hostname in hostnames:
            async def resolve_with_semaphore(hname):
                async with dns_semaphore:
                    if shutdown_event.is_set(): return hname, []
                    return await self._resolve_single_async(hname)
            tasks.append(resolve_with_semaphore(hostname))
        
        resolved_list = await asyncio.gather(*tasks, return_exceptions=True)
        for item in resolved_list:
            if isinstance(item, Exception):
                continue
            hostname, resolved = item
            results[hostname] = resolved
        return results

    async def get_sni_response(self, hostname, deep):
        server_name_indication = ".".join(hostname.split(".")[0 - deep:])
        if server_name_indication in self.scanned_ssl:
            return None 
        
        with lock: 
            self.scanned_ssl.add(server_name_indication)

        sock = None
        try:
            host_ip = await asyncio.wait_for(
                asyncio.to_thread(socket.gethostbyname, server_name_indication),
                timeout=3 
            )
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            await asyncio.to_thread(sock.settimeout, SOCKET_TIMEOUT_SECONDS)
            
            wrapped_sock = await asyncio.to_thread(
                ssl.create_default_context().wrap_socket, 
                sock, server_hostname=server_name_indication
            )
            await asyncio.wait_for(
                asyncio.to_thread(wrapped_sock.connect, (host_ip, 443)),
                timeout=SOCKET_TIMEOUT_SECONDS
            )
            return {"status": "True", "server_name_indication": server_name_indication}
        except (socket.error, socket.timeout, ssl.SSLError, asyncio.TimeoutError):
            return {"status": "", "server_name_indication": server_name_indication}
        except Exception:
            return {"status": "", "server_name_indication": server_name_indication}
        finally:
            if sock:
                await asyncio.to_thread(sock.close)

    def print_result(self, host, hostname, sni=None):
        if sni and sni == "True":
            color = GREEN 
            host_display = f"{host if host else hostname:<20}" 
            status_str = f"{'SSL OK':<15}"
            log(f"{color}{host_display} | {status_str}{CC}")

            # Simplified logic for SSL, classifying based on hostname
            # You might need a more sophisticated check for "cloud" in SNI response
            if "cloud" in hostname.lower() or "cdn" in hostname.lower() or "azure" in hostname.lower() or "amazon" in hostname.lower(): # Basic heuristic
                self.cloud_hosts.add(hostname)
                with lock:
                    self.live_cloud_hosts_count = len(self.cloud_hosts)
            else:
                self.other_hosts.add(hostname)
                with lock:
                    self.live_other_hosts_count = len(self.other_hosts)

    def _live_stats_updater(self):
        global total_scan_items 
        global shutdown_event 
        
        while self.scan_active and not shutdown_event.is_set(): 
            with lock:
                total_successful_connections = self.live_cloud_hosts_count + self.live_other_hosts_count
                stats_message = (
                    f"{Y1}Scanning Progress:{CC} {self.scanned_count}/{total_scan_items} | "
                    f"{GREEN}Successful:{total_successful_connections}{CC} | "
                    f"{RED}Failed:{self.live_failed_scans}{CC}"
                )
                log_replace(stats_message)
            time.sleep(0.5)
        sys.stdout.write(f"{CN}\r")
        sys.stdout.flush()

    def print_stats(self, start_time):
        elapsed_time = time.time() - start_time
        label_width = 28 

        print(f"\n{Y1}{'=' * 40}{CC}")
        print(f"{Y1}{'SSL Scan Statistics':^40}{CC}")
        print(f"{Y1}{'=' * 40}{CC}")

        total_successful_connections = len(self.cloud_hosts) + len(self.other_hosts)
        print(f"{Y1}{'Successful Connections':<28}: {total_successful_connections}{CC}")
        print(f"{Y1}{'Failed Connections':<28}: {self.failed_scans}{CC}")

        print(f"{Y1}{'Time Elapsed':<28}: {elapsed_time:.2f} seconds{CC}")
        print(f"{Y1}{'Saved Cloud Hosts to':<28}: {os.path.basename(self.cloud_hosts_output_path)}{CC}")
        print(f"{Y1}{'Saved Other Hosts to':<28}: {os.path.basename(self.other_hosts_output_path)}{CC}")
        print(f"{Y1}{'=' * 40}{CC}")

    async def _scan_single_target(self, hostname, deep, resolved_hosts_map):
        global shutdown_event
        await asyncio.sleep(0)

        if shutdown_event.is_set():
            return []

        async with self.semaphore:
            await asyncio.sleep(0)
            if shutdown_event.is_set(): 
                return []
            
            results = []
            resolved_for_host = resolved_hosts_map.get(hostname, [(None, "DNS Failed")])

            if not resolved_for_host or all(host_ip is None for host_ip, _ in resolved_for_host):
                with lock: 
                    self.failed_scans += 1
                    self.scanned_count += 1
                    self.live_failed_scans = self.failed_scans
                return results

            for host_ip, resolved_hostname in resolved_for_host:
                await asyncio.sleep(0)
                if shutdown_event.is_set(): return [] 
                if host_ip is None: continue 

                response = await self.get_sni_response(resolved_hostname, deep)
                with lock: 
                    self.scanned_count += 1
                    if response and response["status"] == "True":
                        self.print_result(host_ip, response["server_name_indication"], sni=response["status"])
                        results.append((host_ip, response["server_name_indication"], None, None, None, response["status"]))
                    else:
                        self.failed_scans += 1
                        self.live_failed_scans = self.failed_scans
            return results

    async def start_scan(self, hostnames, deep, threads):
        start_time = time.time()
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)

        host_len = 20
        status_len = 15
        
        log(f"{Y1}{'Host':<{host_len}} | {'Status':<{status_len}}{CC}")
        log(f"{Y1}{'-'*host_len} | {'-'*status_len}{CC}")

        global total_scan_items
        total_scan_items = len(hostnames)

        self.semaphore = Throttler(threads) 

        stats_thread = threading.Thread(target=self._live_stats_updater)
        stats_thread.daemon = True
        stats_thread.start()

        try:
            resolved_hosts_map = await self.resolve(hostnames)
            
            scan_tasks = []
            for hostname in hostnames:
                scan_tasks.append(
                    self._scan_single_target(hostname, deep, resolved_hosts_map)
                )
            await asyncio.gather(*scan_tasks, return_exceptions=True)

        except asyncio.CancelledError:
            log(f"{Y1}Scan interrupted. Attempting graceful shutdown...{CC}")
        finally:
            self.scan_active = False 

            if stats_thread.is_alive():
                stats_thread.join(timeout=2)

            async with aiofiles.open(self.cloud_hosts_output_path, "a+") as f:
                await f.seek(0)
                existing_content = await f.read()
                existing = set(existing_content.splitlines())
                for hostname in self.cloud_hosts:
                    if hostname not in existing:
                        await f.write(f"{hostname}\n")
            async with aiofiles.open(self.other_hosts_output_path, "a+") as f:
                await f.seek(0)
                existing_content = await f.read()
                existing = set(existing_content.splitlines())
                for hostname in self.other_hosts:
                    if hostname not in existing:
                        await f.write(f"{hostname}\n")

            self.print_stats(start_time)

async def amain():
    global shutdown_event
    shutdown_event = asyncio.Event() 

    clear_screen()
    parser = argparse.ArgumentParser(
        description="SSL Host Scanner: Scans hosts for valid SSL connections (SNI).",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=52)
    )
    parser.add_argument("-d", "--deep", help=f"Subdomain depth for SNI (e.g., 2 for example.com from sub.example.com, default: {DEFAULT_DEEP})", type=int, default=DEFAULT_DEEP)
    parser.add_argument("-f", "--file", help=f"Input file name (default: {DEFAULT_HOSTS_FILE})", type=str, default=DEFAULT_HOSTS_FILE)
    parser.add_argument("-t", "--threads", help=f"Number of concurrent operations (async tasks, default: {DEFAULT_THREADS})", type=int, default=DEFAULT_THREADS)
    
    global args
    
    if len(sys.argv) == 1:
        print(f"{Y1}--- SSL Scanner ---{CC}\n")
        
        # File Input (Default)
        val_file = DEFAULT_HOSTS_FILE
        
        # Threads Input
        val_threads = input(f"{GREEN}Enter threads (default: {DEFAULT_THREADS}):\n{CC}").strip()
        if not val_threads: val_threads = str(DEFAULT_THREADS)

        # Deep Input
        val_deep = input(f"{GREEN}Enter subdomain depth for SNI (default: {DEFAULT_DEEP}):\n{CC}").strip()
        if not val_deep: val_deep = str(DEFAULT_DEEP)

        args = argparse.Namespace(
            file=val_file,
            threads=int(val_threads),
            deep=int(val_deep)
        )
    else:
        args = parser.parse_args()

    scanner = SSLScanner()

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

    try:
        await scanner.start_scan(
            hostnames_to_scan,
            args.deep,
            args.threads
        )
    finally:
        scanner.scan_active = False 
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
