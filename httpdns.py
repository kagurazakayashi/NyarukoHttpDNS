#!coding=utf-8
import string
import json
import sys
import os
import getopt
import datetime
import platform
# python3 -m pip install requests
import requests
# pip3 install dnslib
from dnslib import DNSRecord, RR, DNSLabel
# pip3 install gevent
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
        return "["+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"]"

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
            printRed(self.gettime()+"[错误] "+host)
            printRed(self.gettime()+"[错误] "+str(e))
            # print(rdata.text)
            return e
        if rjson[0] == "TE":
            return "OK"
        elif rjson[0] != "OK":
            return None
        return rjson[1]

    def handle(self, data, address):
        global arga
        global cache
        global hosts
        global totali
        hk = hosts.keys()
        hkl = len(hosts.keys())
        ca = cache.keys()
        cal = len(cache.keys())
        totali[3] = "I" + str(totali[0]) + "/E" + str(totali[1]) + "/A" + str(
            totali[0]+totali[1]) + "/C" + str(totali[2]) + "/M" + str(cal) + "/F" + str(hkl)
        print(self.gettime() + "[请求] " + totali[3] +
              " : " + str(address[0]) + ":" + str(address[1]))
        dns = self.parse(data)
        qname = str(dns.q.qname)
        print(self.gettime()+"[解析] "+qname)
        rtype = ""
        rdns = ""
        if hkl > 0 and qname in hk:
            rtype = " A "
            rdns = hosts[qname]
            printYellow(self.gettime() + "[本地] "+qname)
            totali[1] += 1
            totali[2] += 1
        elif arga["cache"] > 0 and qname in ca:
            rdnsarr = cache[qname]
            if type(rdnsarr) != list:
                printRed(self.gettime() + "[缓存] (NULL)")
                totali[1] += 1
                totali[2] += 1
                dns = dns.reply()
                dns.add_answer(*RR.fromZone(rtype.join([])))
                self.socket.sendto(dns.pack(), address)
                return
            rtype = " "+rdnsarr[0]+" "
            rdns = rdnsarr[1]
            printYellow(self.gettime() + "[缓存] "+qname)
            totali[0] += 1
            totali[2] += 1
        else:
            rdnsarr = self.getdns(qname)
            if type(rdnsarr) != list:
                printRed(self.gettime()+"[错误] "+qname)
                totali[1] += 1
                if arga["cache"] > 1 and rdnsarr == None:
                    cache[qname] = None
                dns = dns.reply()
                dns.add_answer(*RR.fromZone(rtype.join([])))
                self.socket.sendto(dns.pack(), address)
                return
            rtype = " "+rdnsarr[0]+" "
            rdns = rdnsarr[1]
            printGreen(self.gettime()+"[成功] "+qname)
            totali[0] += 1
            if arga["cache"] > 0:
                cache[qname] = rdnsarr
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
        'color': True,
        'ua': 'Mozilla/5.0 (X11; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0',
        'port': 443,
        'cache': 0
    }
    info = "NyarukoHttpDNS 版本 1.4.0\nhttps://github.com/kagurazakayashi/NyarukoHttpDNS\n有关命令行的帮助信息，请查看 README.md 。"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:u:6b:d:x:p:c:a:kt:", [
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
    else:
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
    print("User-Agent: "+str(arga["ua"]))
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
        while line:
            if len(line) == 0 or line[0:1] == "#":
                line = f.readline()
                continue
            sparr = line.split(' ')
            ip = sparr[0]
            host = sparr[-1].replace('\n', '').replace('\r', '')
            if host[-1:] != ".":
                # host = host.strip('.')
                host = host+"."
            nhosts[host] = ip
            line = f.readline()
    except Exception as e:
        return e
    return nhosts


if __name__ == '__main__':
    """初始化"""
    global arga
    arga = argv()
    global cache
    cache = {}
    global hosts
    hosts = {}
    global totali
    totali = [0, 0, 0, "0"]  # 成功，失败，缓存，显示字符串
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
