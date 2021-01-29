#!coding=utf-8
import string
import json
import sys
import os
import getopt
import datetime
import platform
import threading
import socket
# python3 -m pip install requests
import requests
# pip3 install dnslib
from dnslib import DNSRecord, RR, DNSLabel
# pip3 install gevent
from gevent import socket
from gevent.server import DatagramServer, StreamServer
from fnmatch import fnmatch, fnmatchcase


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
        return "["+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"]"

    def getdns(self, host, dnsi=0):
        """从服务器查询"""
        global arga
        purl = arga["url"]
        pdata = {
            'h': host,
            'i': arga["ipv"],
            'q': '3'
        }
        if len(arga["dns"]) > 0:
            pdata['d'] = arga["dns"][dnsi]
        if arga["timeout"] != "":
            pdata['t'] = arga["timeout"]
        # print(self.gettime()+"[上传] "+str(pdata))
        proxies = {}
        if arga["proxy"] != "":
            proxies = {
                'http': arga["proxy"],
                'https': arga["proxy"]
            }
        ua = {}
        if arga["ua"] != "":
            ua = {'User-Agent': arga["ua"]}
        try:
            rdata = requests.post(
                purl,
                data=pdata,
                timeout=arga["timeout"],
                proxies=proxies,
                verify=arga["verify"],
                headers=ua
            )
            # print(self.gettime()+"[下载] "+rdata.text)
            rjson = json.loads(rdata.text)
        except Exception as e:
            # printRed(self.gettime()+"[错误] "+host)
            printRed(self.gettime()+"[错误] "+str(e))
            dnsi += 1
            if dnsi < len(arga["dns"]):
                return dnsi
            return None
        if rjson[0] == "TE":
            return "OK"
        elif rjson[0] != "OK":
            dnsi += 1
            if dnsi < len(arga["dns"]):
                return dnsi
            return None
        return rjson[1]

    def handle(self, data, address):
        global arga
        if arga["thread"]:
            totali[4] += 1
            nt = threading.Thread(target=self.dnsThread, args=(data, address))
            nt.start()
        else:
            self.dnsThread(data, address)

    def dnsThread(self, data, address):
        global totali
        global arga
        global cache
        global hosts
        hk = hosts.keys()
        hkl = len(hosts.keys())
        ca = cache.keys()
        cal = len(cache.keys())
        totali[3] = "I" + str(totali[0]) + "/E" + str(totali[1]) + "/A" + str(
            totali[0]+totali[1]) + "/C" + str(totali[2]) + "/M" + str(cal) + "/F" + str(hkl) + "/T" + str(len(threading.enumerate()))
        print(self.gettime() + "[请求] " + totali[3] +
              " | " + str(address[0]) + ":" + str(address[1]))
        dns = self.parse(data)
        qname = str(dns.q.qname)
        rtype = ""
        rdns = ""
        isLocFile = ""
        if hkl > 0:
            for nhk in hk:
                if fnmatch(qname, nhk) == True:
                    isLocFile = nhk
                    break
        if len(isLocFile) > 0:
            rtype = " A "
            rdns = hosts[isLocFile]
            print(self.gettime()+"[解析] "+qname+" -> FILE")
            printYellow(self.gettime() + "[本地] "+isLocFile+" -> FILE")
            totali[1] += 1
            totali[2] += 1
        elif arga["cache"] > 0 and qname in ca:
            print(self.gettime()+"[解析] "+qname+" -> CACHE")
            rdnsarr = cache[qname]
            if type(rdnsarr) != list:
                printRed(self.gettime() + "[缓存] (NULL) -> CACHE")
                totali[1] += 1
                totali[2] += 1
                dns = dns.reply()
                dns.add_answer(*RR.fromZone(rtype.join([])))
                self.socket.sendto(dns.pack(), address)
                return
            rtype = " "+rdnsarr[0]+" "
            rdns = rdnsarr[1]
            printYellow(self.gettime() + "[缓存] "+qname+" -> CACHE")
            totali[0] += 1
            totali[2] += 1
        else:
            print(self.gettime()+"[解析] "+qname+" -> "+arga["dns"][0])
            dnsi = 0
            while dnsi >= 0:
                rdnsarr = self.getdns(qname, dnsi)
                toStr = qname+" -> "+arga["dns"][dnsi]
                if type(rdnsarr) != list:
                    printRed(self.gettime()+"[错误] "+toStr)
                    totali[1] += 1
                    if type(rdnsarr) == int:
                        dnsi = rdnsarr
                        toStr = qname+" -> "+arga["dns"][dnsi]
                        printYellow(self.gettime() + "[备选] "+toStr)
                        continue
                    if rdnsarr == None and arga["cache"] > 1:
                        cache[qname] = None
                    dns = dns.reply()
                    dns.add_answer(*RR.fromZone(rtype.join([])))
                    self.socket.sendto(dns.pack(), address)
                    return
                rtype = " "+rdnsarr[0]+" "
                rdns = rdnsarr[1]
                printGreen(self.gettime()+"[成功] "+toStr)
                totali[0] += 1
                if arga["cache"] > 0:
                    cache[qname] = rdnsarr
                break
        printGreen(self.gettime()+"[结果] "+rtype+" : "+rdns)
        dns = dns.reply()
        dns.add_answer(*RR.fromZone(rtype.join([qname, rdns])))
        self.socket.sendto(dns.pack(), address)
        totali[4] -= 1


def argv():
    arga = {
        'url': '',
        'ipv': '4f',
        'dns': '',
        'bind': '0.0.0.0:53',
        'proxy': '',
        'verify': True,
        'timeout': 5,
        'color': True,
        'ua': 'Mozilla/5.0 (X11; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0',
        'port': 443,
        'cache': 0,
        'thread': True
    }
    info = "NyarukoHttpDNS 版本 1.5.3\nhttps://github.com/kagurazakayashi/NyarukoHttpDNS\n有关命令行的帮助信息，请查看 README.md 。"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:u:6b:d:x:p:c:a:kmht:", [
                                   "url=", "dns=", "proxy=", "port=", "ua=", "timeout="])
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
        elif opt in ("-x", "--proxy"):
            arga["proxy"] = arg
        elif opt in ("-p", "--port"):
            arga["port"] = int(arg)
        elif opt in ("-c", "--cache"):
            arga["cache"] = int(arg)
        elif opt in ("-a", "--ua"):
            arga["ua"] = arg
        elif opt in ("-k", "--no-check-certificate"):
            requests.urllib3.disable_warnings()
            arga["verify"] = False
        elif opt in ("-t", "--timeout"):
            arga["timeout"] = int(arg)
        elif opt in ("-m", "--mono"):
            arga["color"] = False
        elif opt in ("-h", "--no-multithreading"):
            arga["thread"] = False
    if arga["url"] == "":
        print("参数不正确。")
        print(info)
        sys.exit(2)
    chmod = arga["url"].split(':')[0]
    if chmod == 'http':
        arga["port"] = 80
    print(info)
    print("远程服务: "+arga["url"])
    print("本地服务: "+arga["bind"])
    print("IP版本: "+arga["ipv"])
    if arga["dns"] != "":
        print("DNS服务器: "+arga["dns"])
        arga["dns"] = arga["dns"].split(',')
    else:
        arga["dns"] = []
        print("DNS服务器: 由服务器指定")
    if arga["proxy"] != "":
        print("连接方式: 通过代理服务器 "+arga["proxy"])
    else:
        print("连接方式: 直接连接")
    print("SSL证书验证: "+str(arga["verify"]))
    print("超时时间: "+str(arga["timeout"])+" 秒")
    if (arga["cache"] <= 0):
        print("缓存模式: 禁止缓存")
    elif (arga["cache"] == 1):
        print("缓存模式: 缓存查询结果，没查到结果则不缓存")
    elif (arga["cache"] >= 2):
        print("缓存模式: 缓存查询结果，即使没查到结果也将无结果状态缓存")
    print("多线程: "+str(arga["thread"]))
    print("User-Agent: "+str(arga["ua"]))
    arga["hostname"] = socket.gethostname()
    arga["ip"] = socket.gethostbyname(arga["hostname"])
    print("本地主机名: "+arga["hostname"])
    print("本机IP地址: "+arga["ip"])
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
        global arga
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


def loadhosts():
    nhosts = {}
    try:
        f = open('hosts.txt', 'r')
        line = f.readline()
        hostname = arga["hostname"]
        ip = arga["ip"]
        ipStr = ''
        ipStr0 = ''
        if ':' in ip:
            ipStr = ipv6DnsUrl(ip)
            ipStr0 = ipv6DnsUrl(ip, True)
        else:
            ipStr = ipv4DnsUrl(ip)
            ipStr0 = ipv4DnsUrl(ip, True)
        while line:
            if len(line) == 0 or line[0:1] == "#":
                line = f.readline()
                continue
            sparr = line.split(' ')
            fip = sparr[0]
            host = sparr[-1].replace('\n', '').replace('\r', '')
            host = host.replace("<ipurl>", ipStr)
            host = host.replace("<ipurl0>", ipStr0)
            host = host.replace("<ip>", ip)
            host = host.replace("<host>", hostname)
            if host[-1:] != ".":
                host = host + "."
            print(dnss.gettime()+"[文件] "+host+" -> "+fip)
            nhosts[host] = fip
            line = f.readline()
    except Exception as e:
        return e
    return nhosts


def ipv4DnsUrl(ipv4, zeroEnd=False):
    ipv4arr = ipv4.split('.')
    if zeroEnd == True:
        ipv4arr[3] = '0'
    ipv4arr = list(reversed(ipv4arr))
    return '.'.join(ipv4arr)


def ipv6DnsUrl(ipv6, zeroEnd=False):
    ipv6 = ipv6.split(':')
    addZeroUnit = 8 - len(ipv6)
    nipv6 = []
    for ipUnit in ipv6:
        ipUnitLen = len(ipUnit)
        if ipUnitLen == 0:
            for _ in range(addZeroUnit + 1):
                nipv6.append('0000')
            continue
        addZero = 4 - ipUnitLen
        nipv6.append(('0' * addZero) + ipUnit)
    if zeroEnd == True:
        nipv6[7] = '0'
    else:
        nipv6[7] = str(int(nipv6[7]))
    ipv6str = ''.join(nipv6)
    ipv6str = '.'.join(reversed(ipv6str))
    return ipv6str


if __name__ == '__main__':
    """初始化"""
    global arga
    arga = argv()
    global cache
    cache = {}
    global hosts
    hosts = {}
    global totali
    totali = [0, 0, 0, "0", 0]  # 0成功，1失败，2缓存，3显示字符串，4线程计数
    dnss = DNSServer(arga["bind"])
    if os.path.exists('hosts.txt'):
        print(dnss.gettime()+"[启动] 正在加载自定义 hosts 文件...")
        hostsr = loadhosts()
        if type(hostsr) == Exception:
            printRed(dnss.gettime()+"[错误] 未能加载 hosts 文件。")
            printRed(dnss.gettime()+"[错误] "+str(hostsr))
        else:
            hosts = hostsr
            printGreen(dnss.gettime()+"[启动] 已加载自定义 hosts 文件 " +
                       str(len(hostsr.keys()))+" 项。")
    print(dnss.gettime()+"[启动] 正在连接到服务器...")
    trdnsarr = dnss.getdns('linktest')
    if type(trdnsarr) != str:
        printRed(dnss.gettime()+"[错误] 未能连接到服务器。")
    else:
        printGreen(dnss.gettime()+"[启动] 初始化 DNS 服务器完成。")
        try:
            dnss.serve_forever()
        except KeyboardInterrupt:
            printYellow(dnss.gettime()+"[退出] 停止服务 ( "+totali[3]+" )")
