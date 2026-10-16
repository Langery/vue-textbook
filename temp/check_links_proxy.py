#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""带代理批量验证外链：2xx/3xx 视为有效，输出失效与超时清单"""
import json, socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error

BASE = "/Users/langery/Desktop/vue-textbook"
links = set()
for f in ["temp/links_md.txt", "temp/links_html.txt"]:
    with open(f"{BASE}/{f}", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                links.add(line)

PROXY = "http://127.0.0.1:7897"
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
)

def clean(u):
    return u.split("#")[0].split("?")[0]

def check(u):
    url = clean(u)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Range": "bytes=0-2048",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with opener.open(req, timeout=20) as resp:
            code = resp.status
            if 200 <= code < 300:
                return u, code, "OK", resp.geturl()
            return u, code, "http_code", resp.geturl()
    except urllib.error.HTTPError as e:
        return u, e.code, "http_code", url
    except urllib.error.URLError as e:
        r = e.reason
        if isinstance(r, socket.timeout):
            return u, 0, "timeout", url
        if isinstance(r, str):
            return u, 0, f"urlerr:{r[:60]}", url
        return u, 0, f"urlerr:{r}", url
    except Exception as e:
        return u, 0, f"err:{type(e).__name__}:{str(e)[:60]}", url

def check_twice(u):
    first = check(u)
    if first[2] in ("timeout", "urlerr", "err"):
        second = check(u)
        if second[2] not in ("timeout", "urlerr", "err"):
            return second
        return first
    return first

results = []
with ThreadPoolExecutor(max_workers=24) as ex:
    futs = {ex.submit(check_twice, u): u for u in sorted(links)}
    for fut in as_completed(futs):
        results.append(fut.result())

results.sort(key=lambda x: x[0])
with open(f"{BASE}/temp/link_results2.json", "w", encoding="utf-8") as fh:
    json.dump(results, fh, ensure_ascii=False, indent=1)

from collections import Counter
cnt = Counter(r[2] for r in results)
print("总数:", len(results), "分组:", dict(cnt))

bad = [r for r in results if r[2] != "OK"]
print(f"\n=== 非 2xx/3xx（{len(bad)} 条）===")
for u, code, kind, final in bad:
    print(f"{kind:>10} {code:>4}  {u}")
