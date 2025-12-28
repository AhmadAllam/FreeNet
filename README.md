# FreeNet - BugHost Finder & Toolset

**FreeNet** is a powerful, all-in-one Python toolset designed to help you discover, scan, and test "bughosts" within Internet Service Providers. These hosts are often used for exploring free internet possibilities via SSH/VPN tunneling apps.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg) ![License](https://img.shields.io/badge/License-Open%20Source-green.svg)

---

## 🚀 Features & Detailed Explanations

Here is a simple explanation of every tool and the terms you might see while using them:

### 1. 🔍 Host Finder
*   **What it does:** Searches for subdomains (hosts) related to a specific website.
*   **When to use:** Start here! If you have a site like `example.com`, use this to find all its hidden subdomains (e.g., `api.example.com`, `cdn.example.com`).
*   **Common Inputs:**
    *   **Target Site:** The main domain you want to scan (e.g., `vodafone.com.eg`).
    *   **Subnet Mask:** Defines how many IP addresses to scan around the target.
        *   `1` (/24): Scans about 254 IPs (Fast).
        *   `2` (/16): Scans about 65,000 IPs (Slower, but finds much more).

### 2. ⚡ Direct Scanner
*   **What it does:** Checks if the hosts you found are alive and accepting connections.
*   **When to use:** Use this after the "Host Finder" to filter out dead or unreachable hosts.
*   **Common Inputs:**
    *   **Input File:** The text file containing the list of hosts (defaults to `BugHosts/All_Hosts.txt`).
    *   **Ports:** The "doors" to try and enter. Common web ports are `80` (HTTP) and `443` (HTTPS).
    *   **Threads:** Speed of the scan. Higher number = faster scan (but takes more CPU). Default is `100`.
    *   **HTTP Method:** The command sent to the server. `HEAD` is fast and light; `GET` retrieves the full page.

### 3. 🔒 SSL Scanner
*   **What it does:** Checks if a host supports SSL/TLS (encrypted connection) via SNI (Server Name Indication).
*   **When to use:** Essential for finding hosts that work with **SSL/TLS Tunneling** apps (like HA Tunnel Plus).
*   **Common Inputs:**
    *   **Subdomain Depth (Deep):** How "deep" to look in the domain name for the SNI.
        *   Example: For `a.b.example.com`, a depth of `2` extracts `example.com`. A depth of `3` extracts `b.example.com`.

### 4. 🌐 Proxy Scanner
*   **What it does:** Looks for open proxies (servers that route your traffic).
*   **When to use:** If you need a working proxy IP and Port for your VPN settings.
*   **Common Inputs:**
    *   **Target URL:** A test site to verify if the proxy actually works (e.g., `http://google.com`).
    *   **Proxy Ports:** The specific ports to check for proxies (e.g., `8080`, `3128`, `80`).

### 5. 💉 Payload Tester
*   **What it does:** The advanced mode. It throws custom "Payloads" (special text strings) at the hosts to see if they bypass restrictions.
*   **When to use:** If you have a `payloads.txt` file and want to test which host reacts to which payload.
*   **Common Inputs:**
    *   **Payloads File:** A text file containing the payloads you want to injection test.

---

## 🛠️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/AhmadAllam/FreeNet.git
    cd FreeNet
    ```

2.  **Install dependencies:**
    ```bash
    pip install aiohttp aiofiles asyncio-throttle
    ```

---

## 📖 How to Use

### The Interactive Menu (Recommended)
1.  Run the main script:
    ```bash
    python main.py
    ```
2.  You will see the menu:
    ```text
    ==========================================
           FreeNet Main Menu by AhmadOo       
    ==========================================
    [1] Host Finder
    [2] Direct Scanner
    [3] SSL Scanner
    [4] Proxy Scanner
    [5] Payload Tester
    [6] Exit
    ```
3.  Type the number of the tool you want.
4.  Answer the questions (or just press **Enter** to use the smart defaults!).

---

## 👤 Author

*   **Dev. AhmadAllam**
*   Telegram: [@echo_tester](https://t.me/echo_tester)
*   **#unlimited_internet_in_egypt**
*   *Don't forget Palestine ❤️*
