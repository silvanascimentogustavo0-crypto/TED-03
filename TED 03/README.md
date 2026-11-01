# TED 03 - Gerenciador de Persistência de Dados (CSV e JSON)

**Instituição:** Centro Universitário UNIBALSAS  
**Curso:** Análise e Desenvolvimento de Sistemas  
**Disciplina:** Algoritmos e Programação Avançada (2026.2)  
**Integrantes:** Gustavo Silva do Nascimento (RA 26.1.15196) e Kauê Lima Oliveira (RA 26.1.19982)  
**Atividade:** TED 03 - Gerenciador de Persistência de Dados em Arquivos Estruturados (CSV e JSON)  
**Entrega:** 31/10/2026 | **Valor:** 1,5 ponto

## Finalidade

Aplicação em Python 3.10+ que lê, converte e atualiza arquivos CSV/JSON, com codificação UTF-8, `with open`, mensagens de erro claras, backup automático antes de substituir arquivos e escrita por arquivo temporário.

## Estrutura do repositório

```text
TED03_Gerenciador_Persistencia/
├── main.py
├── src/persistencia/
│   ├── __init__.py
│   ├── arquivos.py         # leitura, escrita atômica e backup
│   └── servico.py          # conversão e atualização
├── dados/
│   ├── clientes.csv
│   └── produtos.json
├── tests/
│   └── test_persistencia.py
├── evidencias/             # saídas reais e registros visuais dos testes
├── relatorio/
│   └── TED03_Relatorio_Gustavo_Kaue.pdf
└── README.md
```

## Requisitos e instalação

- Python 3.10 ou superior. Nenhuma biblioteca externa é necessária para a aplicação.
- Abra um terminal na pasta raiz deste repositório.
- Os exemplos abaixo funcionam no Windows (`py` pode substituir `python`) e Linux/macOS.

## Como executar

**1. Ler os arquivos**

```bash
python main.py ler-csv dados/clientes.csv
python main.py ler-json dados/produtos.json
```

**2. Converter CSV em JSON**

```bash
python main.py csv-para-json dados/clientes.csv resultados/clientes.json
```

**3. Converter JSON em CSV**

```bash
python main.py json-para-csv dados/produtos.json resultados/produtos.csv
```

Junto do CSV será gerado `resultados/produtos.csv.tipos.json`. Ele registra os tipos JSON e a soma de verificação do CSV, permitindo reconstruir números, listas, objetos, booleanos, campos ausentes e valores `null` em uma futura conversão de volta. Guarde os dois arquivos juntos.

```bash
python main.py csv-para-json resultados/produtos.csv resultados/produtos_recuperados.json
```

**4. Atualizar um arquivo e comprovar backup**

Para não alterar os dados de demonstração do repositório, primeiro faça uma cópia para a pasta `resultados`:

```bash
python main.py csv-para-json dados/clientes.csv resultados/clientes.json
python main.py atualizar-json resultados/clientes.json 0 cidade Imperatriz
python main.py ler-json resultados/clientes.json
```

O comando de atualização criará um arquivo `resultados/clientes.json.AAAAMMDDTHHMMSSZ.XXXXXXXX.bak` contendo a versão **anterior**.

**5. Observar tratamento de erro**

```bash
python main.py ler-csv dados/inexistente.csv
```

Resultado esperado: mensagem `[ERRO] Arquivo não encontrado: ...` e código de saída 1, sem traceback inesperado.

**6. Ver todos os comandos disponíveis**

```bash
python main.py --help
```

## Executar testes automatizados

```bash
python -m unittest discover -s tests -v
```

São verificados conversão de ida e volta, acentos, zeros à esquerda, tipos JSON, existência e conteúdo do backup, atualização com metadados, CSV malformado, arquivo inexistente, codificação incorreta e JSON inválido.

## Notas sobre integridade

- Dados CSV são lidos como **texto** por padrão: `001` continua `001`. CSV não possui tipos de dados intrínsecos.
- Para manter os tipos JSON na ida e volta, a aplicação cria um arquivo de metadados ao exportar JSON -> CSV. Se o CSV for modificado fora da aplicação, a conferência de integridade impede sua conversão com metadados desatualizados.
- Alterações realizadas pelo comando `atualizar-csv` atualizam também os metadados. O valor textual informado no comando passa a ser string JSON; os demais campos preservam seus tipos anteriores.
- Os backups são criados **antes** da substituição de qualquer arquivo existente. A substituição do arquivo principal utiliza `os.replace` após escrita em arquivo temporário. Os backups não são removidos automaticamente.
- JSON é convertido para CSV quando a raiz é um objeto ou lista não vazia de objetos. Estruturas incompatíveis são rejeitadas com mensagem explicativa, em vez de perder dados silenciosamente.
- Operações envolvendo CSV e seu arquivo auxiliar são gravadas separadamente, não em uma transação única. Em caso de falha entre escritas, restaure os backups correspondentes antes de reconverter.

## Relatório e evidências

Consulte `relatorio/TED03_Relatorio_Gustavo_Kaue.pdf`. O relatório inclui capturas de tela reais do terminal (`evidencias/captura_real_*.png`). Os registros textuais da execução estão em `evidencias/cenario_*.txt`, acompanhados de imagens complementares `.png`.

## Entrega acadêmica

1. Publique esta pasta inteira em um repositório GitHub/GitLab acessível ao professor.
2. Verifique que `main.py`, `dados`, `src`, `tests`, `evidencias`, `README.md` e `relatorio` aparecem no repositório.
3. No Portal do Aluno, envie **o link do repositório**, não apenas o link do relatório.

## Referências

- Python Software Foundation. Documentação de `csv`: https://docs.python.org/3/library/csv.html
- Python Software Foundation. Documentação de `json`: https://docs.python.org/3/library/json.html
- Python Software Foundation. Documentação de `open`: https://docs.python.org/3/library/functions.html#open
- Python Software Foundation. Documentação de `os.replace`: https://docs.python.org/3/library/os.html#os.replace
