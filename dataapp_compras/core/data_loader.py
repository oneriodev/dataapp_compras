# -*- coding: utf-8 -*-
"""
Importação e tratamento de dados (CSV/XLSX).

Contém toda a lógica de leitura de arquivos e limpeza/normalização dos
dados antes de disponibilizá-los para análise: detecção de encoding e
separador, conversão de números no formato brasileiro, remoção de
linhas de total/resumo e expansão de colunas combinadas
(ex: "Categoria : Marca").
"""

import io

import pandas as pd


# ----------------------------------------------------------------------------
# LEITURA DE ARQUIVOS
# ----------------------------------------------------------------------------
def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    """
    Lê um arquivo CSV ou XLSX enviado pelo usuário e retorna um DataFrame.
    Faz um tratamento básico de tipos e nomes de colunas.
    """
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        raw = uploaded_file.read()
        uploaded_file.seek(0)
        df = read_csv_bytes_with_fallback(raw)
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Formato de arquivo não suportado. Use CSV ou XLSX.")

    df = basic_data_cleaning(df)
    return df


def read_csv_bytes_with_fallback(raw: bytes) -> pd.DataFrame:
    """
    Lê os bytes de um CSV tentando diferentes combinações de encoding e
    separador, já que relatórios exportados de ERPs/Excel no Brasil
    costumam vir em Latin-1 / Windows-1252 (não UTF-8) e usar ';' como
    separador. Tenta detectar automaticamente até conseguir ler o arquivo.
    """
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1"]
    ultimo_erro = None

    for encoding in encodings:
        try:
            # sep=None + engine="python" deixa o pandas detectar o separador (',' ou ';')
            df = pd.read_csv(io.BytesIO(raw), sep=None, engine="python", encoding=encoding)
            return df
        except (UnicodeDecodeError, UnicodeError) as e:
            ultimo_erro = e
            continue
        except Exception:
            # Se a detecção automática de separador falhar, tenta separador ';' fixo
            try:
                df = pd.read_csv(io.BytesIO(raw), sep=";", encoding=encoding)
                return df
            except (UnicodeDecodeError, UnicodeError) as e:
                ultimo_erro = e
                continue
            except Exception as e:
                ultimo_erro = e
                continue

    raise ValueError(
        f"Não foi possível ler o arquivo CSV com nenhum encoding testado "
        f"(utf-8, cp1252, latin1). Erro original: {ultimo_erro}"
    )


# ----------------------------------------------------------------------------
# TRATAMENTO / LIMPEZA DE DADOS
# ----------------------------------------------------------------------------
def is_text_column(series: pd.Series) -> bool:
    """
    Verifica se uma coluna deve ser tratada como texto (não numérica e não data).
    Não usa comparação direta de dtype == object porque, dependendo da versão
    do pandas, colunas de texto podem vir com dtype 'str'/'string' em vez de
    'object' — usar is_numeric_dtype/is_datetime64_any_dtype é mais robusto.
    """
    return not (
        pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series)
    )


def convert_br_numeric_series(series: pd.Series):
    """
    Tenta converter uma série de texto para número, assumindo o padrão
    brasileiro (ponto como separador de milhar, vírgula como decimal, ex:
    '1.234,56'). Retorna a série convertida se pelo menos 60% dos valores
    não-vazios forem convertidos com sucesso; caso contrário, retorna None
    (mantendo a coluna como texto).
    """
    texto = series.astype(str).str.strip()
    nao_vazios = texto != ""
    if not nao_vazios.any():
        return None

    limpo = (
        texto.str.replace("%", "", regex=False)
        .str.replace(".", "", regex=False)  # remove separador de milhar
        .str.replace(",", ".", regex=False)  # vírgula decimal -> ponto
    )
    convertido = pd.to_numeric(limpo, errors="coerce")

    taxa_sucesso = convertido[nao_vazios].notna().mean()
    if taxa_sucesso >= 0.6:
        return convertido
    return None


def remove_summary_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove linhas de rodapé/resumo comuns em relatórios de BI exportados
    (ex: 'TOTAL: 422 linhas'), identificadas por começarem com 'total'
    em qualquer coluna de texto. Essas linhas, se mantidas, duplicam os
    valores nos somatórios das métricas.
    """
    if df.empty:
        return df
    mascara_total = pd.Series(False, index=df.index)
    for col in df.columns:
        try:
            valores = df[col].astype(str).str.strip().str.lower()
            mascara_total = mascara_total | valores.str.startswith("total")
        except Exception:
            continue
    if mascara_total.any():
        df = df.loc[~mascara_total].copy()
    return df


def expand_combined_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Alguns relatórios de BI trazem duas informações combinadas em uma única
    coluna, separadas por ':' — por exemplo, uma coluna chamada
    'Categoria : Marca' com valores como '01 - ALIMENTO : 3 CORACOES'.
    Esta função detecta esse padrão pelo nome da coluna e cria duas novas
    colunas (ex: 'Categoria' e 'Marca'), mantendo a coluna original para
    quem preferir usá-la como identificador de produto/item mais granular.
    """
    df = df.copy()
    for col in list(df.columns):
        if ":" not in col or not is_text_column(df[col]):
            continue
        partes_nome = [p.strip() for p in col.split(":", 1)]
        if len(partes_nome) != 2 or not all(partes_nome):
            continue

        dividido = df[col].astype(str).str.split(":", n=1, expand=True)
        if dividido.shape[1] != 2:
            continue

        nome_col_1, nome_col_2 = partes_nome
        if nome_col_1 in df.columns:
            nome_col_1 = f"{nome_col_1} (auto)"
        if nome_col_2 in df.columns:
            nome_col_2 = f"{nome_col_2} (auto)"

        df[nome_col_1] = dividido[0].str.strip()
        df[nome_col_2] = dividido[1].str.strip()
    return df


def basic_data_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tratamento básico dos dados:
    - Remove espaços em branco extras dos nomes de colunas.
    - Remove linhas de total/resumo (ex: 'TOTAL: 422 linhas').
    - Remove linhas totalmente vazias.
    - Converte colunas numéricas no formato brasileiro (1.234,56).
    - Expande colunas combinadas do tipo 'Categoria : Marca'.
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = remove_summary_rows(df)
    df = df.dropna(how="all")

    for col in df.columns:
        if not is_text_column(df[col]):
            continue
        convertido = convert_br_numeric_series(df[col])
        if convertido is not None:
            df[col] = convertido

    df = expand_combined_columns(df)
    return df


# ----------------------------------------------------------------------------
# SUGESTÃO AUTOMÁTICA DE MAPEAMENTO DE COLUNAS
# ----------------------------------------------------------------------------
def auto_suggest_column_mapping(colunas: list) -> dict:
    """
    Sugere automaticamente o mapeamento de colunas com base em palavras-chave
    comuns em relatórios de BI de vendas (ex: 'Venda Valor' -> faturamento).
    A sugestão é só um ponto de partida; o usuário pode ajustar livremente
    na barra lateral.
    """
    def buscar(*termos):
        # 1ª passada: nome de coluna igual (exato) a algum termo — evita que
        # uma coluna combinada como "Categoria : Marca" seja escolhida no
        # lugar da coluna "Marca" isolada, só porque contém a palavra "marca".
        for termo in termos:
            for c in colunas:
                if c.lower().strip() == termo:
                    return c
        # 2ª passada: correspondência parcial (substring)
        for termo in termos:
            for c in colunas:
                if termo in c.lower():
                    return c
        return None

    sugestao = {
        "marca": buscar("marca"),
        "quantidade": buscar("venda quantidade", "quantidade vendida", "qtd venda", "quantidade"),
        "faturamento": buscar("venda valor", "faturamento", "valor venda", "valor de venda"),
        "custo": buscar("custo bruto", "custo líquido", "custo liquido", "custo"),
        "custo_liquido": buscar("custo líquido", "custo liquido"),
        "imposto": buscar("imposto", "impostos", "tributo", "tributos"),
    }
    produto = buscar("produto", "descrição", "descricao", "item")
    if not produto:
        # Fallback: usa uma coluna combinada (ex: "Categoria : Marca") como
        # identificador de item, quando não existe uma coluna "Produto" isolada.
        produto = next((c for c in colunas if ":" in c), None)
    sugestao["produto"] = produto
    return sugestao
