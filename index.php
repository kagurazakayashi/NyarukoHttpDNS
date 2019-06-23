<?php
set_time_limit(5);
function http403() {
    die(header("HTTP/1.1 403 Forbidden"));
}
function fail($e=null) {
    if ($e) {
        $errinfo = array("NG",$e->getMessage());
    } else {
        $errinfo = array("NG");
    }
    header('Content-Type:application/json;charset=utf-8');
    die(json_encode($errinfo));
}
function ipvar($type,$argv) {
    $ipvena = [1,1];
    if (isset($argv["i"])) {
        if ($argv["i"] == "4") $ipvena = [1,0];
        else if ($argv["i"] == "6") $ipvena = [0,1];
        else if ($argv["i"] == "a" || $argv["i"] == "4f" || $argv["i"] == "6f") $ipvena = [1,1];
    }
    if ($type == "A" && $ipvena[0] == 1) return true;
    else if ($type == "AAAA" && $ipvena[1] == 1) return true;
    return false;
}
$argv = count($_POST) > 0 ? $_POST : $_GET;
if (!isset($argv["h"]) || !preg_match('/^[a-z0-9.\-_]+$/i', $argv["h"])) http403();
$nsresult = null;
if (isset($argv["d"])) {
    if (!filter_var($argv["d"], FILTER_VALIDATE_IP)) http403();
    $dns = array($argv["d"]);
    try {
        @$nsresult = dns_get_record($argv["h"], DNS_ALL, $dns);
    } catch (Exception $e) {
        fail($e);
    }
} else {
    try {
        @$nsresult = dns_get_record($argv["h"], DNS_ALL);
    } catch (Exception $e) {
        fail($e);
    }
}
if (!$nsresult || count($nsresult) == 0) fail();
$echoarr = array();
if (isset($argv["q"]) && $argv["q"] != "0") {
    $qarr = array();
    $qarrv4 = array();
    $qarrv6 = array();
    $min = -1;
    $max = -1;
    foreach ($nsresult as $nowresult) {
        if ((isset($nowresult["ip"]) || isset($nowresult["ipv6"])) && isset($nowresult["type"]) && isset($nowresult["ttl"]) && ipvar($nowresult["type"],$argv)) {
            $ttl = intval($nowresult["ttl"]);
            if ($min == -1) {
                $min = $ttl;
                $max = $ttl;
            }
            if ($ttl <= $min) {
                array_unshift($qarr,$nowresult);
                if ($nowresult["type"] == "A") array_unshift($qarrv4,$nowresult);
                else if ($nowresult["type"] == "AAAA") array_unshift($qarrv6,$nowresult);
                $min = $ttl;
            } else if ($ttl >= $max) {
                array_push($qarr,$nowresult);
                if ($nowresult["type"] == "A") array_push($qarrv4,$nowresult);
                else if ($nowresult["type"] == "AAAA") array_push($qarrv6,$nowresult);
                $max = $ttl;
            }
        }
    }
    if ($argv["q"] == "1") {
        if (isset($argv["i"]) && $argv["i"] == "4f") {
            $echoarr = array_merge($qarrv4,$qarrv6);
        } else if (isset($argv["i"]) && $argv["i"] == "6f") {
            $echoarr = array_merge($qarrv6,$qarrv4);
        } else {
            $echoarr = $qarr;
        }
    } else if ($argv["q"] == "2" || $argv["q"] == "3" || $argv["q"] == "4") {
        if (isset($argv["i"]) && $argv["i"] == "4f") {
            $echoarr = end($qarrv4) ? end($qarrv4) : array();
        } else if (isset($argv["i"]) && $argv["i"] == "6f") {
            $echoarr = end($qarrv6) ? end($qarrv6) : array();
        } else {
            $echoarr = end($qarr) ? end($qarr) : array();
        }
        if ($argv["q"] == "3") {
            $ntype = "A";
            if (isset($echoarr["ipv6"])) {
                $echoarr = ["AAAA",$echoarr["ipv6"]];
            } else if (isset($echoarr["ip"])) {
                $echoarr = ["A",$echoarr["ip"]];
            } else {
                fail();
            }
        } else if ($argv["q"] == "4") $echoarr = isset($echoarr["ipv6"]) ? $echoarr["ipv6"] : $echoarr["ip"];
    }
} else {
    $echoarr = $nsresult;
}
header('Content-Type:application/json;charset=utf-8');
echo json_encode(["OK",$echoarr]);
?>
