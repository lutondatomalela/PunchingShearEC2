# Contribuir para o PunchingShearEC2

A versão 1.15.0 constitui a base congelada. As alterações seguintes devem usar uma nova versão e manter o histórico e os inventários anteriores.

## Antes de propor uma alteração

- Descreva o problema, o comportamento esperado e o âmbito afetado.
- Utilize exemplos mínimos fictícios. Não publique ficheiros de obras, coordenadas, nomes de clientes ou exportações privadas.
- Para alterações de cálculo, identifique a expressão, convenções, unidades e condições de aplicabilidade; acrescente referências numéricas independentes.
- Preserve os testes de regressão. Uma alteração de resultados exige justificação explícita.
- Para importação e persistência, teste gravação/reabertura, cancelamento, falhas e conservação dos dados não afetados.
- Para interface, siga também o guião de conferência visual.

## Verificação local

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
python tools/verify_baseline.py
```

Atualize a versão, o histórico e a documentação afetada. Numa versão posterior, a conferência da base 1.15.0 é identificada como histórica; o inventário original não deve ser reescrito.

## Organização

Mantenha separadas as alterações de cálculo, interface e documentação sempre que possível. Não inclua ambientes virtuais, caches, relatórios gerados nem cópias de normas protegidas por direitos de autor.

A aceitação de uma alteração pressupõe revisão técnica adequada ao seu âmbito. Uma suite aprovada não substitui essa revisão.
