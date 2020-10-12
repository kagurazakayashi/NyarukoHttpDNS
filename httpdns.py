#!coding=utf-8
import string
import requests
import json
import sys
import getopt
import datetime
import platform
# pip3 install dnslib
# pip3 install gevent
# python3 -m pip install requests
from dnslib import DNSRecord, RR, DNSLabel
from gevent import socket
from gevent.server import DatagramServer, StreamServer


class DNSServer(DatagramServer):
    """UDP-DNS服务器"""

    def parse(self, data):
        """解析数据"""
        try:
            dns = DNSRecord.parse(data)
        except Exception as e:
            printRed(e)
        return dns

    def gettime(self):
        return "["+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')+"]"

    def getdns(self, host):
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
            rdata = requests.post(
                purl, data=pdata, timeout=arga["timeout"], proxies=proxies, verify=arga["verify"])
            # print(self.gettime()+"[下载] "+rdata.text)
            rjson = json.loads(rdata.text)
        except Exception as e:
            printRed(self.gettime()+"[错误] "+host)
            printRed(self.gettime()+"[错误] "+str(e))
            # print(rdata.text)
            return None
        if rjson[0] != "OK":
            return None
        return rjson[1]

    def handle(self, data, address):
        dns = self.parse(data)
        qname = str(dns.q.qname)
        print(self.gettime()+"[请求] "+str(address[0]) + ":"+str(address[1]))
        print(self.gettime()+"[解析] "+qname)
        rdnsarr = self.getdns(qname)
        if rdnsarr == None:
            printRed(self.gettime()+"[错误] "+qname)
            return
        rtype = " "+rdnsarr[0]+" "
        rdns = rdnsarr[1]
        printGreen(self.gettime()+"[成功] "+qname)
        printGreen(self.gettime()+"[结果] "+rtype+" : "+rdns)
        dns = dns.reply()
        dns.add_answer(*RR.fromZone(rtype.join([qname, rdns])))
        self.socket.sendto(dns.pack(), address)


def argv():
    arga = {
        'url': '',
        'ipv': '4f',
        'dns': '',
        'bind': '0.0.0.0:53',
        'proxy': '',
        'verify': True,
        'timeout': 5,
        'color': True
    }
    info = "NyarukoHttpDNS 版本 1.1.0\nhttps://github.com/kagurazakayashi/NyarukoHttpDNS\n有关命令行的帮助信息，请查看 README.md 。"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:u:6b:d:p:kt:", [
                                   "url=", "dns=", "proxy=", "timeout="])
    except getopt.GetoptError:
        printRed("参数不正确。")
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
        elif opt in ("-m", "--mono"):
            arga["color"] = False
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
    return arga


if 'Windows' in platform.system():
    import sys
    import ctypes
    __stdInputHandle = -10
    __stdOutputHandle = -11
    __stdErrorHandle = -12
    __foreGroundBLUE = 0x09
    __foreGroundGREEN = 0x0a
    __foreGroundRED = 0x0c
    __foreGroundYELLOW = 0x0e
    stdOutHandle = ctypes.windll.kernel32.GetStdHandle(__stdOutputHandle)

    def setCmdColor(color, handle=stdOutHandle):
        if arga["color"]:
            return ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)

    def resetCmdColor():
        if arga["color"]:
            setCmdColor(__foreGroundRED | __foreGroundGREEN | __foreGroundBLUE)

    def printBlue(msg):
        setCmdColor(__foreGroundBLUE)
        sys.stdout.write(msg + '\n')
        resetCmdColor()

    def printGreen(msg):
        setCmdColor(__foreGroundGREEN)
        sys.stdout.write(msg + '\n')
        resetCmdColor()

    def printRed(msg):
        setCmdColor(__foreGroundRED)
        sys.stdout.write(msg + '\n')
        resetCmdColor()

    def printYellow(msg):
        setCmdColor(__foreGroundYELLOW)
        sys.stdout.write(msg + '\n')
        resetCmdColor()
else:
    STYLE = {
        'fore': {
            'red': 31,
            'green': 32,
            'yellow': 33,
            'blue': 34,
        }
    }

    def UseStyle(msg, mode='', fore='', back='40'):
        if arga["color"]:
            fore = '%s' % STYLE['fore'][fore] if (
                fore in STYLE['fore']) else ''
            style = ';'.join([s for s in [mode, fore, back] if s])
            style = '\033[%sm' % style if style else ''
            end = '\033[%sm' % 0 if style else ''
            return '%s%s%s' % (style, msg, end)
        else:
            return msg

    def printRed(msg):
        print(UseStyle(msg, fore='red'))

    def printGreen(msg):
        print(UseStyle(msg, fore='green'))

    def printYellow(msg):
        print(UseStyle(msg, fore='yellow'))

    def printBlue(msg):
        print(UseStyle(msg, fore='blue'))

if __name__ == '__main__':
    """初始化"""
    global arga
    arga = argv()
    dnss = DNSServer(arga["bind"])
    printGreen(
        "["+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')+"][启动] 初始化 DNS 服务器。")
    dnss.serve_forever()
