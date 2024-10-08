# BugHosts Finder

## Description

The **BugHosts Finder** script is designed to discover "bughosts" in Internet Service Providers, enabling access to free internet using SSH VPN applications like **HTTP Custom**, **HTTP Injector**, **HA Tunnel Plus**, and **TLS Tunnel**.

---

### Requirements

- **Termux** or **Kali Nethunter**

### Installing & Executing

1. **Navigate to the FreeNet directory:**
   ```bash
   cd /FreeNet
   ```

2. **Make all scripts executable:**
   ```bash
   chmod +x *
   ```

3. **Install the required Python packages:**
   ```bash
   apt install python3-requests && pip install asyncio requests
   ```

4. **Follow the instructions below.**

---

# **Find Tool: `find.py`**

### How to Run

You can run the `find.py` tool using the command line. The tool requires inputs for the site name and subnet mask. There are two options for the subnet mask:

- **Option 1:** Subnet mask `255.255.255.0`
- **Option 2:** Subnet mask `255.255.0.0`

### Examples

- **Using Subnet Mask 255.255.255.0:**
   ```bash
   python find.py vodafone.com 1
   ```

- **Using Subnet Mask 255.255.0.0:**
   ```bash
   python find.py vodafone.com 2
   ```

### Additional Options

You can specify the number of concurrent requests using the `--threads` option. For example, to set 10 concurrent requests:
```bash
python find.py vodafone.com 1 --threads 10
```

---

## Output

After running the program:

- Hostnames for each IP address in the specified subnet will be searched.
- Results will be printed to the console.
- Hostnames will be stored in the file:
  - **Path:** `BugHosts/All_Hosts.txt`
- Discovered hostnames will be converted to IP addresses and saved in:
  - **Path:** `BugHosts/All_IP.txt`

---

# **Scan Tool: `scan.py`**

### Overview

The `scan.py` tool is used to perform comprehensive scans on hostnames to check their availability and gather information about them. The tool supports different modes of scanning, including direct requests, SSL requests, and proxy requests.

### How to Use

- **To run the scan with default settings:**
   ```bash
   python scan.py
   ```

- **For a direct scan:**
   ```bash
   python scan.py -m direct -o hosts.txt -p 80
   ```

- **To run it using a proxy:**
   ```bash
   python scan.py -m proxy -p 8080 -P proxy.example.com:8080
   ```

### Multiple Ports Support

You can specify multiple ports for concurrent scanning by separating them with commas. For example:
```bash
python scan.py -m direct -p 80,443
```

### Arguments

- `-d`, `--deep`: Specify the subdomain depth (default: 2).
- `-m`, `--mode`: Set the scan mode (options: direct, proxy, ssl; default: direct).
- `-f`, `--file`: Input file name (default: `BugHosts/All_Hosts.txt`).
- `-p`, `--ports`: Target ports (comma-separated; default: 80). You can specify multiple ports for concurrent scanning.
- `-t`, `--threads`: Number of threads to use (default: 8).
- `-I`, `--ignore-redirect-location`: Ignore redirect location for proxy mode.
- `-M`, `--method`: HTTP method to use (default: HEAD).
- `-P`, `--proxy`: Specify proxy in the format `proxy.example.com:8080`.

---

## Notes

This tool is made with love for:

```
#unlimited_internet_in_egypt
```

---

## Authors

* **Dev. AhmadAllam**
  * My account: [Telegram](https://t.me/echo_Allam)
  * Don't forget Palestine ❤️