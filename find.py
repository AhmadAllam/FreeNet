import socket
import asyncio
import signal
import sys
import argparse

RED = "\033[31m"
CC = "\033[0m"

def signal_handler(sig, frame):
    print(f'\n{RED}Goodbye!{CC}')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

async def get_hostname(addr):
    try:
        hostname = await asyncio.to_thread(socket.gethostbyaddr, addr)
        return hostname[0]
    except socket.herror:
        print(f"No hostname for {addr}")
        return None
    except socket.gaierror:
        print(f"{addr} is not a valid.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

async def fetch_hostnames(subnet, max_requests):
    semaphore = asyncio.Semaphore(max_requests)
    
    async def sem_get_hostname(addr):
        async with semaphore:
            return await get_hostname(addr)

    tasks = []
    for i in range(256):
        addr = f"{subnet}{i}"
        tasks.append(sem_get_hostname(addr))
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

async def find_hostnames_in_subnet(ip, depth, max_requests):
    if ip is None or depth < 0:
        return

    prefix = ip.rfind(".")
    subnet = ip[:prefix + 1]
    filename = "host.txt"

    try:
        hostnames = await fetch_hostnames(subnet, max_requests)

        with open(filename, "a") as f:
            for i, hostname in enumerate(hostnames):
                addr = f"{subnet}{i}"
                if hostname:
                    print(f"{hostname} ({addr})")
                    f.write(hostname + "\n")
                else:
                    print(f"{addr} no hostname")
    except Exception as e:
        print(f"An unexpected error occurred while fetching hostnames: {e}")

    if depth > 0:
        for i in range(0, 256):
            subnet_branch = f"{subnet}{i}"
            await find_hostnames_in_subnet(subnet_branch, depth - 1, max_requests)

def main():
    parser = argparse.ArgumentParser(description="Find hostnames in a subnet.")
    parser.add_argument("site", help="The site to get IP address from.")
    parser.add_argument("depth", type=int, help="The depth for subnet search.")
    parser.add_argument("--threads", type=int, default=10, help="Maximum number of concurrent requests.")
    
    args = parser.parse_args()

    ip = get_ip_address(args.site)
    if ip:
        asyncio.run(find_hostnames_in_subnet(ip, args.depth, args.threads))

if __name__ == "__main__":
    main()
