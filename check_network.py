import socket
import asyncio
import time
import argparse
from concurrent.futures import ThreadPoolExecutor

dns_server = "62.240.110.198"
default_test_domain = "vodafone.com.eg"
default_max_requests = 50
default_max_workers_24 = 50
default_max_workers_16 = 50
default_timeout_seconds = 2
default_max_subnets_batch = 200
test_max_requests = [50, 100, 200]
test_max_workers_24 = [50, 100, 200]
test_max_workers_16 = [50, 100, 200]
test_timeout_seconds = [1, 2, 3]
test_max_subnets_batch = [50, 100, 200]
DARK_BLUE = "\033[34m"
LIGHT_BLUE = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
CC = "\033[0m"

class RateLimiter:
    def __init__(self, rate_per_second):
        self.interval = 1.0 / rate_per_second if rate_per_second > 0 else 0
        self.last_call = 0

    async def acquire(self):
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.interval:
            await asyncio.sleep(self.interval - elapsed)
        self.last_call = time.time()

async def resolve_hostname(addr, timeout, rate_limiter):
    await rate_limiter.acquire()
    try:
        socket.setdefaulttimeout(timeout)
        hostname = await asyncio.to_thread(socket.gethostbyname, addr)
        return hostname
    except (socket.gaierror, socket.timeout):
        return None
    except Exception as e:
        return None

async def test_parameter(param, value, test_domain, timeout=default_timeout_seconds, max_requests=default_max_requests, max_workers_24=default_max_workers_24, max_workers_16=default_max_workers_16, max_subnets_batch=default_max_subnets_batch, verbose=True):
    start_time = time.time()
    success = 0
    failed = 0
    rate_limiter = RateLimiter(50)
    
    try:
        if param == "max_requests" or param == "combined":
            tasks = [resolve_hostname(test_domain, timeout, rate_limiter) for _ in range(int(value))]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success = sum(1 for r in results if r is not None and isinstance(r, str))
            failed = int(value) - success
        elif param == "max_workers_24":
            with ThreadPoolExecutor(max_workers=int(value)) as executor:
                futures = [executor.submit(lambda: asyncio.run(resolve_hostname(test_domain, timeout, rate_limiter))) for _ in range(256)]
                results = [f.result() for f in futures]
                success = sum(1 for r in results if r is not None and isinstance(r, str))
                failed = 256 - success
        elif param == "max_workers_16":
            with ThreadPoolExecutor(max_workers=int(value)) as executor:
                futures = [executor.submit(lambda: asyncio.run(resolve_hostname(test_domain, timeout, rate_limiter))) for _ in range(256)]
                results = [f.result() for f in futures]
                success = sum(1 for r in results if r is not None and isinstance(r, str))
                failed = 256 - success
        elif param == "timeout_seconds":
            tasks = [resolve_hostname(test_domain, value, rate_limiter) for _ in range(max_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success = sum(1 for r in results if r is not None and isinstance(r, str))
            failed = max_requests - success
        elif param == "max_subnets_batch":
            tasks = [resolve_hostname(test_domain, timeout, rate_limiter) for _ in range(int(value))]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success = sum(1 for r in results if r is not None and isinstance(r, str))
            failed = int(value) - success
    except Exception as e:
        success = 0
        failed = int(value) if param in ["max_requests", "max_subnets_batch", "combined"] else 256
    
    elapsed_time = time.time() - start_time
    success_rate = (success / (success + failed) * 100) if (success + failed) > 0 else 0
    
    if verbose:
        print(f"{DARK_BLUE}Test with {param} = {value}:{CC}")
        print(f"  {LIGHT_BLUE}Success: {success:<10}{CC}")
        print(f"  {LIGHT_BLUE}Failed: {failed:<10}{CC}")
        print(f"  {LIGHT_BLUE}Time taken: {elapsed_time:.2f} seconds{CC}")
        print(f"{'-' * 50}")
    
    return success, elapsed_time, success_rate

async def test_combined_values(test_domain, max_requests, max_workers_24, max_workers_16, timeout_seconds, max_subnets_batch, attempt, max_attempts):
    success, elapsed_time, success_rate = await test_parameter(
        "combined", max_requests, test_domain, timeout_seconds, max_requests, max_workers_24, max_workers_16, max_subnets_batch, verbose=False
    )
    
    return success, elapsed_time, success_rate

async def main():
    parser = argparse.ArgumentParser(description="Test DNS parameter values.")
    parser.add_argument("--test-parameter", choices=["max_requests", "max_workers_24", "max_workers_16", "timeout_seconds", "max_subnets_batch"])
    parser.add_argument("--test-values", nargs="+", type=float)
    parser.add_argument("--test-domain", default=default_test_domain)
    
    args = parser.parse_args()
    
    test_domain = args.test_domain
    suggested_values = {
        "max_requests": default_max_requests,
        "max_workers_24": default_max_workers_24,
        "max_workers_16": default_max_workers_16,
        "timeout_seconds": default_timeout_seconds,
        "max_subnets_batch": default_max_subnets_batch
    }
    
    if args.test_parameter and args.test_values:
        test_values = args.test_values
        param = args.test_parameter
        best_value = None
        best_success = 0
        best_time = float('inf')
        best_success_rate = 0
        
        for value in test_values:
            success, elapsed_time, success_rate = await test_parameter(param, value, test_domain)
            await asyncio.sleep(2)
            
            if success > best_success or (success == best_success and elapsed_time < best_time):
                best_value = value
                best_success = success
                best_time = elapsed_time
                best_success_rate = success_rate
        
        if best_value is not None:
            print(f"\n{GREEN}╔{'═' * 38}╗{CC}")
            print(f"{GREEN}║{f' Best Value for {param} ':^38}║{CC}")
            print(f"{GREEN}╠{'═' * 38}╩{'═' * 8}╗{CC}")
            print(f"{DARK_BLUE}║ Best value:      {best_value:<10} {' ':<7} ║{CC}")
            print(f"{DARK_BLUE}║ Success:         {best_success:<10} {' ':<7} ║{CC}")
            print(f"{DARK_BLUE}║ Time:            {best_time:.2f} seconds {' ':<3} ║{CC}")
            print(f"{GREEN}╠{'═' * 8}╦{'═' * 29}╩{CC}")
            print(f"{LIGHT_BLUE}║{' ':<8}╩ Test this value in your scanning script to ensure no crashes.{CC}")
            print(f"{GREEN}╚{'═' * 38}╝{CC}")
    else:
        print(f"{GREEN}Running default tests for all parameters{CC}")
        for param, test_values in [
            ("max_requests", test_max_requests),
            ("max_workers_24", test_max_workers_24),
            ("max_workers_16", test_max_workers_16),
            ("timeout_seconds", test_timeout_seconds),
            ("max_subnets_batch", test_max_subnets_batch)
        ]:
            print(f"\n{DARK_BLUE}Testing parameter: {param}{CC}")
            best_value = None
            best_success = 0
            best_time = float('inf')
            best_success_rate = 0
            
            for value in test_values:
                success, elapsed_time, success_rate = await test_parameter(param, value, test_domain)
                await asyncio.sleep(2)
                
                if success > best_success or (success == best_success and elapsed_time < best_time):
                    best_value = value
                    best_success = success
                    best_time = elapsed_time
                    best_success_rate = success_rate
            
            if best_value is not None:
                print(f"\n{GREEN}╔{'═' * 38}╗{CC}")
                print(f"{GREEN}║{f' Best Value for {param} ':^38}║{CC}")
                print(f"{GREEN}╠{'═' * 38}╩{'═' * 8}╗{CC}")
                print(f"{DARK_BLUE}║ Best value:      {best_value:<10} {' ':<7} ║{CC}")
                print(f"{DARK_BLUE}║ Success:         {best_success:<10} {' ':<7} ║{CC}")
                print(f"{DARK_BLUE}║ Time:            {best_time:.2f} seconds {' ':<3} ║{CC}")
                print(f"{GREEN}╠{'═' * 8}╦{'═' * 29}╩{CC}")
                print(f"{GREEN}╚{'═' * 38}╝{CC}")
                suggested_values[param] = best_value
        
        print(f"\n{GREEN}Starting combined tests with suggested values...{CC}")
        max_attempts = 5
        reduction_factor = 0.8
        attempt = 1
        
        while attempt <= max_attempts:
            success, elapsed_time, success_rate = await test_combined_values(
                test_domain,
                suggested_values["max_requests"],
                suggested_values["max_workers_24"],
                suggested_values["max_workers_16"],
                suggested_values["timeout_seconds"],
                suggested_values["max_subnets_batch"],
                attempt,
                max_attempts
            )
            
            if success_rate >= 80 and elapsed_time < 5:
                print(f"\n{GREEN}╔{'═' * 48}╗{CC}")
                print(f"{GREEN}║{ ' Final Recommended Values ':^48}║{CC}")
                print(f"{GREEN}╠{'═' * 48}╩{'═' * 8}╗{CC}")
                print(f"{DARK_BLUE}║ max_requests:      {suggested_values['max_requests']:<10} {' ':<17} ║{CC}")
                print(f"{DARK_BLUE}║ max_workers_24:    {suggested_values['max_workers_24']:<10} {' ':<17} ║{CC}")
                print(f"{DARK_BLUE}║ max_workers_16:    {suggested_values['max_workers_16']:<10} {' ':<17} ║{CC}")
                print(f"{DARK_BLUE}║ timeout_seconds:   {suggested_values['timeout_seconds']:<10} {' ':<17} ║{CC}")
                print(f"{DARK_BLUE}║ max_subnets_batch: {suggested_values['max_subnets_batch']:<10} {' ':<17} ║{CC}")
                print(f"{GREEN}╠{'═' * 8}╦{'═' * 39}╩{CC}")
                print(f"{LIGHT_BLUE}║{' ':<8}╩ These values are stable and fast for your network. Use them in your scanning script.{CC}")
                print(f"{GREEN}╚{'═' * 48}╝{CC}")
                break
            else:
                print(f"\n{RED}Combined test failed (Attempt {attempt}/{max_attempts}). Reducing values...{CC}")
                suggested_values["max_requests"] = max(10, int(suggested_values["max_requests"] * reduction_factor))
                suggested_values["max_workers_24"] = max(10, int(suggested_values["max_workers_24"] * reduction_factor))
                suggested_values["max_workers_16"] = max(5, int(suggested_values["max_workers_16"] * reduction_factor))
                suggested_values["timeout_seconds"] = max(1, suggested_values["timeout_seconds"] * reduction_factor)
                suggested_values["max_subnets_batch"] = max(32, int(suggested_values["max_subnets_batch"] * reduction_factor))
                print(f"{LIGHT_BLUE}New values: max_requests={suggested_values['max_requests']:<6} max_workers_24={suggested_values['max_workers_24']:<6} max_workers_16={suggested_values['max_workers_16']:<6} timeout_seconds={suggested_values['timeout_seconds']:<6} max_subnets_batch={suggested_values['max_subnets_batch']}{CC}")
                attempt += 1
            
            if attempt > max_attempts:
                print(f"\n{RED}╔{'═' * 48}╗{CC}")
                print(f"{RED}║{ ' Failed to Find Stable Values ':^48}║{CC}")
                print(f"{RED}╠{'═' * 48}╩{'═' * 8}╗{CC}")
                print(f"{DARK_BLUE}║ max_requests:      {suggested_values['max_requests']:<10} {' ':<17} ║{CC}")
                print(f"{DARK_BLUE}║ max_workers_24:    {suggested_values['max_workers_24']:<10} {' ':<17} ║{CC}")
                print(f"{DARK_BLUE}║ max_workers_16:    {suggested_values['max_workers_16']:<10} {' ':<17} ║{CC}")
                print(f"{DARK_BLUE}║ timeout_seconds:   {suggested_values['timeout_seconds']:<10} {' ':<17} ║{CC}")
                print(f"{DARK_BLUE}║ max_subnets_batch: {suggested_values['max_subnets_batch']:<10} {' ':<17} ║{CC}")
                print(f"{RED}╠{'═' * 8}╦{'═' * 39}╩{CC}")
                print(f"{LIGHT_BLUE}║{' ':<8}╩ Try these values manually or use individual suggested values from earlier tests.{CC}")
                print(f"{RED}╚{'═' * 48}╝{CC}")

if __name__ == "__main__":
    asyncio.run(main())