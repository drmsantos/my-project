from flask import Flask, render_template, jsonify
import threading
import subprocess
import sys

app = Flask(__name__)

logs = []

def executar_script_captura():
    global logs
    logs.clear()
    logs.append("Início da captura...\n")

    # Caminho absoluto para Captura.py
    caminho_script = r"D:\Projetos\Automacao\my-project\Captura.py"

    try:
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            python_executavel = sys.executable
        else:
            python_executavel = 'python'

        logs.append(f"Executando: {python_executavel} {caminho_script}\n")

        process = subprocess.Popen(
            [python_executavel, caminho_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in iter(process.stdout.readline, ''):
            if line:
                logs.append(line)
        process.stdout.close()
        process.wait()

        if process.returncode == 0:
            logs.append("Execução finalizada com sucesso.\n")
        else:
            logs.append(f"Script retornou código de erro: {process.returncode}\n")

    except Exception as e:
        logs.append(f"Erro ao executar Captura.py: {e}\n")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/executar_captura', methods=['POST'])
def executar_captura():
    thread = threading.Thread(target=executar_script_captura)
    thread.start()
    return jsonify({"status": "Execução iniciada"})

@app.route('/logs')
def obter_logs():
    return jsonify({"logs": ''.join(logs)})

if __name__ == '__main__':
    app.run(debug=True)
