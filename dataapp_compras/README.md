# 🛒 DataApp Compras — Setor de Compras (Supermercado)

Protótipo em **Streamlit** para análise de métricas de vendas voltado ao
setor de Compras de uma rede de supermercados. Foi desenhado para consumir
relatórios de BI exportados de ERPs de varejo (testado e ajustado
especificamente para o **Consinco/TOTVS**), já filtrados por período na
origem — por isso o app não trabalha com colunas de data.

O objetivo é dar ao time de Compras uma visão rápida de rentabilidade,
concentração de faturamento e itens problemáticos, sem depender de
planilhas manuais ou relatórios estáticos.

## ✨ Principais recursos

- **Importação flexível**: aceita CSV ou XLSX, com detecção automática de
  encoding (UTF-8, Latin-1/cp1252) e separador — cobre a maioria dos
  relatórios exportados de ERPs brasileiros.
- **Tratamento automático de dados**: conversão de números no formato
  brasileiro (`1.234,56`), remoção de linhas de total/rodapé, e separação
  automática de colunas combinadas (ex.: `"Categoria : Marca"` vira duas
  colunas).
- **Mapeamento de colunas assistido**: a aplicação sugere automaticamente
  qual coluna do seu arquivo corresponde a Produto, Marca, Quantidade,
  Faturamento, Custo, Custo Líquido e Imposto — e você pode ajustar
  livremente se a sugestão errar.
- **Indicadores gerais**: faturamento, lucro, margem bruta, total e média
  de vendas, com comparativo opcional de margem bruta vs. margem sobre
  Custo Líquido (mostra o efeito de impostos/descontos já embutidos no
  ERP).
- **Rankings Top 5**: produtos e marcas mais vendidos e mais lucrativos.
- **Curva ABC**: classificação de produtos ou marcas por concentração de
  faturamento (A = até 80% acumulado, B = até 95%, C = restante).
- **Detecção de margem negativa**: identifica itens vendidos abaixo do
  custo (prejuízo), cruzando com volume de vendas para priorizar os casos
  mais críticos.
- **Aba "Maiores Gastos"**: produtos com maior Custo Líquido e marcas com
  maior carga de Impostos.
- **Relatório de Insights**: botão que gera uma síntese textual objetiva
  cruzando achados de todas as abas (ex.: um item que está entre os mais
  vendidos e ao mesmo tempo com margem negativa vira um alerta único),
  com recomendação de ação — exportável em `.txt`.
- **Persistência local**: os dados tratados podem ser salvos em um banco
  SQLite local, permitindo recarregar a análise sem reenviar o arquivo.

## 🧱 Stack técnica

| Camada          | Tecnologia        |
|-----------------|--------------------|
| Interface       | [Streamlit](https://streamlit.io) |
| Manipulação de dados | [pandas](https://pandas.pydata.org), [NumPy](https://numpy.org) |
| Gráficos        | [Plotly Express](https://plotly.com/python/plotly-express/) |
| Banco de dados  | [SQLAlchemy](https://www.sqlalchemy.org) + SQLite |
| Leitura de Excel | [openpyxl](https://openpyxl.readthedocs.io) |

## 📂 Estrutura do projeto

dataapp_compras/
├── app.py # Ponto de entrada: configura a página e monta a interface
├── requirements.txt
├── README.md
├── core/ # Lógica de negócio (sem dependência de UI)
│ ├── config.py # Constantes (caminho do banco, nome da tabela)
│ ├── database.py # Conexão SQLAlchemy/SQLite (salvar, carregar, limpar)
│ ├── data_loader.py # Leitura de CSV/XLSX, limpeza e sugestão de mapeamento
│ ├── metrics.py # KPIs, rankings Top N, Curva ABC e margem negativa
│ ├── insights.py # Síntese textual dos achados (usada na aba Relatório)
│ ├── state.py # Inicialização e reset do st.session_state
│ └── charts.py # Funções de gráficos Plotly reutilizáveis
└── ui/ # Componentes de interface (Streamlit)
├── sidebar.py # Barra lateral: importação, modelagem, salvar/resetar
├── tab_produtos.py # Aba "Produtos / Visão Geral"
├── tab_maiores_gastos.py # Aba "Maiores Gastos"
├── tab_relatorio.py # Aba "Relatório" (insights textuais)
└── tab_dados.py # Aba "Dados" (tabela + exportação)


A separação segue uma regra simples: tudo em `core/` funciona sem
depender de Streamlit (fácil de testar isoladamente); tudo em `ui/` cuida
apenas de exibir e coletar interação do usuário, chamando as funções de
`core/`. `app.py` só orquestra as duas camadas.

## 🚀 Como rodar

### Pré-requisitos
- Python 3.10+
- pip

### Passo a passo

1. Clone o repositório e entre na pasta:
```bash
   git clone <url-do-seu-repositorio>
   cd dataapp_compras
```
2. (Opcional, recomendado) Crie um ambiente virtual:
```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Linux/Mac
```
3. Instale as dependências:
```bash
   pip install -r requirements.txt
```
4. Rode a aplicação (sempre a partir da raiz do projeto, onde está o `app.py`):
```bash
   streamlit run app.py
```
5. O Streamlit abre automaticamente no navegador (geralmente em
   `http://localhost:8501`).

## 📖 Como usar

1. **Importação**: envie um arquivo CSV ou XLSX na barra lateral.
2. **Modelagem**: selecione as colunas que deseja manter na análise e, em
   seguida, mapeie qual coluna representa cada informação: **Produto**,
   **Marca**, **Quantidade vendida**, **Faturamento**, **Custo**, **Custo
   Líquido** e **Imposto**. A aplicação já tenta sugerir esse mapeamento
   automaticamente ao carregar o arquivo. Custo Líquido e Imposto são
   opcionais — só habilitam a aba "Maiores Gastos" e o comparativo de
   margem.
3. **Salvar no banco**: persiste os dados tratados em SQLite local
   (`dataapp_compras.db`), permitindo recarregar a análise depois sem
   reenviar o arquivo.
4. **Resetar análise**: limpa seleções, filtros e o banco local, para
   começar do zero.
5. **Navegue pelas abas**:
   - **📦 Produtos / Visão Geral** — indicadores gerais, comparativo de
     margem, rankings Top 5, Curva ABC e produtos com margem negativa.
   - **💸 Maiores Gastos** — produtos com maior Custo Líquido e marcas
     com maior carga tributária.
   - **📋 Relatório** — clique em "Gerar relatório" para uma síntese
     textual com recomendações de ação, exportável em `.txt`.
   - **🗂️ Dados** — tabela dos dados selecionados, com exportação em CSV.

## ⚠️ Observações e limitações conhecidas

- O tratamento numérico assume **formato brasileiro** (`1.234,56`). Um
  arquivo com números em formato americano (`1,234.56`) será convertido
  incorretamente sem aviso — verifique a origem dos dados antes de
  confiar nos números caso o arquivo não venha de um ERP nacional.
- Linhas de rodapé/total (ex.: `"TOTAL: 422 linhas"`) são detectadas e
  removidas automaticamente para não inflar os somatórios.
- Colunas combinadas no formato `"Categoria : Marca"` são detectadas pelo
  nome e separadas automaticamente em duas colunas.
- O app **não trabalha com datas nem calcula tendência de vendas ao longo
  do tempo** — os relatórios de origem já vêm filtrados por período na
  extração do ERP.
- A Curva ABC usa os cortes padrão de mercado (80% / 95% acumulados).
- "Produtos com Margem Negativa" identifica itens cujo faturamento ficou
  abaixo do custo (prejuízo), cruzando com o ranking de vendas para
  destacar os casos de maior impacto.

## 🗺️ Possíveis próximos passos

- Opção de formato numérico (brasileiro vs. internacional) selecionável
  na interface, para suportar arquivos de outras origens além do
  Consinco.
- Exibição de Custo Líquido Total e Lucro sobre Custo Líquido como
  métricas visíveis (hoje calculados internamente, mas não exibidos).
- Exportação do Relatório de Insights em outros formatos além de `.txt`.

## 👤 Autor

Desenvolvido por **Onerio Ramos** como projeto de portfólio, aplicando Data
Science e desenvolvimento back-end a um problema real do setor de Compras
em varejo supermercadista.