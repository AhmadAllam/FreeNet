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
   pip install requests asyncio
   ```

4. Now follow the instructions below.

## Help

This tool is made with love for

```
#unlimited_internet_in_egypt
```

### **Find Tool: `find.py`**

**Running Find.py Tool**: You can run the tool using the command line. The tool requires inputs for the site name and subnet mask. There are two options for the subnet mask:

   - `1`: Subnet mask 255.255.255.0
   - `2`: Subnet mask 255.255.0.0

   ### Example 1: Using Subnet Mask 255.255.255.0

   ```bash
   python find.py vodafone.com 1
   ```

   ### Example 2: Using Subnet Mask 255.255.0.0

   ```bash
   python find.py vodafone.com 2
   ```

   ### Additional Options

   You can specify the number of concurrent requests using the `--threads` option. For example, to set 10 concurrent requests:

   ```bash
   python script.py Vodafone.com 1 --threads 10
   ```

## Output

After running the program, it will search for hostnames for each IP address in the specified subnet. The results will be printed to the console and the hostnames will be written to a text file named `host.txt`.
```

### **Scan Tool: `scan.py`**

* This tool will scan hosts from the `host.txt` file.

#### How to Use?
- To run the scan with default settings:
  ```bash
  python scan.py
  ```
- For a direct scan:
  ```bash
  python scan.py -m direct -o hosts.txt -p 80
  ```
- To run it using a proxy:
  ```bash
  python scan.py -m proxy -p 8080 -P proxy.example.com:8080
  ```

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
  python scan.py -m direct -o hosts.txt -p 80
  ```
- To run it using a proxy:
  ```bash
  python scan.py -m proxy -p 8080 -P proxy.example.com:8080
  ```

### **Host to IP Tool: `host2ip.py`**

* This tool will convert hostnames in `host.txt` to IPs.

#### How to Use?
- To convert hostnames to IPs:
  ```bash
  python host2ip.py
  ```

#### Output:
- The result will be saved in the `ip.txt` file.
- If you want to scan an IP, just copy it from the `ip.txt` file to `host.txt` and run the scan tool.

#### Example Usage:
```bash
python host2ip.py
```

## Authors

* Dev. AhmadAllam
  * My account: [Telegram](https://t.me/echo_Allam)
  * Don't forget Palestine ❤️