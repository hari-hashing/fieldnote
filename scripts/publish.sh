#!/usr/bin/env bash
# Create a new GitHub repository and push this project using GitHub CLI.
# Usage: ./scripts/publish.sh [owner/repository] [public|private]
set -euo pipefail

REPO_SLUG="${1:-embodied-ai-atlas}"
VISIBILITY="${2:-public}"

if [[ "$VISIBILITY" != "public" && "$VISIBILITY" != "private" ]]; then
  echo "Visibility must be 'public' or 'private'." >&2
  exit 2
fi
if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required. Install it from https://cli.github.com/ and run 'gh auth login'." >&2
  exit 1
fi
if ! command -v git >/dev/null 2>&1; then
  echo "Git is required." >&2
  exit 1
fi
gh auth status >/dev/null

if [[ -d .git ]]; then
  echo "A Git repository already exists here; refusing to alter its remotes or history." >&2
  exit 1
fi

git init --initial-branch=main
git add -A
if git diff --cached --quiet; then
  echo "There are no project files to commit." >&2
  exit 1
fi
if ! git config user.name >/dev/null; then
  git config user.name "Fieldnote Publisher"
fi
if ! git config user.email >/dev/null; then
  gh_user="$(gh api user --jq .login)"
  git config user.email "${gh_user}@users.noreply.github.com"
fi
git commit -m "Initial commit: Fieldnote embodied AI research atlas"
# gh repo create fails safely if the target already exists.
gh repo create "$REPO_SLUG" "--${VISIBILITY}" --source . --remote origin --push

echo
echo "Repository created and pushed: $(git remote get-url origin)"
echo "Next: GitHub repository Settings > Pages > Build and deployment > Source > GitHub Actions."
