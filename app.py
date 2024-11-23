import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify

# Inicialize o app
app = Flask(__name__)
app.secret_key = 'chave_secreta_para_sessao'

# Função para configurar o banco de dados
def init_db():
    try:
        conn = sqlite3.connect('membros.db')
        cursor = conn.cursor()
        
        # Cria a tabela membros, se ainda não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS membros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                progresso INTEGER NOT NULL,
                foto TEXT,
                aceitou_termos BOOLEAN DEFAULT 0
            )
        ''')

        # Verifica e adiciona a coluna 'aceitou_termos' caso ela não exista
        cursor.execute("PRAGMA table_info(membros)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'aceitou_termos' not in columns:
            cursor.execute("ALTER TABLE membros ADD COLUMN aceitou_termos BOOLEAN DEFAULT 0")
            conn.commit()
        
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        conn.close()

# Função para obter estatísticas
def obter_estatisticas():
    try:
        conn = sqlite3.connect('membros.db')
        cursor = conn.cursor()
        
        # Total de membros
        cursor.execute("SELECT COUNT(*) FROM membros")
        total_membros = cursor.fetchone()[0]
        
        # Progresso médio
        cursor.execute("SELECT AVG(progresso) FROM membros")
        progresso_medio = cursor.fetchone()[0] or 0

        # Membros que aceitaram os termos
        cursor.execute("SELECT COUNT(*) FROM membros WHERE aceitou_termos = 1")
        membros_termos = cursor.fetchone()[0]
    except Exception as e:
        print(f"Erro ao obter estatísticas: {e}")
        total_membros, progresso_medio, membros_termos = 0, 0, 0
    finally:
        conn.close()
    
    return {
        "total_membros": total_membros,
        "progresso_medio": progresso_medio,
        "membros_termos": membros_termos
    }

# Chame a função ao iniciar o app
init_db()

# Rota para a página inicial
@app.route('/')
def index():
    terms_accepted = request.cookies.get('termsAccepted')
    try:
        conn = sqlite3.connect('membros.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, progresso, foto FROM membros")
        membros = cursor.fetchall()
    except Exception as e:
        print(f"Erro ao buscar membros: {e}")
        membros = []
    finally:
        conn.close()

    membros = [{"id": m[0], "nome": m[1], "progresso": m[2], "foto": m[3] or "default.jpg"} for m in membros]
    return render_template('index.html', membros=membros, terms_accepted=terms_accepted)

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'senha123':
            session['logged_in'] = True
            return redirect(url_for('progresso'))
        else:
            return "Usuário ou senha incorretos!"
    return render_template('login.html')

# Rota para progresso (restrito para admin)
@app.route('/progresso', methods=['GET', 'POST'])
def progresso():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        progresso = request.form.get('progresso')
        try:
            conn = sqlite3.connect('membros.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO membros (nome, progresso) VALUES (?, ?)", (nome, int(progresso)))
            conn.commit()
        except Exception as e:
            print(f"Erro ao adicionar membro: {e}")
        finally:
            conn.close()

    try:
        conn = sqlite3.connect('membros.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, progresso, foto FROM membros")
        membros = cursor.fetchall()
    except Exception as e:
        print(f"Erro ao buscar membros: {e}")
        membros = []
    finally:
        conn.close()

    membros = [{"id": m[0], "nome": m[1], "progresso": m[2], "foto": m[3] or "default.jpg"} for m in membros]
    return render_template('progresso.html', membros=membros)

# API para atualizar progresso
@app.route('/update_progresso', methods=['POST'])
def update_progresso():
    try:
        membro_id = request.json.get('id')
        novo_progresso = request.json.get('progresso')
        
        if membro_id and novo_progresso is not None:
            conn = sqlite3.connect('membros.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE membros SET progresso = ? WHERE id = ?", (novo_progresso, membro_id))
            conn.commit()
            return jsonify({"success": "Progresso atualizado"}), 200
        else:
            return jsonify({"error": "Dados inválidos"}), 400
    except Exception as e:
        print(f"Erro ao atualizar progresso: {e}")
        return jsonify({"error": "Erro ao atualizar progresso"}), 500
    finally:
        conn.close()

# Rota para logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
