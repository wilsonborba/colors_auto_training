#!/usr/bin/env bash
set -euo pipefail

TARGET_BRANCH="${1:-feature/main}"
REMOTE_NAME="${2:-origin}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Erro: execute dentro de um repositório git." >&2
  exit 1
fi

CURRENT_BRANCH="$(git branch --show-current)"
if [[ -z "$CURRENT_BRANCH" ]]; then
  echo "Erro: HEAD destacada. Faça checkout de uma branch antes." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Erro: working tree suja. Commit/stash antes de sincronizar." >&2
  exit 1
fi

echo "[1/5] Habilitando rerere para reaproveitar resoluções de conflito..."
git config rerere.enabled true

echo "[2/5] Buscando '$TARGET_BRANCH' em '$REMOTE_NAME'..."
if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  git fetch "$REMOTE_NAME" "$TARGET_BRANCH"
  TARGET_REF="$REMOTE_NAME/$TARGET_BRANCH"
elif git show-ref --verify --quiet "refs/heads/$TARGET_BRANCH"; then
  TARGET_REF="$TARGET_BRANCH"
else
  echo "Erro: remoto '$REMOTE_NAME' não existe e branch local '$TARGET_BRANCH' não encontrada." >&2
  exit 1
fi

echo "[3/5] Rebase de '$CURRENT_BRANCH' sobre '$TARGET_REF'..."
set +e
git rebase "$TARGET_REF"
REBASERC=$?
set -e

if [[ $REBASERC -ne 0 ]]; then
  echo
  echo "Conflitos detectados. Resolva arquivos e rode:"
  echo "  git add <arquivos>"
  echo "  git rebase --continue"
  echo
  echo "Para desistir:"
  echo "  git rebase --abort"
  echo
  echo "Arquivos em conflito:"
  git diff --name-only --diff-filter=U || true
  echo
  echo "Dica: para procurar marcadores de conflito em arquivos rastreados (sem depender de rg):"
  echo "  git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- . ':(exclude).venv/**'"
  exit $REBASERC
fi

echo "[4/5] Rebase concluído sem conflitos pendentes."

echo "[5/5] Pronto. Faça push com atualização de histórico:"
echo "  git push --force-with-lease"
