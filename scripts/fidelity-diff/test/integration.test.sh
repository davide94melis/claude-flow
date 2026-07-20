#!/usr/bin/env bash
set -euo pipefail
source /opt/homebrew/opt/nvm/nvm.sh && nvm use 20 >/dev/null 2>&1
DIR="$(cd "$(dirname "$0")/.." && pwd)"
PW="/Users/cnunziata/Projects/BA/ba-web/node_modules/playwright-core"

# 1) Build a golden PNG from an HTML snippet.
cat > /tmp/fd-a.html <<'EOF'
<body style="margin:0"><div style="width:300px;height:120px;background:#2c8287;color:#fff;font:20px sans-serif;display:flex;align-items:center;justify-content:center">Salva</div></body>
EOF
node -e "const{renderHtmlToPng}=require('$DIR/render.js');renderHtmlToPng(require('fs').readFileSync('/tmp/fd-a.html','utf8'),{width:300,height:120,pwPath:'$PW'}).then(r=>require('fs').writeFileSync('/tmp/fd-golden.png',r.png))"

# 2) Identical snippet vs golden -> expect ~100%.
SAME=$(node "$DIR/fidelity-diff.js" --snippet /tmp/fd-a.html --golden /tmp/fd-golden.png --width 300 --height 120 --pw "$PW" --json)
echo "identical: $SAME"
node -e "const s=$SAME;if(s.score<0.99){console.error('EXPECTED >=0.99, got',s.score);process.exit(1)}"

# 3) Modified snippet (different color) vs golden -> expect noticeably < 100%.
cat > /tmp/fd-b.html <<'EOF'
<body style="margin:0"><div style="width:300px;height:120px;background:#b00020;color:#fff;font:20px sans-serif;display:flex;align-items:center;justify-content:center">Salva</div></body>
EOF
DIFF=$(node "$DIR/fidelity-diff.js" --snippet /tmp/fd-b.html --golden /tmp/fd-golden.png --width 300 --height 120 --pw "$PW" --out /tmp/fd-diff.png --json)
echo "modified: $DIFF"
node -e "const s=$DIFF;if(s.score>0.85){console.error('EXPECTED <0.85, got',s.score);process.exit(1)}"
test -f /tmp/fd-diff.png || { echo 'diff png missing'; exit 1; }
echo 'integration: all checks passed'
