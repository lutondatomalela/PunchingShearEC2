# Compilar a distribuição Windows

Requer Windows x64, Python 3.12 com Tk e Git. Trabalhe numa cópia limpa do commit que pretende distribuir.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt -r requirements-build.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\python tools/build_windows.py
```

O script cria um executável autónomo com PyInstaller e ensaia-o a partir de uma pasta temporária independente, com caracteres portugueses no caminho. A distribuição só é preparada se esse ensaio terminar com sucesso.

Os artefactos ficam em `artifacts/`: executável, ZIP Windows, ZIP do código do commit, metadados e hashes SHA-256. A pasta `build/` contém apenas intermédios. Estes ficheiros gerados não integram o histórico Git; são anexados à release.

## Publicação

O workflow executa primeiro todos os testes em Linux/Python 3.10 e 3.12 e Windows/Python 3.12. O executável é compilado no Windows, depois da aprovação dos três ambientes.

A publicação automática só ocorre num push em `main`, no repositório original, cujo título do commit começa por `Publicar RC Windows `. A versão deve conter `-rc.`. O publicador cria uma pre-release em rascunho, envia os artefactos e só então a torna visível. Uma tag ou release já existente provoca a paragem; não é substituída.

Para uma nova candidata, incremente o identificador RC e atualize as notas de publicação. Alterações de documentação sem esse título executam os testes e a compilação, mas não publicam outra versão.

## Limites

Os testes não substituem a inspeção visual da interface. A distribuição não utiliza certificado de assinatura de código. Não são incluídos dados de projeto nem normas protegidas por direitos de autor. O ZIP contém as licenças disponíveis dos componentes distribuídos.
