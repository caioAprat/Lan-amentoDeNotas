import os, csv, glob
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from datetime import datetime

BANCO_CSV = 'banco_notas.csv'
PASTA_CSVS = 'dados_antigos'

HTML_FORM = """
<!DOCTYPE html>
<html><head><title>Lançamento de Notas</title><meta charset="utf-8"></head>
<body style="font-family: Arial; margin: 40px; background: #f4f4f9;">
    <div style="background: white; padding: 20px; border-radius: 8px; max-width: 500px; margin: auto; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
        <h2>Lançamento de notas</h2>
        <form action="/salvar" method="POST">
            <label>Nome: *</label><br><input type="text" name="nome" required style="width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box;"><br>
            <label>R.A: *</label><br><input type="text" name="ra" required style="width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box;"><br>
            <label>NOTA 01: *</label><br><input type="number" step="0.1" name="nota01" required style="width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box;"><br>
            <input type="submit" value="Enviar" style="background: #673ab7; color: white; border: none; padding: 12px; width: 100%; cursor: pointer; font-weight: bold;">
        </form>
    </div>
</body></html>
"""

def inicializar_banco():
    if not os.path.exists(BANCO_CSV):
        with open(BANCO_CSV, 'w', newline='', encoding='utf-8', errors='ignore') as f:
            writer = csv.writer(f)
            writer.writerow(["Carimbo de data/hora", "Nome:", "R.A", "NOTA 01", "NOTA 02", "TF 01", "TF 02"])
        
        # Junta os 300 CSVs se eles existirem na pasta
        arquivos = glob.glob(f'{PASTA_CSVS}/*.csv')
        for arq in arquivos:
            with open(arq, 'r', encoding='utf-8', errors='ignore') as f_in, open(BANCO_CSV, 'a', newline='', encoding='utf-8') as f_out:
                reader = csv.reader(f_in)
                try: next(reader) # Pula o cabeçalho
                except: pass
                csv.writer(f_out).writerows(reader)

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        inicializar_banco()
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_FORM.encode('utf-8'))

    def do_POST(self):
        if self.path == '/salvar':
            tamanho = int(self.headers.get('Content-Length', 0))
            dados = parse_qs(self.rfile.read(tamanho).decode('utf-8'))
            nome = dados.get('nome', [''])[0]
            ra = dados.get('ra', [''])[0]
            nota01 = dados.get('nota01', [''])[0]
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            with open(BANCO_CSV, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([agora, nome, ra, nota01, "", "", ""])
            
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

if __name__ == '__main__':
    if not os.path.exists(PASTA_CSVS): os.makedirs(PASTA_CSVS)
    server = HTTPServer(('localhost', 5000), RequestHandler)
    print("SISTEMA RODANDO! Acesse: http://localhost:5000")
    server.serve_forever()