#!/usr/bin/env bash
# Deploy the checked-out commit to production.
#
#   deploy/deploy.sh [all|api|web]
#
# The commit must be clean and already on origin/master. To roll back, check out an older
# master commit and run this again.
set -euo pipefail

TARGET="${1:-all}"

SSH_HOST=root@104.237.147.195
SERVER_REPO=/var/repo/api.dailyoffice2019.com
SERVER_DIR=/var/www/api.dailyoffice2019.com
PAGES_PROJECT=dailyoffice2019
WRANGLER=wrangler@4.149.0
API_URL=https://api.dailyoffice2019.com/api/v1/psalms
WEB_URL=https://www.dailyoffice2019.com/

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
fail() {
  echo "$*" >&2
  exit 1
}
trap '[ $? = 0 ] || printf "\n\033[1;31mDEPLOY FAILED\033[0m\n" >&2' EXIT

case "$TARGET" in
  all | api | web) ;;
  *)
    echo "usage: $0 [all|api|web]" >&2
    exit 2
    ;;
esac

cd "$(git rev-parse --show-toplevel)"

step "Preflight"
[ -z "$(git status --porcelain)" ] || fail "working tree has uncommitted or untracked changes"
git fetch --quiet origin master
git merge-base --is-ancestor HEAD origin/master || fail "HEAD is not on origin/master; push it first"
SHA=$(git rev-parse HEAD)
echo "Deploying $(git log -1 --format='%h %s') [$TARGET]"

if [ "$TARGET" != api ]; then
  step "Building frontend"
  NODE_WANT="v$(cat app/.nvmrc)"
  if [ "$(node -v 2>/dev/null)" != "$NODE_WANT" ]; then
    set +eu
    . "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
    nvm install "$NODE_WANT" >/dev/null
    set -eu
  fi
  [ "$(node -v)" = "$NODE_WANT" ] || fail "need Node $NODE_WANT (app/.nvmrc)"
  (cd app && npm ci --no-audit --no-fund --loglevel=error && npx vitest run && npm run build)
fi

if [ "$TARGET" != web ]; then
  step "Deploying API"
  git push --force production "$SHA:refs/heads/live"
  ssh "$SSH_HOST" "git --git-dir=$SERVER_REPO --work-tree=$SERVER_DIR checkout --force $SHA && bash $SERVER_DIR/deploy/server.sh"
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "$API_URL")
  [ "$code" = 200 ] || fail "$API_URL returned $code"
  echo "$API_URL -> 200"
fi

if [ "$TARGET" != api ]; then
  step "Deploying frontend"
  (cd app && npx --yes "$WRANGLER" pages deploy dist --project-name="$PAGES_PROJECT" --branch=master \
    --commit-hash="$SHA" --commit-message="$(git log -1 --format=%s)" --commit-dirty=false)
  entry=$(grep -oE 'assets/index-[^"]+\.js' app/dist/index.html)
  for attempt in 1 2 3 4 5 6; do
    [[ "$(curl -s --max-time 30 "$WEB_URL")" == *"$entry"* ]] && break
    [ "$attempt" = 6 ] && fail "$WEB_URL is not serving the new build ($entry)"
    sleep 5
  done
  echo "$WEB_URL is serving $entry"
fi

printf '\n\033[1;32mDeployed %s [%s]\033[0m\n' "$(git log -1 --format='%h %s')" "$TARGET"
