#!/bin/bash
# 用 curl 直连验证，2xx 视为有效，输出非 2xx 清单
cd /Users/langery/Desktop/vue-textbook
: > temp/bad_links.txt
cat temp/links_md.txt temp/links_html.txt | sort -u | while IFS= read -r url; do
  u="${url%%#*}"
  code=$(curl -s -o /dev/null -L --max-time 25 -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36" -H "Range: bytes=0-2048" -w "%{http_code}" "$u" 2>/dev/null)
  if [[ "$code" =~ ^2[0-9][0-9]$ ]]; then
    :
  else
    echo "$code | $url" >> temp/bad_links.txt
  fi
done
echo "=== 非2xx 清单 ==="
cat temp/bad_links.txt
