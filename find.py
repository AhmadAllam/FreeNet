# script setting
dns1 = "8.8.8.8"
dns2 = "8.8.4.4"
mask_choice_1 = (255, 255, 255, 0)
mask_choice_2 = (255, 255, 0, 0)
max_requests = 20

# Printing settings
DARK_BLUE = "\033[34m"
LIGHT_BLUE = "\033[36m"
RED = "\033[31m"
GREEN = "\033[32m"
CC = "\033[0m"

output_directory = "BugHosts"
output_file = "All_Hosts.txt"
ip_output_file = "All_IP.txt"

# -------------------------------------------------------------------

import socket
import asyncio
import signal
import sys
import argparse
import os

def signal_handler(sig, frame):
    print(f'\n{RED}Goodbye!{CC}')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def set_dns():
    with open('/etc/resolv.conf', 'w') as file:
        file.write(f"nameserver {dns1}\n")
        file.write(f"nameserver {dns2}\n")

async def get_hostname(addr):
    try:
        hostname = await asyncio.to_thread(socket.gethostbyaddr, addr)
        return hostname[0]
    except (socket.herror, socket.gaierror):
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

async def fetch_hostnames(subnet, max_requests):
    semaphore = asyncio.Semaphore(max_requests)

    async def sem_get_hostname(addr):
        async with semaphore:
            return await get_hostname(addr)

    tasks = [sem_get_hostname(f"{subnet}{i}") for i in range(256)]
    return await asyncio.gather(*tasks)

def get_ip_address(site):
    try:
        ip = socket.gethostbyname(site)
        print(f"{site} IP address: {ip}")
        return ip
    except socket.gaierror:
        print(f"{site} IP address not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while getting IP address: {e}")
        return None

async def find_hostnames_in_subnet(ip, mask, max_requests):
    if ip is None:
        return

    prefix = ip.rfind(".")
    subnet = ip[:prefix + 1]

    print(f"{'-' * 55}")
    print(f"{DARK_BLUE}{'Host IP':<20} {LIGHT_BLUE}{'Hostname':<20}{CC}")
    print(f"{'-' * 55}")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_path = os.path.join(output_directory, output_file)
    ip_output_path = os.path.join(output_directory, ip_output_file)

    discovered_hostnames = []

    try:
        with open(output_path, "a+") as f:
            f.seek(0)
            existing_hostnames = f.read().splitlines()

            if mask == mask_choice_1:
                for i in range(256):
                    addr = f"{subnet}{i}"
                    hostname = await get_hostname(addr)
                    if hostname:
                        if hostname not in existing_hostnames:
                            print(f"{DARK_BLUE}{addr:<20} {LIGHT_BLUE}{hostname:<20}{CC}")
                            f.write(hostname + "\n")
                            discovered_hostnames.append(hostname)
                            existing_hostnames.append(hostname)
                        else:
                            print(f"{DARK_BLUE}{addr:<20} {LIGHT_BLUE}{'Duplicate hostname':<20}{CC}")
                    else:
                        print(f"{DARK_BLUE}{addr:<20} {LIGHT_BLUE}{'No hostname':<20}{CC}")

            elif mask == mask_choice_2:
                first_two_octets = '.'.join(ip.split('.')[:2]) + '.'
                for second_octet in range(256):
                    for i in range(256):
                        full_addr = f"{first_two_octets}{second_octet}.{i}"
                        hostname = await get_hostname(full_addr)
                        if hostname:
                            if hostname not in existing_hostnames:
                                print(f"{DARK_BLUE}{full_addr:<20} {LIGHT_BLUE}{hostname:<20}{CC}")
                                f.write(hostname + "\n")
                                discovered_hostnames.append(hostname)
                                existing_hostnames.append(hostname)
                            else:
                                print(f"{DARK_BLUE}{full_addr:<20} {LIGHT_BLUE}{'Duplicate hostname':<20}{CC}")
                        else:
                            print(f"{DARK_BLUE}{full_addr:<20} {LIGHT_BLUE}{'No hostname':<20}{CC}")

    except Exception as e:
        print(f"An unexpected error occurred while fetching hostnames: {e}")

    print(f"{GREEN}Finished in mask: {mask}{CC}") 

    print()
    print()

    # Convert discovered hostnames to IP addresses and save to All_IP.txt
    print(f"{GREEN}converting hostnames to IP addresses...{CC}")  

    try:
        with open(ip_output_path, "w") as ip_file:
            for hostname in discovered_hostnames:
                try:
                    ip_address = socket.gethostbyname(hostname)
                    ip_file.write(ip_address + "\n")
                except socket.gaierror:
                    ip_file.write(f'no ip "{hostname}"\n')
                    print(f"Could not resolve IP for hostname: {hostname}")
    except Exception as e:
        print(f"An unexpected error occurred while saving IP addresses: {e}")

    print(f"{GREEN}Successfully completed!{CC}")  
    sys.exit(0)

def main():
    print("\033[H\033[J", end="")
    set_dns()
    parser = argparse.ArgumentParser(description="Find hostnames in a subnet.")
    parser.add_argument("site", help="The site to get IP address from.")
    parser.add_argument("mask", type=int, nargs='?', default=1, choices=[1, 2], help="The subnet mask choice (1 or 2).")

    args = parser.parse_args()

    ip = get_ip_address(args.site)

    if args.mask == 1:
        mask = mask_choice_1
    elif args.mask == 2:
        mask = mask_choice_2

    if ip:
        asyncio.run(find_hostnames_in_subnet(ip, mask, max_requests))

if __name__ == "__main__":
    main()