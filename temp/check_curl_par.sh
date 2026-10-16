#!/bin/bash
# curl 并行验证（xargs -P 16），输出非 2xx 清单
cd /Users/langery/Desktop/vue-textbook
check_one() {
  url="$1"
  u="${url%%#*}"
  code=$(curl -s -o /dev/null -L --max-time 30 -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36" -H "Range: bytes=0-2048" -w "%{http_code}" "$u" 2>/dev/null)
  if [[ ! "$code" =~ ^2[0-9][0-9]$ ]]; then
    echo "$code | $url"
  fi
}
export -f check_one
cat temp/links_md.txt temp/links_html.txt | sort -u | xargs -P 16 -I {} bash -c 'check_one "$@"' _ {} | sort > temp/bad_links.txt
echo "=== 非2xx 清单 ==="
cat temp/bad_links.txt
