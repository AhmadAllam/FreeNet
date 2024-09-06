Here's a formatted version of your README file:

---

# Free-internet

Find bughosts for HTTP Custom / HA Tunnel.

## Description

This is a simple script to find bughosts in ISPs to get free internet using SSH VPN applications like HTTP Custom, HTTP Injector, HA Tunnel Plus, and TLS Tunnel.

## Getting Started

### Dependencies

* Termux or Kali Nethunter
* Internet connection for installation only

### Installing & Executing

1. Navigate to the FreeNet directory:
   ```bash
   cd /FreeNet
   ```

2. Make all scripts executable:
   ```bash
   chmod +x *
   ```

3. Install the required Python package:
   ```bash
   pip install requests
   ```

4. Now follow the instructions below.

## Help

This tool is made with love for

```
#unlimited_internet_in_egypt
```

### Find

* This tool helps to find bughosts using a domain or IP.
* When typing `www.google.com`, the tool will search for all addresses containing the hostname within the scope of this IP. 
* This tool searches in IP ranges like `192.168.xxx.xxx` or `192.168.1.xxx`.

#### How to use?

- To find a bughost:
  ```bash
  python find.py www.vodafone.com 0
  ```
  - `www.vodafone.com` is the name of the bughost.
  - `0` at the end indicates the search depth.
  - If you want a more in-depth search, write `1` or `2` instead of `0`.
  - To specify the number of threads and increase the number of operations, use:
    ```bash
    python find.py www.vodafone.com 0 --threads 20
    ```
  - The default value is 10 threads.

### Scan

* This tool will scan hosts from the `host.txt` file.

#### Available Options:
- **-d, --deep**: Specify the subdomain depth (number of sub-levels). The default value is 2.
- **-m, --mode**: Specify the scan mode. Available options are:
  - `direct`: Direct scan without a proxy.
  - `proxy`: Use a proxy for the scan.
  - `ssl`: Scan using SSL protocol.
- **-o, --output**: Specify the output filename where scan results will be saved.
- **-p, --port**: Specify the target port (default value is 80).
- **-t, --threads**: Specify the number of threads to use. The default value is 8.
- **-I, --ignore-redirect-location**: Specify a redirect location to ignore when using proxy mode.
- **-M, --method**: Specify the HTTP method to use (like GET or POST; default is HEAD).
- **-P, --proxy**: Specify the proxy address to be used (like `proxy.example.com:8080`). This option is required in proxy mode.

#### Example Usage:
- To run the script with a direct scan:
  ```bash
  python scan.py -m direct -o results.json -p 80
  ```
- To run it using a proxy:
  ```bash
  python scan.py -m proxy -p 8080 -P proxy.example.com:8080
  ```

### Host to IP

* This tool will convert hostnames in `host.txt` to IPs. 
* The result will be saved in the `ip.txt` file.
* If you want to scan an IP, just copy it from the `ip.txt` file to `host.txt` and run the scan tool.

#### Example Usage:
```bash
python host2ip.py
```

## Authors

* Dev. AhmadAllam
  * My account: [Telegram](https://t.me/echo_Allam)
  * Don't forget Palestine ❤️