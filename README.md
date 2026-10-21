# Lancamento de Notas

Sistema web (Streamlit) que le arquivos CSV ou Excel com as notas dos alunos
e informa se o aluno foi aprovado ou reprovado.

## Regra

As notas vem de 0 a 10.
- Prova = media(NOTA 01, NOTA 02) x 0,8 (vale ate 8)
- TF = media(TF 01, TF 02) x 0,2 (vale ate 2)
- Media final = Prova + TF
- 7,0 ou mais: APROVADO. Abaixo de 7,0: REPROVADO.

## Como usar

1. py -m pip install -r requirements.txt
2. Coloque os arquivos .csv ou .xlsx na pasta dados/
3. py -m streamlit run app.py
4. Abra localhost:8501