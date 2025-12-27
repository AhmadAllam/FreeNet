# BugHosts Finder

## Overview

**BugHosts Finder** is a collection of Python scripts designed to help you find "bughosts" within Internet Service Providers. These bughosts can potentially be used to access free internet via SSH VPN apps like **HTTP Custom**, **HTTP Injector**, **HA Tunnel Plus**, and **TLS Tunnel**.

---

## Quick Start

```bash
git clone https://github.com/AhmadAllam/FreeNet.git
cd FreeNet
chmod +x *
```

---

## Requirements

```bash
apt update && apt upgrade -y
apt install python3 python3-pip
pip install asyncio-throttle aiohttp aiofiles
```

---

## Scripts & Usage

### 1. `mode_find.py`: Find Hosts in IP Ranges

- **Help and options:**
   ```bash
   python mode_find.py -h
   ```
- **Scan a /24 subnet (254 possible IP addresses):**
   ```bash
   python mode_find.py -s vodafone.com -m 1
   ```
- **Scan a /16 subnet (65,536 possible IP addresses):**
   ```bash
   python mode_find.py -s vodafone.com -m 2
   ```

**Output:**
- Discovered hostnames: `BugHosts/All_Hosts.txt`
- Corresponding IP addresses: `BugHosts/All_IP.txt`

---

### 2. `mode_direct.py`: Scan Hosts for Open Ports and Services

- **Help and options:**
   ```bash
   python mode_direct.py -h
   ```
- **Scan with default settings (uses `BugHosts/All_Hosts.txt` and ports 80, 443):**
   ```bash
   python mode_direct.py
   ```
- **Scan a specific file and port:**
   ```bash
   python mode_direct.py -f my_hosts.txt -p 80
   ```
- **Scan multiple ports concurrently:**
   ```bash
   python mode_direct.py -p 80,443,8080
   ```
- **Scan using a proxy:**
   ```bash
   python mode_direct.py -P proxy.example.com:8080 -p 80
   ```

**Output:**
- "Cloud Hosts" (based on server headers/heuristics): `BugHosts/cloud_hosts.txt`
- "Other Hosts": `BugHosts/other_hosts.txt`

---

### 3. `mode_payload.py`: Test Hosts with Custom HTTP Payloads

- **Help and options:**
   ```bash
   python mode_payload.py -h
   ```
- **Run with default settings (uses `BugHosts/All_Hosts.txt` as input, `payloads.txt` for payloads, and `http://www.google.com/generate_204` as the target URL):**
   ```bash
   python mode_payload.py
   ```
- **Specify a custom input file and payloads file:**
   ```bash
   python mode_payload.py -f my_custom_hosts.txt --payloads-file my_custom_payloads.txt
   ```

**Output:**
- Discovered bug hosts: `BugHosts/payload_bugs.txt`

---

### 4. `mode_proxy.py`: Hunt for Open Proxies

- **Help and options:**
   ```bash
   python mode_proxy.py -h
   ```
- **Run with default settings (uses `BugHosts/All_Hosts.txt` and a list of common proxy ports like 80, 8080, 3128, etc.):**
   ```bash
   python mode_proxy.py
   ```
- **Specify custom ports to scan for proxies (e.g., only ports 80 and 8080):**
   ```bash
   python mode_proxy.py -p 80,8080
   ```
- **Use a specific input file for hostnames/IPs:**
   ```bash
   python mode_proxy.py -f my_ip_list.txt
   ```

**Output:**
- Discovered open proxies: `BugHosts/open_proxies.txt`

---

## Important Notes

- This tool is provided for educational and research purposes only. Use it responsibly and ethically.
- Built with ❤️ for:  
  ```
  #unlimited_internet_in_egypt
  ```

---

## Author

- **Dev. AhmadAllam**
   - Telegram: [@echo_tester](https://t.me/echo_tester)
    - Don't forget Palestine ❤️
