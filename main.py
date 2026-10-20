import pandas as pd
from pathlib import Path

COLUNAS_NOTAS = ["NOTA 01", "NOTA 02", "TF 01", "TF 02"]
MEDIA_APROVACAO = 6.0


def carregar_dados(pasta="dados"):
    arquivos = list(Path(pasta).glob("*.csv"))
    if not arquivos:
        print(f"Nenhum CSV encontrado na pasta '{pasta}'.")
        return pd.DataFrame()

    tabelas = []
    for arquivo in arquivos:
        try:
            tabelas.append(pd.read_csv(arquivo))
        except Exception as erro:
            print(f"Erro ao ler {arquivo.name}: {erro}")

    df = pd.concat(tabelas, ignore_index=True)
    print(f"{len(arquivos)} arquivos carregados, {len(df)} registros.")
    return df


def calcular_media(df):
    for col in COLUNAS_NOTAS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Média"] = df[COLUNAS_NOTAS].mean(axis=1).round(2)
    df["Situação"] = df["Média"].apply(
        lambda m: "Aprovado" if m >= MEDIA_APROVACAO else "Reprovado"
    )
    return df


def buscar_por_ra(df, ra):
    resultado = df[df["R.A"].astype(str) == str(ra)]
    if resultado.empty:
        print("Aluno não encontrado.")
    else:
        print(resultado[["Nome:", "R.A"] + COLUNAS_NOTAS + ["Média", "Situação"]].to_string(index=False))


def menu(df):
    while True:
        print("\n=== Lançamento de Notas ===")
        print("1 - Listar todos os alunos")
        print("2 - Buscar aluno por R.A")
        print("3 - Listar aprovados")
        print("4 - Listar reprovados")
        print("5 - Exportar relatório (relatorio.csv)")
        print("0 - Sair")
        opcao = input("Escolha: ").strip()

        if opcao == "1":
            print(df[["Nome:", "R.A", "Média", "Situação"]].to_string(index=False))
        elif opcao == "2":
            buscar_por_ra(df, input("R.A: ").strip())
        elif opcao == "3":
            print(df[df["Situação"] == "Aprovado"][["Nome:", "R.A", "Média"]].to_string(index=False))
        elif opcao == "4":
            print(df[df["Situação"] == "Reprovado"][["Nome:", "R.A", "Média"]].to_string(index=False))
        elif opcao == "5":
            df.to_csv("relatorio.csv", index=False, encoding="utf-8-sig")
            print("relatorio.csv gerado.")
        elif opcao == "0":
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    dados = carregar_dados()
    if not dados.empty:
        dados = calcular_media(dados)
        menu(dados)