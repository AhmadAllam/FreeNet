#!/bin/bash
clear
#colors
red="\e[31m"
green="\e[32m"
yelo="\e[1;33m"
cyn="\e[36m"
nc="\e[0m"

loopF () {
for (( i=0; i<${#text}; i++ )); do
    echo -n "${text:$i:1}"
    sleep 0.02
done
}
#function_my cat
mycat () {
echo -e "${yelo} "
cat << "caty" 
,_     _
 |\\_,-~/
 / _  _ |    ,--.
(  @  @ )   / ,-'
 \  _T_/-._( (
 /         `. \
|         _  \ |
 \ \ ,  /      |
  || |-_\__   /
 ((_/`(____,-'
_____________________
caty
}

#function_banner
banner () {
text="free internet Script by "
loopF
printf "${nc}@AhmadAllam${nc}"
}

#function_menu
menu () {
echo ""
echo ""
echo -e " [1]:${cyn}Find bughosts by domain ${nc} "
echo -e " [2]:${cyn}Find bughosts by IP ${nc} "
echo -e " [3]:${cyn}Scan extracted bughosts ${nc} "
echo -e " [4]:${cyn}Convert host.txt to ip.txt ${nc} "
echo -e " [5]:${cyn}install needed Tools ${nc} "
echo -e " [0]:${cyn}about & help ${nc} "
echo -e ""
echo ""

#choice
printf "${yelo}Select number of Tool${nc} : "
read -p "" entry



#function tools
function tools {
echo -e "${green}checking needed tools${nc} "
sleep 1
for tool in curl python python2 git
do
$tool -h &>/dev/null
done
[ $? -eq 0 ] && echo -e "${green}good all tools are installed${nc}" || echo -e "${red}error missing some tools now its installing ${nc} ..." apt -y update ; apt -y upgrade ; apt -y install curl python2 python2-minimal git pip ; pip install requests
}

#cases
case $entry in
	  1 | 01)
	  clear
      text="find bughost by domain name only"
      echo -e "${green} "
      loopF
      echo -e "${nc} "
      sleep 1
      python2 .find.py
      menu
      ;;
      
	2 | 02)
	  clear
      text="find bughost by ip to get hostname"
      echo -e "${green} "
      loopF
      echo -e "${nc} "
      sleep 1
      python3 .find2.py 2>&1 | tee tmp.txt ; cat tmp.txt | egrep -o '([0-9]{1,3}\.){3}[0-9]{1,3}' >host.txt ; rm tmp.txt
      menu
      ;;
	
	3 | 03)
	  clear
      text="scan bughost host.txt to know working SNI "
      echo -e "${green} "
      loopF
      echo -e "${nc} "
      sleep 1
      python3 .scan.py host.txt
      menu
      ;;
	
	4 | 04)
	  clear
      text="covert bughost file host.txt to ip.txt "
      echo -e "${green} "
      loopF
      echo -e "${nc} "
      sleep 1
      python3 .host2ip.py
      menu
      ;;
	
	5 | 05)
	  clear
      text="install needed tools to run script without errors :)"
      echo -e "${green} "
      loopF
      sleep 1
      echo -e "${nc} "
      tools
      menu
      ;;
	
	0 | 00)
	clear
	text="#free internet in Egypt"
      echo -e "${cyn} "
      loopF
      echo -e "${nc} "
      sleep 2
      echo " "
      grep -A 40 "this tool made by love for" README.md
      
    esac

}

#function_reset
reset_color() {
	tput sgr0   # reset attributes
	tput op     # reset color
}

#function_goodbye
goodbye () {
echo -e "${red} "
      text="thanks & goodbye."
      loopF
      echo -e "${nc} "
      reset_color
      exit
}
trap goodbye INT

##call functions
mycat
banner
menu