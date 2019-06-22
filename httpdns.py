#!coding=utf-8
import string
import requests
import json
import sys
import getopt
# pip3 install dnslib
# pip3 install gevent
# pip3 install requests
from dnslib import DNSRecord,RR,DNSLabel

from gevent import socket
from gevent.server import DatagramServer,StreamServer

class DNSServer(DatagramServer):
    """UDP-DNS服务器"""
    
    def parse(self,data):
        """解析数据"""
        try:
            dns = DNSRecord.parse(data)
        except Exception as e:
            print(e)
        return dns

    def getdns(self,host):
        """从服务器查询"""
        global arga
        purl = arga["url"]
        pdata = {
            'h': host,
            'i': arga["ipv"],
            'q': '3'
        }
        if arga["dns"] != "":
            pdata['d'] = arga["dns"]
        try:
            rdata = requests.post(purl, data=pdata, timeout=5)
            rjson = json.loads(rdata.text)
        except Exception as e:
            print("[错误] "+host+" 解析失败: "+str(e))
            # print(rdata.text)
            return None
        if rjson[0] != "OK":
            return None
        return rjson[1]

    def handle(self,data,address):
        dns = self.parse(data)
        # print("收到DNS请求 %s,query:%s" % str(address),str(dns))
        qname = str(dns.q.qname)
        print("[请求] 收到来自 "+str(address[0])+":"+str(address[1])+" 的 DNS 请求，正在解析 "+qname+" ...")
        rdnsarr = self.getdns(qname)
        if rdnsarr == None:
            print("[错误] "+qname+" 解析失败")
            return
        rtype = " "+rdnsarr[0]+" "
        rdns = rdnsarr[1]
        print("[成功] "+qname+" 以"+rtype+"解析到 "+rdns)
        dns = dns.reply()
        dns.add_answer(*RR.fromZone(rtype.join([qname,rdns])))
        self.socket.sendto(dns.pack(),address)

def argv():
    arga = {
        'url': '',
        'ipv': '4f',
        'dns': '',
        'bind': '0.0.0.0:53'
    }
    try:
        opts, args = getopt.getopt(sys.argv[1:],"u:6b:d:",["url=","dns="])
    except getopt.GetoptError:
        print("参数不正确，请查看 README.md")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-u", "--url"):
            arga["url"] = arg
        elif opt in ("-6", "--ipv6"):
            arga["ipv"] = "6f"
        elif opt in ("-b", "--bind"):
            arga["bind"] = arg
        elif opt in ("-d", "--dns"):
            arga["dns"] = arg
    return arga

if __name__ == '__main__':
    """初始化"""
    global arga
    arga = argv()
    dnss = DNSServer(arga["bind"])
    dnss.serve_forever()
