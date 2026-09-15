# PunchingShearEC2 — Windows

## Obter e executar

A distribuição **1.15.1-rc.1** é uma candidata a lançamento para Windows x64. Inclui Python, Tk e as dependências; não exige instalar Python.

1. Abra a [release v1.15.1-rc.1](https://github.com/lutondatomalela/PunchingShearEC2/releases/tag/v1.15.1-rc.1).
2. Descarregue `PunchingShearEC2-1.15.1-rc.1-Windows-x64.zip`.
3. Extraia a pasta completa para uma localização à sua escolha.
4. Execute `PunchingShearEC2.exe`.
5. Comece por um exemplo e confirme os dados antes de calcular.

Também está disponível o ficheiro `.exe` autónomo. O ZIP acrescenta exemplos externos, documentação, metadados e licenças de terceiros. Guarde os seus projetos numa pasta própria, fora da distribuição.

## Identificação e integridade

A janela e os relatórios identificam a versão. `BUILD-INFO.json` regista o commit de origem, ambiente de compilação, dependências e resultado do ensaio do executável. `SHA256SUMS.txt` permite conferir os ficheiros descarregados:

```powershell
Get-FileHash .\PunchingShearEC2-1.15.1-rc.1-Windows-x64.zip -Algorithm SHA256
```

Compare o valor com a linha correspondente no ficheiro SHA256SUMS. Esta RC não tem assinatura digital de código; o sistema operativo pode apresentar um aviso de editor desconhecido. O hash identifica o ficheiro, mas não substitui uma assinatura digital.

## Primeiro uso

Abra **Exemplos**, selecione um caso e execute **Calcular / F5**. Confira as páginas **Verificações**, **Fiadas** e **Memória**. Para vários pilares, utilize **Pilares…** e guarde o conjunto em JSON.

Os ficheiros de projeto 1.15.0 continuam a usar o mesmo formato. Conserve o original ao ensaiar a RC e recalcule os resultados depois de alterar dados. Consulte [a documentação](README.md) para importação, hipóteses e limitações.

## Estado da RC

O processo de publicação exige testes em Linux e Windows e um ensaio automático do executável: arranque de Tk, catálogo, cálculo, gravação/reabertura e exportação PDF/XLSX/TXT/JSON. A validação visual em postos Windows, diferentes escalas de ecrã e fluxos completos de utilização permanece por concluir antes da versão estável.

A compilação é realizada num runner Windows x64. Não foram ensaiados Windows ARM, versões antigas do sistema operativo nem execução em rede.

## Comunicar um problema

Inclua a versão, versão do Windows, escala de ecrã, passos para reproduzir, comportamento esperado e captura da mensagem. Use um exemplo mínimo sem dados de obra confidenciais. [Issues do projeto](https://github.com/lutondatomalela/PunchingShearEC2/issues).
