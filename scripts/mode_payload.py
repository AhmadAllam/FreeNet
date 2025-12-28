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

# Default input file for hosts
DEFAULT_HOSTS_FILE = "BugHosts/All_Hosts.txt"

# Default file containing payload definitions
DEFAULT_PAYLOAD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payloads.txt")

# Default target URL to test connectivity through payloads
DEFAULT_TARGET_URL = "http://www.google.com/generate_204"

# Default number of concurrent operations (async tasks)
DEFAULT_THREADS = 100

# Socket timeout in seconds for individual requests (payload tests)
SOCKET_TIMEOUT_SECONDS = 5 

# Directory for output files
OUTPUT_DIRECTORY = "BugHosts"

# Output file name for found bug hosts
OUTPUT_PAYLOAD_BUGS_FILE = "payload_bugs.txt"

# Output file name for payloads that caused errors (for debugging)
OUTPUT_EXC_PAYLOADS_FILE = "payloads_exc.txt"
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

class PayloadTester:
    def __init__(self):
        self.found_bug_hosts = set()
        self.scanned_count = 0
        self.failed_tests = 0
        self.total_payload_tests = 0
        self.output_file_path = os.path.join(OUTPUT_DIRECTORY, OUTPUT_PAYLOAD_BUGS_FILE)
        self.exc_payloads_file_path = os.path.join(OUTPUT_DIRECTORY, OUTPUT_EXC_PAYLOADS_FILE)
        self.payloads = []
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.scan_active = True

    async def load_payloads(self, filename):
        if not os.path.exists(filename):
            log(f"{RED}Payload file '{filename}' not found. Please create it.{CC}")
            sys.exit(1)

        async with aiofiles.open(filename, 'r') as f:
            async for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    self.payloads.append(line)
        if not self.payloads:
            log(f"{RED}No payloads found in '{filename}'. Exiting.{CC}")
            sys.exit(1)

    async def log_exc_payload(self, hostname, payload_line, error_message):
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
        async with aiofiles.open(self.exc_payloads_file_path, "a") as f:
            await f.write(f"Host: {hostname} | Payload: {payload_line} | Error: {error_message}\n")

    async def _request_aiohttp(self, method, url, session, headers, allow_redirects, verify_ssl, timeout):
        try:
            async with session.request(
                method, url, headers=headers, allow_redirects=allow_redirects, 
                ssl=verify_ssl, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                await response.read()
                return response
        except (aiohttp.ClientError, asyncio.TimeoutError, socket.gaierror):
            return None
        except Exception:
            return None

    async def test_payload_on_host(self, hostname, payload_line, target_url, session, semaphore):
        global shutdown_event
        await asyncio.sleep(0)
        if shutdown_event.is_set():
            return

        async with semaphore:
            await asyncio.sleep(0)
            if shutdown_event.is_set():
                return
                
            current_status_code = ""
            is_success = False
            
            headers = self.headers.copy() 
            method = "GET"
            url_to_request = target_url

            try:
                parts = payload_line.split(':', 1)
                payload_type = parts[0].strip().upper()
                payload_value = parts[1].strip() if len(parts) > 1 else ""

                if payload_type == "HOST_HEADER":
                    header_parts = payload_value.split(':', 1)
                    header_name = header_parts[0].strip()
                    header_value = header_parts[1].strip()
                    headers[header_name] = header_value
                    url_to_request = f"http://{hostname}" 
                elif payload_type == "URL_PREFIX":
                    url_to_request = payload_value.replace("TARGET_URL", target_url)
                elif payload_type == "URL_SUFFIX":
                    url_to_request = f"{target_url}{payload_value}"
                elif payload_type == "CONNECT_METHOD":
                    raise NotImplementedError("CONNECT_METHOD payloads are not yet supported directly via aiohttp. Requires raw async sockets.")
                elif payload_type == "HTTP_REQUEST_LINE_INJECTION":
                    sock = None
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        await asyncio.wait_for(
                            asyncio.to_thread(sock.settimeout, SOCKET_TIMEOUT_SECONDS),
                            timeout=SOCKET_TIMEOUT_SECONDS
                        )
                        host_ip = await asyncio.wait_for(
                            asyncio.to_thread(socket.gethostbyname, hostname),
                            timeout=3 
                        )
                        await asyncio.wait_for(
                            asyncio.to_thread(sock.connect, (host_ip, 80)),
                            timeout=SOCKET_TIMEOUT_SECONDS
                        ) 

                        full_request = f"{payload_value.replace('TARGET_URL', target_url).replace('[crlf]', '\\r\\n')}\r\nHost: {hostname}\r\n\r\n"
                        await asyncio.wait_for(
                            asyncio.to_thread(sock.sendall, full_request.encode()),
                            timeout=SOCKET_TIMEOUT_SECONDS
                        ) 

                        response_data = await asyncio.wait_for(
                            asyncio.to_thread(sock.recv, 4096),
                            timeout=SOCKET_TIMEOUT_SECONDS
                        ) 
                        response_data = response_data.decode(errors='ignore')

                        if response_data:
                            first_line = response_data.split('\r\n')[0]
                            if len(first_line.split(' ')) > 1:
                                current_status_code = first_line.split(' ')[1]
                                if current_status_code in ["200", "301", "302", "403"]:
                                    is_success = True
                            else:
                                current_status_code = "Malformed Response"
                        else:
                            current_status_code = "No Response"

                    except (socket.error, socket.timeout, asyncio.TimeoutError) as e:
                        current_status_code = f"Socket ERR ({e})"
                        await self.log_exc_payload(hostname, payload_line, str(e))
                    except Exception as e:
                        current_status_code = f"EXC ({e})"
                        await self.log_exc_payload(hostname, payload_line, str(e))
                    finally:
                        if sock:
                            await asyncio.to_thread(sock.close)

                elif payload_type == "REAL_HOST":
                    headers["Host"] = payload_value
                    url_to_request = f"http://{hostname}"
                else:
                    headers["X-Custom-Payload"] = payload_value
                    url_to_request = f"http://{hostname}"

                if payload_type != "HTTP_REQUEST_LINE_INJECTION":
                    response = await self._request_aiohttp(method, url_to_request, session, headers=headers, allow_redirects=False, verify_ssl=False, timeout=SOCKET_TIMEOUT_SECONDS)
                    if response:
                        current_status_code = str(response.status)
                        if response.status in [200, 301, 302, 403]:
                            is_success = True
                    else:
                        current_status_code = "ERR"
                    
            except NotImplementedError as e:
                current_status_code = "N/A"
                await self.log_exc_payload(hostname, payload_line, str(e))
            except Exception as e:
                current_status_code = "EXC"
                await self.log_exc_payload(hostname, payload_line, str(e))
            finally:
                with lock: 
                    self.scanned_count += 1
                    if is_success:
                        log(f"{GREEN}{hostname:<25} | {current_status_code:<5}{CC}")
                        self.found_bug_hosts.add(f"Host: {hostname:<25} | Payload: {payload_line:<50} | Status Code: {current_status_code}")
                    else:
                        self.failed_tests += 1

    async def save_bug_hosts(self):
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
        async with aiofiles.open(self.output_file_path, "w") as f:
            for entry in sorted(list(self.found_bug_hosts)):
                await f.write(f"{entry}\n")

    def _live_stats_updater(self):
        global total_scan_items 
        global shutdown_event 
        
        while self.scan_active and not shutdown_event.is_set(): 
            with lock:
                stats_message = (
                    f"{Y1}Scanning Progress:{CC} {self.scanned_count}/{self.total_payload_tests} | "
                    f"{GREEN}Bug Hosts:{len(self.found_bug_hosts)}{CC} | "
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
        print(f"{Y1}{'Payload Scan Summary':^40}{CC}")
        print(f"{Y1}{'=' * 40}{CC}")

        print(f"{Y1}{'Successful Bug Hosts Found':<28}: {len(self.found_bug_hosts)}{CC}")
        print(f"{Y1}{'Total Payload Tests':<28}: {self.total_payload_tests}{CC}")
        print(f"{Y1}{'Failed Payload Tests':<28}: {self.failed_tests}{CC}")

        print(f"{Y1}{'Time Elapsed':<28}: {elapsed_time:.2f} seconds{CC}")
        print(f"{Y1}{'Saved to':<28}: {os.path.basename(self.output_file_path)}{CC}")
        print(f"{Y1}{'=' * 40}{CC}")

    async def start_scan(self, hostnames, payload_file, target_url, threads):
        start_time = time.time()
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)

        host_len = 25
        code_len = 5
        log(f"{Y1}{'Host':<{host_len}} | {'Code':<{code_len}}{CC}") 
        log(f"{Y1}{'-'*host_len} | {'-'*code_len}{CC}")

        await self.load_payloads(payload_file) 
        self.total_payload_tests = len(hostnames) * len(self.payloads)
        global total_scan_items
        total_scan_items = self.total_payload_tests

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
                    for payload in self.payloads:
                        scan_tasks.append(
                            self.test_payload_on_host(hostname, payload, target_url, session, self.semaphore)
                        )
                await asyncio.gather(*scan_tasks, return_exceptions=True)

        except asyncio.CancelledError:
            log(f"{Y1}Scan interrupted. Attempting graceful shutdown...{CC}")
        finally:
            self.scan_active = False 

            if stats_thread.is_alive():
                stats_thread.join(timeout=2)
            await self.save_bug_hosts() 
            
            # --- START_MODIFICATION_1 ---
            if session and not session.closed:
                await session.close()
            # --- END_MODIFICATION_1 ---

            self.print_stats(start_time)

async def amain():
    global shutdown_event
    shutdown_event = asyncio.Event() 

    clear_screen()
    parser = argparse.ArgumentParser(
        description="Payload Tester: Tests hosts with various HTTP payloads.",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=52)
    )
    parser.add_argument("-f", "--file", help=f"Input file name (default: {DEFAULT_HOSTS_FILE})", type=str, default=DEFAULT_HOSTS_FILE)
    parser.add_argument("-t", "--threads", help=f"Number of concurrent operations (async tasks, default: {DEFAULT_THREADS})", type=int, default=DEFAULT_THREADS)
    parser.add_argument("--payloads-file", help=f"File containing payload definitions (default: {DEFAULT_PAYLOAD_FILE})", type=str, default=DEFAULT_PAYLOAD_FILE)
    parser.add_argument("--target-url", help=f"Target URL to test connectivity through payloads (default: {DEFAULT_TARGET_URL})", type=str, default=DEFAULT_TARGET_URL)

    global args
    
    if len(sys.argv) == 1:
        print(f"{Y1}--- Payload Tester ---{CC}\n")
        
        # File Input (Default)
        val_file = DEFAULT_HOSTS_FILE

        # Threads Input
        val_threads = input(f"{GREEN}Enter threads (default: {DEFAULT_THREADS}):\n{CC}").strip()
        if not val_threads: val_threads = str(DEFAULT_THREADS)

        # Payloads File Input (Default)
        val_payloads = DEFAULT_PAYLOAD_FILE
        
        # Target URL
        val_url = input(f"{GREEN}Enter target URL (default: {DEFAULT_TARGET_URL}):\n{CC}").strip()
        if not val_url: val_url = DEFAULT_TARGET_URL

        args = argparse.Namespace(
            file=val_file,
            threads=int(val_threads),
            payloads_file=val_payloads,
            target_url=val_url
        )
    else:
        args = parser.parse_args()

    tester = PayloadTester()

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

    if not os.path.exists(args.payloads_file):
        print(f"{RED}Payload file '{args.payloads_file}' not found. Please create it.{CC}")
        sys.exit(1)

    try:
        await tester.start_scan(
            hostnames_to_scan,
            args.payloads_file,
            args.target_url,
            args.threads
        )
    finally:
        tester.scan_active = False 
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
        # --- START_MODIFICATION_2 ---
        try:
            loop = asyncio.get_event_loop()
            
            # Check if the loop is still running or active, and if so, stop it gracefully
            if not loop.is_closed():
                # Cancel all outstanding tasks
                pending_tasks = [task for task in asyncio.all_tasks(loop) if task is not asyncio.current_task()]
                if pending_tasks:
                    for task in pending_tasks:
                        task.cancel()
                    try:
                        # Give some time for tasks to cancel
                        loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
                    except asyncio.CancelledError:
                        pass # Expected if tasks are cancelled
                    except Exception as e:
                        print(f"{RED}Error during pending task cleanup: {e}{CC}")
                
                # Close the loop
                if not loop.is_running(): 
                    loop.close()

            # Shutdown the default ThreadPoolExecutor if it exists
            if hasattr(loop, '_default_executor') and isinstance(loop._default_executor, concurrent.futures.ThreadPoolExecutor):
                loop._default_executor.shutdown(wait=True, cancel_futures=True)
        except RuntimeError:
            pass # Happens if the loop was already closed/stopped by asyncio.run
        except Exception as e:
            print(f"{RED}Error during final cleanup: {e}{CC}")
        # --- END_MODIFICATION_2 ---
