virtualenv -p /usr/bin/python2 venv
sudo setcap 'CAP_NET_RAW+eip' venv/bin/python2
sudo setcap 'CAP_NET_RAW+eip' `which tcpdump`
source venv/bin/activate
pip install scapy==2.3.1