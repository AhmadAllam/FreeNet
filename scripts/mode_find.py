import socket
import asyncio
import signal
import sys
import argparse
import os
from concurrent.futures import ThreadPoolExecutor
import time

# --- CONFIGURABLE_SETTINGS ---
# Colors for output display
CN = "\033[K"
Y1 = "\033[33m"
RED = "\033[31m"
GREEN = "\033[32m"
WHITE = "\033[97m"
CC = "\033[0m"

# DNS servers used by the script
DNS_SERVER_1 = "62.240.110.198"
DNS_SERVER_2 = "62.240.110.197"

# Default site if none is specified
DEFAULT_SITE = "vodafone.com.eg"

# Subnet masks
MASK_CHOICE_1 = (255, 255, 255, 0) # /24
MASK_CHOICE_2 = (255, 255, 0, 0)   # /16

# Maximum concurrent requests
MAX_CONCURRENT_REQUESTS = 50

# Socket timeout in seconds
SOCKET_TIMEOUT_SECONDS = 3

# Directory for output files
OUTPUT_DIRECTORY = "BugHosts"

# Output file names
OUTPUT_HOSTS_FILE = "All_Hosts.txt"
OUTPUT_IPS_FILE = "All_IP.txt"
# --- END_CONFIGURABLE_SETTINGS ---


def signal_handler(sig, frame):
    sys.stdout.write(f'\n{RED}Goodbye!{CC}\n')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def set_dns():
    try:
        with open('/etc/resolv.conf', 'w') as file:
            file.write(f"nameserver {DNS_SERVER_1}\n")
            file.write(f"nameserver {DNS_SERVER_2}\n")
    except PermissionError:
        sys.stdout.write(f"{RED}Warning: No root privileges, continuing without changing DNS...{CC}\n")
        sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(f"{RED}Warning: Failed to set DNS ({e}), continuing anyway...{CC}\n")
        sys.stdout.flush()

async def get_hostname(addr):
    try:
        hostname = await asyncio.to_thread(socket.gethostbyaddr, addr)
        return addr, hostname[0]
    except (socket.herror, socket.gaierror, socket.timeout):
        return addr, None
    except Exception as e:
        sys.stdout.write(f"{RED}An unexpected error occurred: {e}{CC}\n")
        sys.stdout.flush()
        return addr, None

def get_ip_address_blocking(site):
    try:
        ip = socket.gethostbyname(site)
        return site, ip
    except socket.gaierror:
        return site, None
    except Exception as e:
        sys.stdout.write(f"{RED}An unexpected error occurred while getting IP address: {e}{CC}\n")
        sys.stdout.flush()
        return site, None

async def get_ip_address(site):
    site, ip = await asyncio.to_thread(get_ip_address_blocking, site)
    return site, ip

def print_stats(site, mask, discovered_hostnames_count, start_time):
    elapsed_time = time.time() - start_time
    mask_str = '.'.join(map(str, mask))
    
    label_width = 19 

    sys.stdout.write(f"{Y1}{'=' * 50}{CC}\n")
    sys.stdout.write(f"{Y1}{' ':>2}{'Scan Results':^46}{' ':>2}{CC}\n")
    sys.stdout.write(f"{Y1}{'=' * 50}{CC}\n")
    sys.stdout.write(f"{Y1}{'  Target Host        :':<{label_width}} {site}{CC}\n")
    sys.stdout.write(f"{Y1}{'  Subnet Mask        :':<{label_width}} {mask_str}{CC}\n")
    sys.stdout.write(f"{Y1}{'  New Host Count     :':<{label_width}} {str(discovered_hostnames_count)}{CC}\n")
    sys.stdout.write(f"{Y1}{'  Elapsed Time       :':<{label_width}} {f'{elapsed_time:.2f} seconds'}{CC}\n")
    sys.stdout.write(f"{Y1}{'=' * 50}{CC}\n")
    sys.stdout.flush()

async def find_hostnames_in_subnet(ip, mask, max_requests_param):
    start_time = time.time()
    if ip is None:
        sys.stdout.write(f"{RED}Error: IP address is None. Cannot perform subnet scan.{CC}\n")
        sys.stdout.flush()
        return
    
    try:
        ip_parts = list(map(int, ip.split('.')))
        if len(ip_parts) != 4 or not all(0 <= part <= 255 for part in ip_parts):
            raise ValueError("Invalid IP address format or range.")
    except ValueError as e:
        sys.stdout.write(f"{RED}Error: Invalid IP address '{ip}' - {e}. Cannot perform subnet scan.{CC}\n")
        sys.stdout.flush()
        return

    sys.stdout.write(f"{Y1}{'-' * 55}{CC}\n")
    sys.stdout.write(f"{Y1}{'Host IP':<14}      {Y1}{'Hostname':<25}{CC}\n")
    sys.stdout.write(f"{Y1}{'-' * 55}{CC}\n")
    sys.stdout.flush()
    
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)
    output_path = os.path.join(OUTPUT_DIRECTORY, OUTPUT_HOSTS_FILE)
    ip_output_path = os.path.join(OUTPUT_DIRECTORY, OUTPUT_IPS_FILE)
    
    new_discovered_hostnames = set()
    all_known_hostnames = set()
    all_known_ips = set()

    if os.path.exists(output_path):
        with open(output_path, "r") as f_read:
            for line in f_read:
                all_known_hostnames.add(line.strip())

    if os.path.exists(ip_output_path):
        with open(ip_output_path, "r") as f_read_ip:
            for line in f_read_ip:
                all_known_ips.add(line.strip())

    try:
        target_addrs = []
        if mask == MASK_CHOICE_1:
            subnet_prefix = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}."
            for i in range(256):
                target_addrs.append(f"{subnet_prefix}{i}")

        elif mask == MASK_CHOICE_2:
            base_prefix = f"{ip_parts[0]}.{ip_parts[1]}."
            for third_octet in range(256):
                for fourth_octet in range(256):
                    target_addrs.append(f"{base_prefix}{third_octet}.{fourth_octet}")
        
        semaphore = asyncio.Semaphore(max_requests_param)

        async def get_hostname_with_semaphore(addr):
            async with semaphore:
                return await get_hostname(addr)

        tasks = [get_hostname_with_semaphore(addr) for addr in target_addrs]
        
        for future in asyncio.as_completed(tasks):
            addr, hostname = await future
            
            if hostname:
                if hostname not in all_known_hostnames:
                    sys.stdout.write(f"{GREEN}{addr:<14}      {GREEN}{hostname:<25}{CC}\n")
                    sys.stdout.flush()
                    new_discovered_hostnames.add(hostname)
                    all_known_hostnames.add(hostname) 
            else:
                sys.stdout.write(f"{GREEN}{addr:<14}      {GREEN}{'No hostname':<25}{CC}\n")
                sys.stdout.flush()
        
        if new_discovered_hostnames:
            with open(output_path, "a") as f_write:
                for hostname in new_discovered_hostnames:
                    f_write.write(hostname + "\n")

    except Exception as e:
        sys.stdout.write(f"{RED}An unexpected error occurred while fetching hostnames: {e}{CC}\n")
        sys.stdout.flush()
    
    sys.stdout.write(f"{Y1}{'=' * 50}{CC}\n")
    sys.stdout.write(f"{Y1}{' ':>2}{'Converting Hostnames to IPs':^46}{' ':>2}{CC}\n")
    sys.stdout.flush()
    
    new_discovered_ips = set()
    try:
        ip_conversion_semaphore = asyncio.Semaphore(max_requests_param)

        async def get_ip_address_with_semaphore(hostname):
            async with ip_conversion_semaphore:
                return await get_ip_address(hostname)

        ip_conversion_tasks = [get_ip_address_with_semaphore(hostname) for hostname in new_discovered_hostnames]
        
        for future in asyncio.as_completed(ip_conversion_tasks):
            original_hostname, ip_address = await future
            
            if ip_address:
                if ip_address not in all_known_ips:
                    sys.stdout.write(f"{GREEN}{original_hostname:<14}      {GREEN}{ip_address:<25}{CC}\n")
                    sys.stdout.flush()
                    new_discovered_ips.add(ip_address)
                    all_known_ips.add(ip_address)
            else:
                sys.stdout.write(f"{GREEN}{original_hostname:<14}      {GREEN}{'No IP found':<25}{CC}\n")
                sys.stdout.flush()

        if new_discovered_ips:
            with open(ip_output_path, "a") as ip_file_write:
                for ip_addr in new_discovered_ips:
                    ip_file_write.write(ip_addr + "\n")

    except Exception as e:
        sys.stdout.write(f"{RED}An unexpected error occurred while saving IP addresses: {e}{CC}\n")
        sys.stdout.flush()
    
    print_stats(args.site, mask, len(new_discovered_hostnames), start_time)

async def main_async():
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()
    set_dns()
    socket.setdefaulttimeout(SOCKET_TIMEOUT_SECONDS)

    parser = argparse.ArgumentParser(
        description=(
            "-h, --help    show this help\n"
            "-s SITE       Target site (e.g., www.freesite.com)\n"
            "-m {1,2}      Subnet mask: 1=/24, 2=/16"
        ),
        epilog="Example:\n  python find.py -s www.vodafone.com -m 2",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )

    parser.add_argument(
        '-h', '--help', action='help', default=argparse.SUPPRESS,
        help=argparse.SUPPRESS
    )
    
    parser.add_argument(
        '-s', '--site',
        default=DEFAULT_SITE,
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        '-m', '--mask',
        type=int,
        default=1,
        choices=[1, 2],
        help=argparse.SUPPRESS
    )
    
    global args
    if len(sys.argv) == 1:
        print(f"{Y1}--- Host Finder ---{CC}\n")
        val_site = input(f"{GREEN}Enter target site (default: {DEFAULT_SITE}):\n{CC}").strip()
        if not val_site: val_site = DEFAULT_SITE
        
        val_mask = input(f"{GREEN}Enter subnet mask [1=/24, 2=/16] (default: 1):\n{CC}").strip()
        if not val_mask: val_mask = "1"
        
        args = argparse.Namespace(
            site=val_site,
            mask=int(val_mask)
        )
    else:
        args = parser.parse_args()
    
    site_for_ip, resolved_ip = await get_ip_address(args.site)
    
    if resolved_ip:
        sys.stdout.write(f"{Y1}Resolved IP for {args.site}: {resolved_ip}{CC}\n")
    else:
        sys.stdout.write(f"{RED}Failed to resolve IP for {args.site}. It might be 'None'.{CC}\n")
    sys.stdout.flush()

    ip = resolved_ip

    if ip and '.' in ip and all(part.isdigit() and 0 <= int(part) <= 255 for part in ip.split('.')):
        if args.mask == 1:
            mask = MASK_CHOICE_1
        elif args.mask == 2:
            mask = MASK_CHOICE_2
        await find_hostnames_in_subnet(ip, mask, MAX_CONCURRENT_REQUESTS)
    else:
        sys.stdout.write(f"{RED}Could not resolve a valid IP for site: {args.site}. Exiting.{CC}\n")
        sys.stdout.flush()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main_async())
