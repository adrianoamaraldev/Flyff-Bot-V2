Faça um commit seguindo o padrão de Conventional Commits em português.

## Formato

```
<tipo>(<escopo opcional>): <descrição curta em português>
```

## Tipos

| Tipo | Quando usar |
|------|-------------|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `chore` | Manutenção, configs, dependências |
| `refactor` | Refatoração sem mudança de comportamento |
| `style` | Formatação/estilo de código sem lógica |
| `ui` | Mudanças visuais no frontend |
| `perf` | Melhoria de performance |
| `docs` | Documentação |

## Exemplos

```
feat(bot): adicionar seleção de monstro alvo no select
fix(vision): corrigir offset_x não definido no detect_by_name
chore(deps): instalar uvicorn[standard] com suporte a websocket
ui(dashboard): tornar card de kills compacto com largura fixa
```

## Regras

- Descrição sempre em português
- Letra minúscula após os dois pontos
- Sem ponto final
- Escopo opcional mas recomendado (ex: bot, vision, frontend, config, healing, loot)
- Máximo ~72 caracteres na primeira linha

## Processo

1. Rodar `git diff` e `git status` para ver o que mudou
2. Escolher o tipo correto e montar a mensagem
3. Fazer `git add` nos arquivos relevantes e `git commit`
