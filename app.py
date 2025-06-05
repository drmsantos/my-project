from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from utils import ler_configuracoes_arquivo, ajustar_imagens_pptx
import os
import threading
import subprocess
import sys

app = Flask(__name__)

logs = []
logs_lock = threading.Lock()
executando = threading.Event()
app.secret_key = "segredo"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Scripts para coleta OpenSearch
caminhos_scripts = {
    'barra': '/home/operador/my-project/Api-BarOpenSearch.py',
    'funcionario': '/home/operador/my-project/Api-FunOpenSearch.py',
    'palmeiras': '/home/operador/my-project/Api-PalOpenSearch.py',
    'jaguare': '/home/operador/my-project/Api-JagOpenSearch.py'
}

# Scripts para ElasticSearch
caminhos_elastic = {
    'barelastic': '/home/operador/my-project/Api-BarElastic.py',
    'funelastic': '/home/operador/my-project/Api-FunElastic.py',
    'palelastic': '/home/operador/my-project/Api-PalElastic.py',
    'jagelastic': '/home/operador/my-project/Api-JagElastic.py'
}

# Caminho fixo para imagens
CAMINHO_IMAGENS = r"/home/operador/my-project/capturas"

def executar_script(caminho_script):
    global logs
    with logs_lock:
        logs.clear()
        logs.append("Início da execução...\n")
    try:
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            python_executavel = sys.executable
        else:
            python_executavel = 'python'
        with logs_lock:
            logs.append(f"Executando: {python_executavel} {caminho_script}\n")
        process = subprocess.Popen(
            [python_executavel, caminho_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in iter(process.stdout.readline, ''):
            if line:
                with logs_lock:
                    logs.append(line)
        process.stdout.close()
        process.wait()
        with logs_lock:
            if process.returncode == 0:
                logs.append("Execução finalizada com sucesso.\n")
            else:
                logs.append(f"Erro: código {process.returncode}\n")
    except Exception as e:
        with logs_lock:
            logs.append(f"Erro ao executar: {e}\n")
    finally:
        executando.clear()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/elastic')
def elastic():
    return render_template('elastic.html')

@app.route('/opensearch')
def opensearch():
    return render_template('opensearch.html')

@app.route('/posdrop')
def posdrop():
    return render_template('posdrop.html')

@app.route('/sair')
def sair():
    # Aqui você pode adicionar lógica de logout ou finalizar sessão
    return "Sessão finalizada. Pode fechar o navegador."

@app.route('/executar_captura', methods=['POST'])
def executar_captura():
    data = request.get_json()
    nome_script = data.get('script')
    caminho_script = caminhos_scripts.get(nome_script)
    if not caminho_script:
        return jsonify({"status": f"Script '{nome_script}' não encontrado."})
    if executando.is_set():
        return jsonify({"status": "Já existe uma execução em andamento."})
    executando.set()
    thread = threading.Thread(target=executar_script, args=(caminho_script,))
    thread.start()
    return jsonify({"status": f"Execução do script '{nome_script}' iniciada."})

@app.route('/executar_elastic', methods=['POST'])
def executar_elastic():
    data = request.get_json()
    nome_script = data.get('script')
    caminho_script = caminhos_elastic.get(nome_script)
    if not caminho_script:
        return jsonify({"status": f"Script '{nome_script}' não encontrado."})
    if executando.is_set():
        return jsonify({"status": "Já existe uma execução em andamento."})
    executando.set()
    thread = threading.Thread(target=executar_script, args=(caminho_script,))
    thread.start()
    return jsonify({"status": f"Execução do script Elastic '{nome_script}' iniciada."})

@app.route("/pptx", methods=["GET", "POST"])
def pptx():
    if request.method == "POST":
        pptx_file = request.files.get("pptx_file")
        config_file = request.files.get("config_file")
        nome_saida = request.form.get("nome_saida")                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     

        if not pptx_file or not config_file or not nome_saida:
            flash("Todos os campos são obrigatórios.")
            return redirect(url_for("pptx"))

        pptx_path = os.path.join(UPLOAD_FOLDER, secure_filename(pptx_file.filename))
        config_path = os.path.join(UPLOAD_FOLDER, secure_filename(config_file.filename))

        pptx_file.save(pptx_path)
        config_file.save(config_path)

        try:
            configuracoes = ler_configuracoes_arquivo(config_path)
            if not configuracoes:
                flash("Nenhuma configuração válida encontrada no arquivo.")
                return redirect(url_for("pptx"))

            output_path = os.path.join(UPLOAD_FOLDER, f"{secure_filename(nome_saida)}.pptx")
            ajustar_imagens_pptx(pptx_path, output_path, configuracoes, CAMINHO_IMAGENS)

            return render_template("pptx_resultado.html", arquivo=os.path.basename(output_path))
        except Exception as e:
            flash(f"Erro ao processar: {e}")
            return redirect(url_for("pptx"))

    return render_template("pptx_index.html")


@app.route("/download/<arquivo>")
def download(arquivo):
    path = os.path.join(UPLOAD_FOLDER, arquivo)
    return send_file(path, as_attachment=True)

@app.route('/logs')
def obter_logs():
    with logs_lock:
        logs_copy = list(logs)
    return jsonify({"logs": logs_copy})

@app.route('/limpar_logs', methods=['POST'])
def limpar_logs():
    with logs_lock:
        logs.clear()
    return jsonify({"status": "Logs limpos com sucesso."})

if __name__ == '__main__':
    app.run(debug=True)