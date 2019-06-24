#!coding=utf-8
import string
import requests
import json
import sys
import getopt
import datetime
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

    def gettime(self):
        return "["+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')+"]"

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
        if arga["timeout"] != "":
            pdata['t'] = arga["timeout"]
        # print(self.gettime()+"[上传] "+str(pdata))
        proxies = {}
        if arga["proxy"] != "":
            proxies = {'http': arga["proxy"], 'https': arga["proxy"]}
        try:
            rdata = requests.post(purl, data=pdata, timeout=arga["timeout"], proxies=proxies, verify=arga["verify"])
            # print(self.gettime()+"[下载] "+rdata.text)
            rjson = json.loads(rdata.text)
        except Exception as e:
            print(self.gettime()+"[错误] "+host+" 解析失败: "+str(e))
            # print(rdata.text)
            return None
        if rjson[0] != "OK":
            return None
        return rjson[1]

    def handle(self,data,address):
        dns = self.parse(data)
        qname = str(dns.q.qname)
        print(self.gettime()+"[请求] 收到来自 "+str(address[0])+":"+str(address[1])+" 的 DNS 请求，正在解析 "+qname+" ...")
        rdnsarr = self.getdns(qname)
        if rdnsarr == None:
            print(self.gettime()+"[错误] "+qname+" 解析失败")
            return
        rtype = " "+rdnsarr[0]+" "
        rdns = rdnsarr[1]
        print(self.gettime()+"[成功] "+qname+" 以"+rtype+"解析到 "+rdns)
        dns = dns.reply()
        dns.add_answer(*RR.fromZone(rtype.join([qname,rdns])))
        self.socket.sendto(dns.pack(),address)

def argv():
    arga = {
        'url': '',
        'ipv': '4f',
        'dns': '',
        'bind': '0.0.0.0:53',
        'proxy': '',
        'verify': True,
        'timeout': 5
    }
    info = "NyarukoHttpDNS 版本 1.0.1\nhttps://github.com/kagurazakayashi/NyarukoHttpDNS\n有关命令行的帮助信息，请查看 README.md 。"
    try:
        opts, args = getopt.getopt(sys.argv[1:],"h:u:6b:d:p:kt:",["url=","dns=","proxy=","timeout="])
    except getopt.GetoptError:
        print("参数不正确。")
        print(info)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help", "-v", "--version"):
            print(info)
            sys.exit(0)
        elif opt in ("-u", "--url"):
            arga["url"] = arg
        elif opt in ("-6", "--ipv6"):
            arga["ipv"] = "6f"
        elif opt in ("-b", "--bind"):
            arga["bind"] = arg
        elif opt in ("-d", "--dns"):
            arga["dns"] = arg
        elif opt in ("-p", "--proxy"):
            arga["proxy"] = arg
        elif opt in ("-k", "--no-check-certificate"):
            requests.urllib3.disable_warnings()
            arga["verify"] = False
        elif opt in ("-t", "--timeout"):
            arga["timeout"] = int(arg)
    if arga["url"] == "":
        print("参数不正确。")
        print(info)
        sys.exit(2)
    print(info)
    print("远程服务: "+arga["url"])
    print("本地服务: "+arga["bind"])
    print("IP版本: "+arga["ipv"])
    if arga["dns"] != "":
        print("DNS服务器: "+arga["dns"])
    else:
        print("DNS服务器: 由服务器指定")
    if arga["proxy"] != "":
        print("连接方式: 通过代理服务器 "+arga["proxy"])
    else:
        print("连接方式: 直接连接")
    print("SSL证书验证: "+str(arga["verify"]))
    print("超时时间: "+str(arga["timeout"])+" 秒")
    print("["+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')+"][启动] 初始化 DNS 服务器。")
    return arga

if __name__ == '__main__':
    """初始化"""
    global arga
    arga = argv()
    dnss = DNSServer(arga["bind"])
    dnss.serve_forever()
