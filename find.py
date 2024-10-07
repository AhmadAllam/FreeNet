import socket
import asyncio
import signal
import sys
import argparse

DARK_BLUE = "\033[34m"
LIGHT_BLUE = "\033[36m"
RED = "\033[31m"
CC = "\033[0m"

dns1 = "8.8.8.8"
dns2 = "8.8.4.4"

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
    filename = "host.txt"

    print(f"{'-' * 55}")
    print(f"{DARK_BLUE}{'Host IP':<20} {LIGHT_BLUE}{'Hostname':<20}{CC}")
    print(f"{'-' * 55}")

    try:
        if mask == (255, 255, 255, 0): 
            for i in range(256):
                addr = f"{subnet}{i}"
                hostname = await get_hostname(addr)
                with open(filename, "a") as f:
                    if hostname:
                        print(f"{DARK_BLUE}{addr:<20} {LIGHT_BLUE}{hostname:<20}{CC}")
                        f.write(hostname + "\n")
                    else:
                        print(f"{DARK_BLUE}{addr:<20} {LIGHT_BLUE}{'No hostname':<20}{CC}")

        elif mask == (255, 255, 0, 0): 
            first_two_octets = '.'.join(ip.split('.')[:2]) + '.'
            for second_octet in range(256):
                for i in range(256):
                    full_addr = f"{first_two_octets}{second_octet}.{i}"
                    hostname = await get_hostname(full_addr)
                    with open(filename, "a") as f:
                        if hostname:
                            print(f"{DARK_BLUE}{full_addr:<20} {LIGHT_BLUE}{hostname:<20}{CC}")
                            f.write(hostname + "\n")
                        else:
                            print(f"{DARK_BLUE}{full_addr:<20} {LIGHT_BLUE}{'No hostname':<20}{CC}")

    except Exception as e:
        print(f"An unexpected error occurred while fetching hostnames: {e}")

    print(f"{RED}Finished searching in subnet with mask: {mask}{CC}")
    print("Finished")
    sys.exit(0)

def main():
    set_dns()
    parser = argparse.ArgumentParser(description="Find hostnames in a subnet.")
    parser.add_argument("site", help="The site to get IP address from.")
    parser.add_argument("mask", type=int, nargs='?', default=1, choices=[1, 2], help="The subnet mask choice (1 or 2).")
    parser.add_argument("--threads", type=int, default=20, help="Maximum number of concurrent requests.")
    
    args = parser.parse_args()

    ip = get_ip_address(args.site)
    
    if args.mask == 1:
        mask = (255, 255, 255, 0)  
    elif args.mask == 2:
        mask = (255, 255, 0, 0)

    if ip:
        asyncio.run(find_hostnames_in_subnet(ip, mask, args.threads))

if __name__ == "__main__":
    main()