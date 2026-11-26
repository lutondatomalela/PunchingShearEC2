# Relatórios para a memória descritiva e justificativa

O PDF organiza os resultados em quadros e fichas de cálculo. Cada parâmetro é identificado pelo nome, símbolo e unidade: por exemplo, **resistência característica à compressão do betão — fck — MPa**. Os esforços são apresentados em kN e kN.m, as áreas de armadura longitudinal em cm²/m e as utilizações em percentagem.

## Exportar um conjunto

1. Abra o conjunto e calcule as ligações pretendidas na versão atual.
2. Em **Pilares… → Relatório do conjunto…**, escolha o piso, grupo ou seleção.
3. Mantenha **Apenas resultados calculados e atualizados** para exportar os resultados disponíveis. O quadro inicial indica quantas combinações foram calculadas, o total previsto e as omissões.
4. Deixe desmarcada **PDF: incluir fichas de todas as combinações** para obter a apresentação condensada.
5. Exporte em **PDF** e confira o âmbito e as conclusões antes de anexar o documento à memória.

A apresentação condensada inclui as combinações condicionantes de cada verificação, os máximos de armadura e extensão da zona armada, as falhas e as pendências exportadas. Também conserva uma ficha para cada definição física distinta dos dados. Os esforços de cada ficha pertencem à mesma combinação; não são uma envolvente de componentes independentes.

Para ver todas as combinações, ative a opção de fichas completas. Para incluir também casos por calcular ou com esforços por definir, desative o filtro de resultados calculados: obtém um mapa de acompanhamento, com essas pendências explícitas.

## Organização do PDF

- Identificação do projeto, referencial normativo, âmbito e síntese por piso e apoio.
- Materiais e hipóteses comuns apresentados uma única vez, quando coincidem em todas as fichas.
- Dados da ligação e armadura longitudinal, incluindo base, reforço, recobrimento e alturas úteis no modo automático.
- Esforços concomitantes, verificações resistentes, combinação condicionante e utilização.
- Perímetros com designações completas, planta esquemática e legenda.
- Fiadas de armadura, verificações locais e condições de amarração quando aplicáveis.

Os cabeçalhos usam cinza claro e texto escuro. O rodapé identifica o programa, a versão, a data de emissão, a página e o repositório. As plantas são esquemáticas e sem escala; não substituem os pormenores construtivos.

## Conclusões e rastreabilidade

**PARCIAL — PENDENTE** significa que a ligação não tem cobertura completa das combinações previstas, mesmo que as combinações já calculadas verifiquem. **Pormenor comum por conferir** mantém-se quando existem propostas diferentes de armadura entre combinações. A simplificação gráfica não altera estas conclusões.

Os códigos internos, hashes e registos brutos de importação saem da apresentação PDF. A exportação **JSON** conserva o resultado completo e as estruturas de dados; **TXT** mantém a memória técnica detalhada. O **XLSX** mantém as folhas de cálculo e de rastreabilidade, com nomes completos nas entradas e nos parâmetros, valores numéricos e unidades explícitas. O formato das folhas «Resumo» e «Parametros» foi atualizado; integrações que leiam essas folhas devem usar os novos cabeçalhos.

Um PDF antigo não é um projeto editável. Para emitir o relatório com a nova apresentação, abra o JSON do caso ou conjunto, recalcule e exporte novamente. A atualização do programa não modifica os PDFs anteriormente emitidos.

## Exemplo público

[Abrir o PDF de demonstração](examples/Relatorio_conjunto.pdf).

Este exemplo usa exclusivamente os dados fictícios de `examples/importacao/Grupos_Ligacoes.json`, no Piso 1. São quatro combinações calculadas de seis previstas. Duas combinações modais permanecem pendentes; por isso, o relatório demonstra também a indicação de cobertura parcial.

Para reproduzir a amostra:

```sh
python tools/report_example.py --output docs/examples/Relatorio_conjunto.pdf
```

As fórmulas, as verificações resistentes e o formato dos projetos não foram alterados nesta revisão da apresentação.
