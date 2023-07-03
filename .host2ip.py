import socket
print(" started be patient ")	
print("                            ")	
reader=open("host.txt","r")
out=open("ip.txt","w")
for host in reader.read().split('\n'):
	try:
		ip=socket.gethostbyname(host)
	except:
		ip="N/A"
	out.write(ip)
	out.write("\n")
out.close()
reader.close()
print("                                ")	
print("***great now open ip file ***")
print("MyTelegram")
print("@echo_Allam")