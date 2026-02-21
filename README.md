# colors_auto_training
A semi supervised training system for colors.


## Fluxo recomendado para evitar conflitos no PR

Quando o GitHub mostrar que a branch tem conflitos com `feature/main`, sincronize **pela linha de comando** na sua branch de trabalho:

```bash
./scripts/sync_feature_main.sh feature/main origin
```

Esse script:
- habilita `git rerere` (reaproveita resoluções de conflito repetidas),
- faz `fetch` da branch alvo,
- executa `rebase` da sua branch atual sobre `feature/main`,
- mostra os arquivos em conflito quando necessário.

Depois de resolver conflitos e finalizar o rebase:

```bash
git push --force-with-lease
```

Se `rg` não estiver instalado no seu ambiente, use este comando para encontrar marcadores de conflito somente nos arquivos versionados:

```bash
git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- . ':(exclude).venv/**'
```

Isso normalmente elimina o botão de conflito no PR e evita ter que resolver no editor web.

## Verificação rápida pós-merge

Para evitar subir conflitos residuais (ex: `<<<<<<< HEAD`) ou erros de sintaxe após resolver merge/rebase, rode:

```bash
./scripts/verify_merge_integrity.sh
```

Esse script valida:
- marcadores de conflito em arquivos rastreados pelo git,
- sintaxe de todos os arquivos Python versionados no repositório.

