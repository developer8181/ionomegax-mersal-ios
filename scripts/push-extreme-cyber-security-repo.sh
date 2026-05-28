#!/usr/bin/env bash
# Push Extreme Cyber Security rebrand to a new GitHub repo (create repo first on GitHub).
set -euo pipefail
REPO_URL="${1:-https://github.com/developer8181/extreme-cyber-security.git}"
BRANCH="${2:-cursor/extreme-cyber-security-rebrand-eef7}"

git remote remove ecs 2>/dev/null || true
git remote add ecs "$REPO_URL"
git push -u ecs "$BRANCH:main"
echo "Pushed to $REPO_URL (branch main from $BRANCH)"
