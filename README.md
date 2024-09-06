## Free-internet

find bughost for httpcustom / hatunnel 

## Description

this is a simple scripts to find bughost in ISP to get free internet by SSH VPN applications like
 http custom - http injector - hatunnel plus - tlsTunnel 

## Getting Started

### Dependencies

* need termux or kali nethunter 
  
* internet connection for installation only

### Installing & Executing

* cd /FreeNet
* chmod +x *
* pip install requests
* Now follow the instructions below


## Help

this tool made by love for

```
 #unlimited_internet_in_egypt
```
* Find
    * it's tool to find bughost with domain or ip .
When typing www.google.com The tool will search for all addresses that contain the hostname Within the scope of this IP
This tool searches in ip 192.168.xxx.xxx or 192.168.1.xxx

    * How to use ?
-python find.py www.vodafone.com 0
-www.vodafone.com the name of my bughost
-zero at the end of the title is search depth.
-If you want the search to be more in-depth, Write 1 or 2 instead of zero
-If you want to specify the number of threads To increase the number of operations, write the following
-(python find.py www.vodafone.com 0 --threads 20)
-The default value is 10 threads
    


* Scan 
    * this tool will scan hosts from host.txt file.
**Available Options**:
   - **-d, --deep**: Specify the subdomain depth (number of sub-levels). The default value is 2.
   - **-m, --mode**: Specify the scan mode. Available options are:
     - `direct`: Direct scan without a proxy.
     - `proxy`: Use a proxy for the scan.
     - `ssl`: Scan using SSL protocol.
   - **-o, --output**: Specify the output filename where scan results will be saved.
   - **-p, --port**: Specify the target port (default value is 80).
   - **-t, --threads**: Specify the number of threads to use. The default value is 8.
   - **-I, --ignore-redirect-location**: Specify a redirect location to ignore when using the proxy mode.
   - **-M, --method**: Specify the HTTP method to use (like GET or POST; default is HEAD).
   - **-P, --proxy**: Specify the proxy address to be used (like `proxy.example.com:8080`). This option is required in proxy mode.
   
**Example Usage**:
   - To run the script with a direct scan:
     ```bash
     python scan.py -m direct -o results.json -p 80
     ```
   - To run it using a proxy:
     ```bash
     python scan.py -m proxy -p 8080 -P proxy.example.com:8080

* host2ip
    * this tool will convert hostnames in (host.txt) to ips
result will be saved in (ip.txt) file
now if you want to scan ip just copy it from
 ip.txt file >> to >> host.txt
 and run scan tool :)
 
**Example Usage**:
python host2ip.py

## Authors

* dev. AhmadAllam
    * my account. [telegram](https://t.me/echo_Allam)
    * don't forget Palestine❤️