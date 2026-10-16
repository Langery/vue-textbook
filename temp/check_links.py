#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量验证教材外链有效性：按状态码分组输出"""
import re, sys, json
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error, socket

BASE = "/Users/langery/Desktop/vue-textbook"
links = set()
for f in ["temp/links_md.txt", "temp/links_html.txt"]:
    with open(f"{BASE}/{f}", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                links.add(line)

# 去掉锚点、统一小写 host 后用于请求
def clean(u):
    u = u.split("#")[0].split("?")[0]
    return u

def check(u):
    url = clean(u)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    # 部分站点拒绝 HEAD，统一用 GET + Range
    headers["Range"] = "bytes=0-1024"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            code = resp.status
            final = resp.geturl()
            # 3xx 已自动跟随，最终 URL 不同视为重定向到有效页
            if code == 200:
                return u, code, "OK", final
            return u, code, "http_code", final
    except urllib.error.HTTPError as e:
        return u, e.code, "http_code", url
    except urllib.error.URLError as e:
        r = e.reason
        if isinstance(r, socket.timeout):
            return u, 0, "timeout", url
        if isinstance(r, str) and "Name or service not known" in r:
            return u, 0, "dns_fail", url
        return u, 0, f"urlerr:{r}", url
    except Exception as e:
        return u, 0, f"err:{type(e).__name__}", url

results = []
with ThreadPoolExecutor(max_workers=30) as ex:
    futs = {ex.submit(check, u): u for u in sorted(links)}
    for fut in as_completed(futs):
        results.append(fut.result())

results.sort(key=lambda x: x[0])
with open(f"{BASE}/temp/link_results.json", "w", encoding="utf-8") as fh:
    json.dump(results, fh, ensure_ascii=False, indent=1)

from collections import Counter
cnt = Counter(r[2] for r in results)
print("总数:", len(results))
print("分组统计:", dict(cnt))

bad = [r for r in results if r[1] not in (200, 301, 302, 303, 307, 308) or r[2] not in ("OK", "http_code")]
print("\n=== 非2xx/3xx 或异常链接 ===")
for u, code, kind, final in bad:
    print(f"{kind:>12} {code:>4}  {u}")
