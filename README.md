# NyarukoHttpDNS
将 DNS 解析结果使用 PHP 经过 HTTP/HTTPS 传输给本地客户端。

# PHP7 服务端
## 接收参数
可以接收以下 GET 或者 POST 参数：
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

## 返回结果
返回 403 状态码或者 JSON 。
```
$ curl "http://127.0.0.1/httpdns/ns.php?h=php.net&d=114.114.114.114&i=6&q=3"
["OK","2a02:cb40:200::1ad"]

$ curl "http://127.0.0.1/httpdns/ns.php?h=php.net&d=8.8.8.8&i=a&q=0"
["OK",[{"host":"php.net","class":"IN","ttl":377,"type":"A","ip":"185.85.0.29"},{"host":"php.net","class":"IN","ttl":377,"type":"NS","target":"dns3.easydns.org"},{"host":"php.net","class":"IN","ttl":377,"type":"NS","target":"dns1.easydns.com"},{"host":"php.net","class":"IN","ttl":377,"type":"NS","target":"dns2.easydns.net"},{"host":"php.net","class":"IN","ttl":377,"type":"NS","target":"dns4.easydns.info"},{"host":"php.net","class":"IN","ttl":377,"type":"SOA","mname":"ns1.php.net","rname":"admin.easydns.com","serial":1561190463,"refresh":16384,"retry":2048,"expire":1048576,"minimum-ttl":2560},{"host":"php.net","class":"IN","ttl":39,"type":"MX","pri":0,"target":"php-smtp3.php.net"},{"host":"php.net","class":"IN","ttl":377,"type":"TXT","txt":"v=spf1 ip4:72.52.91.12 ip6:2a02:cb41::8 ip4:140.211.15.143 ip4:208.43.231.12 ?all","entries":["v=spf1 ip4:72.52.91.12 ip6:2a02:cb41::8 ip4:140.211.15.143 ip4:208.43.231.12 ?all"]},{"host":"php.net","class":"IN","ttl":377,"type":"AAAA","ipv6":"2a02:cb40:200::1ad"}]]
```

# Python3 客户端
## 安装
`pip install dnslib`
`pip install gevent`
`pip install requests`

## 接收参数
`python ns.py -u <PHP网址> [-6] [-d <DNS地址>]`
- `-u <PHP网址>` 或 `--url <PHP网址>` 
  - 输入上面PHP文件所部署到的网址
- `-6` 或 `--ipv6`
  - （可选）优先返回 IPv6 地址，否则优先返回 IPv4 地址。
- `-d <DNS的IP地址>` 或 `--dns <DNS的IP地址>`
  - （可选）从指定 DNS 服务器进行查询，否则使用 PHP 主机的 DNS 设置。
