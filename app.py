import re
import unicodedata
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Lancamento de Notas", layout="wide")

PASTA = Path("dados")
PASTA.mkdir(exist_ok=True)

PROVAS = ["NOTA 01", "NOTA 02"]
TFS = ["TF 01", "TF 02"]
NOTAS = PROVAS + TFS
OBRIGATORIAS = ["Nome", "R.A"] + NOTAS

# Notas dos arquivos vem de 0 a 10.
# Prova = media(NOTA 01, NOTA 02) x 0,8 (vale 8)
# TF = media(TF 01, TF 02) x 0,2 (vale 2)
# Media final = Prova + TF ; aprovado se >= 7
NOTA_BASE = 10.0
MAX_PROVA = 8.0
MAX_TF = 2.0
NOTA_MAXIMA = MAX_PROVA + MAX_TF
MEDIA_APROVACAO = 7.0

PESO_NOTA = {
    "NOTA 01": MAX_PROVA / NOTA_BASE / 2,
    "NOTA 02": MAX_PROVA / NOTA_BASE / 2,
    "TF 01": MAX_TF / NOTA_BASE / 2,
    "TF 02": MAX_TF / NOTA_BASE / 2,
}

VERDE = "#28a745"
VERMELHO = "#dc3545"
AMARELO = "#d39e00"

ESTILO = {
    "Aprovado": (VERDE, "APROVADO"),
    "Reprovado": (VERMELHO, "REPROVADO"),
    "Incompleto": (AMARELO, "NOTAS INCOMPLETAS"),
}

ALIASES = {
    "Nome": ["nome", "nomedoaluno", "aluno", "nomecompleto"],
    "R.A": ["ra", "registroacademico", "matricula"],
    "NOTA 01": ["nota01", "nota1", "n1"],
    "NOTA 02": ["nota02", "nota2", "n2"],
    "TF 01": ["tf01", "tf1"],
    "TF 02": ["tf02", "tf2"],
    "Data": ["carimbodedatahora", "datahora", "data"],
}

CSS = """
<style>
.nt-card{background:rgba(128,128,128,0.10);border:1px solid rgba(128,128,128,0.28);border-radius:16px;padding:20px 22px;margin-bottom:16px;}
.nt-alto{min-height:215px;}
.nt-perfil{display:flex;align-items:center;gap:18px;flex-wrap:wrap;}
.nt-avatar{width:76px;height:76px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:700;color:#fff;flex-shrink:0;}
.nt-nome{font-size:30px;font-weight:700;line-height:1.15;}
.nt-ra{opacity:0.7;font-size:15px;margin-top:4px;}
.nt-selo{margin-left:auto;padding:10px 26px;border-radius:999px;font-weight:800;font-size:18px;letter-spacing:1px;color:#fff;}
.nt-titulo{font-size:13px;text-transform:uppercase;letter-spacing:1px;opacity:0.65;margin-bottom:6px;}
.nt-media{font-size:56px;font-weight:800;line-height:1.05;}
.nt-msg{font-size:16px;margin-top:10px;}
.nt-barra{position:relative;height:14px;border-radius:999px;background:rgba(128,128,128,0.25);margin-top:18px;}
.nt-barra-fill{height:100%;border-radius:999px;}
.nt-marca{position:absolute;top:-5px;width:3px;height:24px;background:#f1c40f;border-radius:2px;margin-left:-1px;}
.nt-legenda{display:flex;justify-content:space-between;font-size:12px;opacity:0.7;margin-top:10px;}
.nt-grade{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin-bottom:8px;}
.nt-grade .nt-card{margin-bottom:0;padding:16px 18px;}
.nt-nota-valor{font-size:40px;font-weight:800;line-height:1.1;}
.nt-max{font-size:16px;font-weight:600;opacity:0.6;}
.nt-mini{height:8px;border-radius:999px;background:rgba(128,128,128,0.25);margin:10px 0 8px 0;}
.nt-mini-fill{height:100%;border-radius:999px;}
.nt-turma{font-size:13px;opacity:0.85;}
.nt-formula{font-family:monospace;font-size:17px;padding:12px 16px;border-radius:10px;background:rgba(128,128,128,0.15);display:block;margin-top:8px;}
</style>
"""


def html_linha(texto):
    return "".join(linha.strip() for linha in texto.strip().splitlines())


def mostrar_html(texto):
    st.markdown(html_linha(texto), unsafe_allow_html=True)


def padronizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def ler_tabela(arquivo):
    if arquivo.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(arquivo, dtype=str)
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(arquivo, sep=None, engine="python", encoding=enc, dtype=str)
        except UnicodeDecodeError:
            continue
    raise ValueError("codificacao do arquivo nao reconhecida")


def padronizar_colunas(tabela):
    renomear = {}
    usados = set()
    for col in tabela.columns:
        p = padronizar(col)
        for destino, lista in ALIASES.items():
            if p in lista and destino not in usados:
                renomear[col] = destino
                usados.add(destino)
                break
    return tabela.rename(columns=renomear)


def fmt(valor):
    return "-" if pd.isna(valor) else f"{valor:.2f}".replace(".", ",")


def fmt_nota(valor):
    if pd.isna(valor):
        return "-"
    texto = f"{valor:.2f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def fmt_delta(valor):
    return f"{valor:+.2f}".replace(".", ",")


def carregar_dados():
    arquivos = sorted(
        a for a in PASTA.iterdir()
        if a.suffix.lower() in (".csv", ".xlsx", ".xls") and not a.name.startswith("relatorio")
    )
    tabelas, erros = [], []

    for arquivo in arquivos:
        try:
            tabela = padronizar_colunas(ler_tabela(arquivo))
            faltando = [c for c in OBRIGATORIAS if c not in tabela.columns]
            if faltando:
                erros.append(
                    arquivo.name + ": faltam as colunas " + ", ".join(faltando)
                    + " | colunas encontradas: " + ", ".join(str(c) for c in tabela.columns)
                )
                continue
            tabelas.append(tabela)
        except Exception as e:
            erros.append(arquivo.name + ": " + str(e))

    if not tabelas:
        return pd.DataFrame(), len(arquivos), erros, 0, pd.DataFrame()

    df = pd.concat(tabelas, ignore_index=True)
    df["Nome"] = df["Nome"].fillna("").astype(str).str.strip()
    df["R.A"] = df["R.A"].fillna("").astype(str).str.strip()
    df = df[df["R.A"] != ""]

    for col in NOTAS:
        df[col] = pd.to_numeric(
            df[col].fillna("").astype(str).str.strip().str.replace(",", ".", regex=False),
            errors="coerce",
        )

    antes = len(df)
    if "Data" in df.columns:
        df["_data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
        df = df.sort_values("_data").drop(columns="_data")
    df = df.drop_duplicates(subset="R.A", keep="last").reset_index(drop=True)
    duplicados = antes - len(df)

    # Notas fora de 0 a 10 sao desconsideradas (aluno fica Incompleto) e listadas
    linhas_invalidas = []
    for n in NOTAS:
        mask = (df[n] > NOTA_BASE + 1e-9) | (df[n] < 0)
        for i in df.index[mask]:
            linhas_invalidas.append(
                {"Nome": df.at[i, "Nome"], "R.A": df.at[i, "R.A"], "Campo": n, "Valor no arquivo": df.at[i, n]}
            )
        df.loc[mask, n] = float("nan")
    invalidos = pd.DataFrame(linhas_invalidas)

    df["Média provas"] = df[PROVAS].sum(axis=1, min_count=2) / 2
    df["Média TFs"] = df[TFS].sum(axis=1, min_count=2) / 2
    df["Prova"] = df["Média provas"] / NOTA_BASE * MAX_PROVA
    df["TF"] = df["Média TFs"] / NOTA_BASE * MAX_TF
    df["Média"] = (df["Prova"] + df["TF"]).round(6)
    df["Situação"] = df["Média"].apply(
        lambda m: "Incompleto" if pd.isna(m)
        else ("Aprovado" if m >= MEDIA_APROVACAO else "Reprovado")
    )
    return df, len(arquivos), erros, duplicados, invalidos


def cor_situacao(valor):
    if valor == "Aprovado":
        return "background-color: #1e7e34; color: white; font-weight: bold"
    if valor == "Reprovado":
        return "background-color: #c82333; color: white; font-weight: bold"
    return "background-color: #b58900; color: white; font-weight: bold"


def iniciais(nome):
    partes = [p for p in nome.split() if p]
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][0].upper()
    return (partes[0][0] + partes[-1][0]).upper()


def mensagem_situacao(aluno):
    media = aluno["Média"]
    situacao = aluno["Situação"]

    if situacao == "Aprovado":
        folga = media - MEDIA_APROVACAO
        if folga < 0.005:
            return "Passou no limite: a média final ficou exatamente em " + fmt(MEDIA_APROVACAO) + "."
        return "Passou com " + fmt(folga) + " ponto(s) acima do mínimo de " + fmt(MEDIA_APROVACAO) + "."

    if situacao == "Reprovado":
        falta = MEDIA_APROVACAO - media
        return "Ficou " + fmt(falta) + " ponto(s) abaixo do mínimo de " + fmt(MEDIA_APROVACAO) + " na média final."

    faltam = [n for n in NOTAS if pd.isna(aluno[n])]
    conhecido = sum(aluno[n] * PESO_NOTA[n] for n in NOTAS if pd.notna(aluno[n]))
    maximo_restante = sum(NOTA_BASE * PESO_NOTA[n] for n in faltam)
    precisa = MEDIA_APROVACAO - conhecido
    base = "Notas que faltam: " + ", ".join(faltam) + ". "
    if precisa <= 0:
        return base + "Com as notas já lançadas o aluno já garante a aprovação."
    if precisa > maximo_restante + 1e-9:
        return base + "Mesmo com nota 10 nelas, não é possível chegar à média " + fmt(MEDIA_APROVACAO) + "."
    return (
        base + "Para ser aprovado, as notas que faltam precisam render " + fmt_nota(precisa)
        + " ponto(s) na média final (máximo possível: " + fmt_nota(maximo_restante) + ")."
    )


def html_nota(nome, valor, maximo, media_turma):
    if pd.isna(valor):
        pct, cor, valor_txt = 0.0, AMARELO, "-"
    else:
        pct = max(0.0, min(valor / maximo * 100, 100.0))
        cor = VERDE if valor >= maximo * MEDIA_APROVACAO / NOTA_MAXIMA else VERMELHO
        valor_txt = fmt_nota(valor)

    if pd.isna(media_turma):
        turma = "Turma: sem dados"
    elif pd.isna(valor):
        turma = "Turma: " + fmt(media_turma)
    else:
        d = valor - media_turma
        cor_d = VERDE if d >= 0 else VERMELHO
        turma = (
            "Turma: " + fmt(media_turma)
            + ' <span style="color:' + cor_d + ';font-weight:700">(' + fmt_delta(d) + ")</span>"
        )

    return f"""
    <div class="nt-card">
    <div class="nt-titulo">{nome}</div>
    <div class="nt-nota-valor" style="color:{cor}">{valor_txt} <span class="nt-max">/ {fmt_nota(maximo)}</span></div>
    <div class="nt-mini"><div class="nt-mini-fill" style="width:{pct:.0f}%;background:{cor}"></div></div>
    <div class="nt-turma">{turma}</div>
    </div>
    """


def resumo_turma(df):
    st.info("Selecione um aluno acima para ver o boletim completo.")
    completos = df[df["Média"].notna()]
    aprovados = int((df["Situação"] == "Aprovado").sum())
    taxa = aprovados / len(completos) * 100 if len(completos) > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Alunos na turma", len(df))
    c2.metric("Média da turma", fmt(completos["Média"].mean()))
    c3.metric("Taxa de aprovação", f"{taxa:.0f}%")
    c4.metric("Maior média", fmt(completos["Média"].max()))


def tela_consulta(df):
    mostrar_html(CSS)
    st.subheader("Consulta de notas")

    ordenado = df.sort_values("Nome", key=lambda s: s.str.lower())
    opcoes = {}
    for i, r in ordenado.iterrows():
        opcoes[r["Nome"] + "  -  R.A " + r["R.A"]] = i

    escolha = st.selectbox(
        "Buscar aluno (digite o nome ou o R.A)",
        list(opcoes),
        index=None,
        placeholder="Comece a digitar o nome ou o R.A...",
        key="aluno_escolhido",
    )

    if escolha is None:
        resumo_turma(df)
        return

    idx = opcoes[escolha]
    aluno = df.loc[idx]
    nome = aluno["Nome"] if aluno["Nome"] else "(sem nome)"
    ra = escape(str(aluno["R.A"]))
    situacao = aluno["Situação"]
    cor, selo = ESTILO[situacao]
    media = aluno["Média"]

    completos = df[df["Média"].notna()]
    media_turma = completos["Média"].mean() if len(completos) > 0 else float("nan")
    medias_cols = {n: df[n].mean() for n in NOTAS + ["Prova", "TF"]}

    if pd.notna(media):
        pct = max(0.0, min(media / NOTA_MAXIMA * 100, 100.0))
        media_txt = fmt(media)
    else:
        pct = 0.0
        media_txt = "-"
    marca = MEDIA_APROVACAO / NOTA_MAXIMA * 100
    msg = escape(mensagem_situacao(aluno))
    nome_html = escape(nome)
    ini = escape(iniciais(nome))

    mostrar_html(f"""
    <div class="nt-card nt-perfil">
    <div class="nt-avatar" style="background:{cor}">{ini}</div>
    <div>
    <div class="nt-nome">{nome_html}</div>
    <div class="nt-ra">R.A {ra}</div>
    </div>
    <div class="nt-selo" style="background:{cor}">{selo}</div>
    </div>
    """)

    col1, col2 = st.columns([3, 2])

    with col1:
        mostrar_html(f"""
        <div class="nt-card nt-alto">
        <div class="nt-titulo">Média final (Prova + TF)</div>
        <div class="nt-media" style="color:{cor}">{media_txt}</div>
        <div class="nt-msg">{msg}</div>
        <div class="nt-barra">
        <div class="nt-barra-fill" style="width:{pct:.1f}%;background:{cor}"></div>
        <div class="nt-marca" style="left:{marca:.1f}%"></div>
        </div>
        <div class="nt-legenda"><span>0</span><span>Linha amarela: mínimo {fmt(MEDIA_APROVACAO)}</span><span>{fmt_nota(NOTA_MAXIMA)}</span></div>
        </div>
        """)

    with col2:
        if pd.notna(media):
            posicao = int((completos["Média"] > media).sum()) + 1
            diff = media - media_turma
            cor_d = VERDE if diff >= 0 else VERMELHO
            mostrar_html(f"""
            <div class="nt-card nt-alto">
            <div class="nt-titulo">Posição na turma</div>
            <div class="nt-media">{posicao}º</div>
            <div class="nt-msg">de {len(completos)} alunos com notas completas</div>
            <div class="nt-msg">Média da turma: <b>{fmt(media_turma)}</b> <span style="color:{cor_d};font-weight:700">({fmt_delta(diff)})</span></div>
            </div>
            """)
        else:
            mostrar_html(f"""
            <div class="nt-card nt-alto">
            <div class="nt-titulo">Posição na turma</div>
            <div class="nt-media" style="opacity:0.5">-</div>
            <div class="nt-msg">Indisponível: o aluno ainda não tem as 4 notas válidas.</div>
            <div class="nt-msg">Média da turma: <b>{fmt(media_turma)}</b></div>
            </div>
            """)

    st.markdown("#### Resultado por componente")
    comp = (
        html_nota("Prova (vale até 8)", aluno["Prova"], MAX_PROVA, medias_cols["Prova"])
        + html_nota("TF (vale até 2)", aluno["TF"], MAX_TF, medias_cols["TF"])
    )
    mostrar_html('<div class="nt-grade">' + comp + "</div>")

    st.markdown("#### Notas lançadas (0 a 10)")
    cartoes = "".join(html_nota(n, aluno[n], NOTA_BASE, medias_cols[n]) for n in NOTAS)
    mostrar_html('<div class="nt-grade">' + cartoes + "</div>")
    st.caption("Verde: nota igual ou acima de 7. A aprovação depende da média final (Prova + TF), não de cada nota isolada.")

    p1, p2 = fmt_nota(aluno["NOTA 01"]), fmt_nota(aluno["NOTA 02"])
    t1, t2 = fmt_nota(aluno["TF 01"]), fmt_nota(aluno["TF 02"])
    mp, mt = fmt(aluno["Média provas"]), fmt(aluno["Média TFs"])
    prova_txt, tf_txt = fmt(aluno["Prova"]), fmt(aluno["TF"])
    mostrar_html(f"""
    <div class="nt-card">
    <div class="nt-titulo">Como a média foi calculada</div>
    <span class="nt-formula">Média das provas = ({p1} + {p2}) ÷ 2 = {mp}</span>
    <span class="nt-formula">Prova = {mp} × 0,8 = {prova_txt} (vale até {fmt_nota(MAX_PROVA)})</span>
    <span class="nt-formula">Média dos TFs = ({t1} + {t2}) ÷ 2 = {mt}</span>
    <span class="nt-formula">TF = {mt} × 0,2 = {tf_txt} (vale até {fmt_nota(MAX_TF)})</span>
    <span class="nt-formula">Média final = {prova_txt} + {tf_txt} = {media_txt}</span>
    <div class="nt-msg">Regra: média final de {fmt(MEDIA_APROVACAO)} ou mais = aprovado. Abaixo disso = reprovado.</div>
    </div>
    """)

    if len(completos) > 0:
        with st.expander("Ver ranking da turma (10 maiores médias)"):
            ranking = completos.sort_values("Média", ascending=False).copy()
            ranking.insert(0, "Pos.", ranking["Média"].rank(method="min", ascending=False).astype(int))
            ranking = ranking.head(10)[["Pos.", "Nome", "R.A", "Média", "Situação"]]
            st.dataframe(
                ranking.style.map(cor_situacao, subset=["Situação"]).format({"Média": "{:.2f}"}),
                width="stretch",
                hide_index=True,
            )

    colunas = ["Nome", "R.A"] + NOTAS + ["Prova", "TF", "Média", "Situação"]
    st.download_button(
        "Baixar boletim deste aluno (CSV)",
        df.loc[[idx]][colunas].round(2).to_csv(index=False).encode("utf-8-sig"),
        file_name="boletim_" + str(aluno["R.A"]) + ".csv",
        mime="text/csv",
        key="baixar_boletim",
    )


def tela_aprovacao(df):
    st.subheader("Aprovados e reprovados")
    st.caption(
        "Notas de 0 a 10. Prova = média(NOTA 01, NOTA 02) × 0,8 (vale 8). "
        "TF = média(TF 01, TF 02) × 0,2 (vale 2). "
        "Média final = Prova + TF. 7,0 ou mais = aprovado."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Alunos", len(df))
    c2.metric("Aprovados", int((df["Situação"] == "Aprovado").sum()))
    c3.metric("Reprovados", int((df["Situação"] == "Reprovado").sum()))
    c4.metric("Incompletos", int((df["Situação"] == "Incompleto").sum()))

    situacao = st.radio(
        "Mostrar", ["Todos", "Aprovado", "Reprovado", "Incompleto"], horizontal=True, key="filtro"
    )
    busca = st.text_input("Filtrar por nome ou R.A", key="filtro_busca")

    filtrado = df if situacao == "Todos" else df[df["Situação"] == situacao]
    if busca:
        t = busca.strip()
        filtrado = filtrado[
            filtrado["Nome"].str.contains(t, case=False, na=False, regex=False)
            | filtrado["R.A"].str.contains(t, na=False, regex=False)
        ]

    colunas = ["Nome", "R.A"] + NOTAS + ["Prova", "TF", "Média", "Situação"]
    tabela = (
        filtrado[colunas]
        .style.map(cor_situacao, subset=["Situação"])
        .format({"Prova": "{:.2f}", "TF": "{:.2f}", "Média": "{:.2f}"}, na_rep="-")
    )
    st.dataframe(tabela, width="stretch", hide_index=True)

    st.download_button(
        "Baixar relatorio (CSV)",
        filtrado[colunas].round(2).to_csv(index=False).encode("utf-8-sig"),
        file_name="relatorio.csv",
        mime="text/csv",
    )


def tela_envio():
    st.subheader("Entrada de dados")
    st.write("Escolha os arquivos (CSV ou Excel, pode selecionar varios) e clique em Salvar.")
    enviados = st.file_uploader(
        "Arquivos", type=["csv", "xlsx"], accept_multiple_files=True, key="uploader"
    )
    if enviados and st.button("Salvar arquivos enviados", key="salvar"):
        for f in enviados:
            (PASTA / f.name).write_bytes(f.getbuffer())
        st.success(
            str(len(enviados))
            + " arquivo(s) salvo(s) na pasta dados. Clique em Recarregar dados na barra lateral."
        )


def principal():
    st.title("Lancamento de Notas")

    if st.sidebar.button("Recarregar dados"):
        st.rerun()

    df, qtd_arquivos, erros, duplicados, invalidos = carregar_dados()

    st.sidebar.write("Arquivos na pasta: " + str(qtd_arquivos))
    st.sidebar.write("Alunos carregados: " + str(len(df)))
    if duplicados:
        st.sidebar.write("Registros repetidos descartados: " + str(duplicados))

    if erros:
        st.warning(str(len(erros)) + " arquivo(s) com problema:")
        for e in erros:
            st.write(e)

    if not invalidos.empty:
        with st.expander(
            "⚠️ " + str(len(invalidos)) + " nota(s) fora da faixa de 0 a 10 foram desconsideradas "
            "(o aluno aparece como Incompleto). Clique para ver quais."
        ):
            st.dataframe(invalidos, width="stretch", hide_index=True)

    aba1, aba2, aba3 = st.tabs(["Consultar aluno", "Aprovação", "Enviar arquivos"])

    with aba1:
        if df.empty:
            st.info("Nenhum dado carregado ainda. Use a aba Enviar arquivos ou coloque os arquivos na pasta dados.")
        else:
            tela_consulta(df)

    with aba2:
        if df.empty:
            st.info("Nenhum dado carregado ainda.")
        else:
            tela_aprovacao(df)

    with aba3:
        tela_envio()


try:
    principal()
except Exception as erro:
    st.error("Ocorreu um erro no sistema:")
    st.exception(erro)