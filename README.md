# NyarukoHttpDNS 1.1.0
将 DNS 解析结果使用 PHP 经过 `HTTP`/`HTTPS` 传输给本地客户端。

![客户端工作截图](https://github.com/kagurazakayashi/NyarukoHttpDNS/raw/master/ScreenShot-1.png)

# PHP7 服务端
## 接收参数
可以接收以下 `GET` 或者 `POST` 参数：
- `h`: 要查询的主机名
- `d`: 指定 DNS 服务器（可选，不提供则用主机当前 DNS 设置）。
- `i`: 需要查询的 IP 地址类型（可选）。可接受的选项：
  - `a`（默认值）, `4`, `4f`, `6`, `6f`
  - a 为显示所有，4 为仅返回 IPv4，6 为仅返回 IPv6，带 f 则为全部显示并靠前显示此项。
- `q`: 精简显示级别（可选）。可接受的选项：
  - `0`: 返回所有查询结果，包括 MX、TXT 等全部类型记录。此项将会忽略 `i` 的设置，`i` 会被强制指定为 `a`。
  - `1`: 返回所有 A/AAAA 记录及其详细信息。
  - `2`: 返回 TTL 最高的一条 A/AAAA 记录及其详细信息。此项将会忽略 `i` 的 `f` 参数。
  - `3`: 只返回 TTL 最高的一条 A/AAAA 记录的 记录类型 和 IP 地址。此项将会忽略 `i` 的 `f` 参数。
  - `4`: 只返回 TTL 最高的一条 A/AAAA 记录的 IP 地址。此项将会忽略 `i` 的 `f` 参数。
- `t`: 超时时间（秒）。超过指定时间则 PHP 脚本中止。

## 返回结果

- 成功：返回 JSON ，内容为数组，第一位为 `OK` 。
- 失败：返回 JSON ，内容为数组，第一位为 `NG` 。
- 错误：返回 HTTP 403 状态码，检查提供的参数是否正确。

```
$ curl "http://127.0.0.1/NyarukoHttpDNS/index.php?h=php.net&d=8.8.8.8&i=6&q=3"
["OK",["AAAA","2a02:cb40:200::1ad"]]

$ curl "http://127.0.0.1/NyarukoHttpDNS/index.php" -X POST -d "h=php.net&d=8.8.8.8&i=4&q=4"
["OK","185.85.0.29"]

$ curl "http://127.0.0.1/NyarukoHttpDNS/?h=php.net&d=8.8.8.8&i=a&q=0"
["OK",[{"host":"php.net","class":"IN","ttl":377,"type":"A","ip":"185.85.0.29"},{"host":"php.net","class":"IN","ttl":377,"type":"NS","target":"dns3.easydns.org"},{"host":"php.net","class":"IN","ttl":377,"type":"NS","target":"dns1.easydns.com"},{"host":"php.net","class":"IN","ttl":377,"type":"NS","target":"dns2.easydns.net"},{"host":"php.net","class":"IN","ttl":377,"type":"NS","target":"dns4.easydns.info"},{"host":"php.net","class":"IN","ttl":377,"type":"SOA","mname":"ns1.php.net","rname":"admin.easydns.com","serial":1561190463,"refresh":16384,"retry":2048,"expire":1048576,"minimum-ttl":2560},{"host":"php.net","class":"IN","ttl":39,"type":"MX","pri":0,"target":"php-smtp3.php.net"},{"host":"php.net","class":"IN","ttl":377,"type":"TXT","txt":"v=spf1 ip4:72.52.91.12 ip6:2a02:cb41::8 ip4:140.211.15.143 ip4:208.43.231.12 ?all","entries":["v=spf1 ip4:72.52.91.12 ip6:2a02:cb41::8 ip4:140.211.15.143 ip4:208.43.231.12 ?all"]},{"host":"php.net","class":"IN","ttl":377,"type":"AAAA","ipv6":"2a02:cb40:200::1ad"}]]
```

## 自定义 hosts
可以创建一个文件名为 `hosts` 的文件和 php 文件放置在一起，用于自定义 ip - host 对应关系。
- 如果客户端要查询的 host 被记录在此文件中，则直接返回此文件所记录的 ip 地址，不进行任何网络查询， `d` 参数也将被忽略。
- 建议定义一个与查询服务器对应的 ip 地址。
- 如果不需要此功能，请不要放置同目录下的 `hosts` 文件。
- 如果写入过于庞大的数据且访问量较大，会影响 I/O 性能。
- 写法和标准 host 文件一致：
  - `ip地址` `主机名`

# Python3 客户端
## 安装
`pip3 install dnslib`
`pip3 install gevent`
`python3 -m pip install requests`

## 接收参数
`python3 ns.py -u <PHP网址> [-6] [-d <DNS地址>]`
- `-u <PHP网址>` 或 `--url <PHP网址>`
  - 输入上面PHP文件所部署到的网址
- `-b <IP地址:端口>` 或 `--bind <IP地址:端口>`
  - （可选）设置 DNS 服务器绑定的 IP地址 和 端口。默认值是 `0.0.0.0:53`。
- `-6` 或 `--ipv6`
  - （可选）优先返回 IPv6 地址，否则优先返回 IPv4 地址。
- `-d <DNS的IP地址>` 或 `--dns <DNS的IP地址>`
  - （可选）从指定 DNS 服务器进行查询，否则使用 PHP 主机的 DNS 设置。
- `-p <代理服务器地址>` 或 `--proxy <代理服务器地址>`
  - （可选）设置代理服务器，可以指定一个 http 代理服务器进行通信。
- `-k` 或 `--no-check-certificate`
  - （可选）使用 https 通信时，不要检查证书（不推荐）。
- `-t` 或 `--timeout`
  - （可选）超时时间（整数秒），等待指定时间后仍未收到返回结果则中止。此选项的数值会同时发送给 PHP 端的此参数。
- `-m` 或 `--mono`
  - （可选）以单色模式输出。提供此项则按默认颜色输出，不输出彩色提示信息。如果需要将输出记录到日志则建议提供此参数。

## 使用
- 使用 `nslookup php.net 127.0.0.1` 进行测试。
- 若测试没问题，直接设置系统 DNS 即可。

# 实践举例
客户端启动参数：

`python3 httpdns.py -u "https://www.xxx.org/n.php" -p "http://127.0.0.1:1080" -t 15 -d 8.8.8.8`

此条命令的含义：
- 访问的 PHP 网址是 `https://www.xxx.org/n.php`
- 要通过代理服务器 `http://127.0.0.1:1080` 访问这个 PHP 网址
- 要求 PHP 服务器必须在 15 秒内完成 DNS 查询
- 要求从 DNS 服务器 `8.8.8.8` 进行查询

# 附：清除 DNS 缓存命令

- Windows: `ipconfig /flushdns`
- macOS: `sudo dscacheutil -flushcache`
- Linux: `service nscd restart`