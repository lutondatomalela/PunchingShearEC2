# Base congelada — 1.15.0

A versão **1.15.0** é a referência para as próximas melhorias do PunchingShearEC2. O commit `9dbf0bf8fa17e18c4ce22e874e6853548d13c560` conserva o código de cálculo, interface e testes da distribuição original. As versões seguintes são identificadas separadamente.

## Identificação

- Distribuição original: `PunchingShearEC2_v1_15_0.zip`.
- Data da distribuição: 13 de setembro de 2026.
- Data de preparação do repositório: 15 de setembro de 2026.
- SHA-256 da distribuição original: `510dcd38284bcbb0fa64c769edddcf62fd81d9ae28e81366b529f12290d1f70f`.
- Identificador de versão: `punching/version.py`.
- Inventário do código congelado: [validation/baseline_1_15_0.json](validation/baseline_1_15_0.json).

O hash acima identifica o ZIP original, não o arquivo de código-fonte gerado pelo GitHub. O arquivo publicado no repositório inclui documentação reorganizada e integração contínua; por isso tem um hash próprio, embora o código da aplicação seja conservado.

## Regra de evolução

1. A identificação `v1.15.0` não deve ser movida para outro commit nem reutilizada para código diferente.
2. Correções e novas funcionalidades devem usar uma nova versão, com testes e descrição no histórico.
3. O inventário original permanece como referência; não se deve alterar os seus hashes para ocultar uma alteração ao código.
4. Na versão 1.15.0, `python tools/verify_baseline.py` exige correspondência com esse inventário.
5. Os conjuntos de projeto são independentes do repositório; não devem ser incluídos nos commits.

O congelamento é uma decisão de controlo de versões, não uma certificação de segurança estrutural. As limitações de [VALIDACAO.md](VALIDACAO.md) permanecem aplicáveis.

## Estado da publicação original

A base está preservada no [commit 9dbf0bf](https://github.com/lutondatomalela/PunchingShearEC2/commit/9dbf0bf8fa17e18c4ce22e874e6853548d13c560). A release 1.15.0 não chegou a ser criada: os testes Windows identificaram leituras de texto dependentes da codificação local e uma falha de saída da linha de comandos com o símbolo β.

A distribuição 1.15.1-rc.1 corrige esses pontos e acrescenta o executável Windows. O inventário original não é alterado. A versão estável só deve ser publicada após a validação da candidata.
