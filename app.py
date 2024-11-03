import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

# Inicialize o app
app = Flask(__name__)
app.secret_key = 'chave_secreta_para_sessao'

# Função para configurar o banco de dados
def init_db():
    try:
        conn = sqlite3.connect('membros.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS membros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                progresso INTEGER NOT NULL,
                foto TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        conn.close()

# Chame a função ao iniciar o app
init_db()

# Rota para a página inicial
@app.route('/')
def index():
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
    return render_template('index.html', membros=membros)

# Rota para a página de progresso dos membros
@app.route('/progresso')
def progresso():
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

# Rota para servir arquivos estáticos (CSS, JS, etc.)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Rota para o login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'senha123':
            session['logged_in'] = True
            return redirect(url_for('adicionar_membro'))
        else:
            return "Usuário ou senha incorretos!"
    return render_template('login.html')

# Rota para adicionar membros (acesso restrito)
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_membro():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        progresso = request.form.get('progresso')
        
        if nome and progresso:
            try:
                conn = sqlite3.connect('membros.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO membros (nome, progresso) VALUES (?, ?)", (nome, int(progresso)))
                conn.commit()
            except Exception as e:
                print(f"Erro ao adicionar membro: {e}")
            finally:
                conn.close()
            return redirect(url_for('index'))
    
    try:
        conn = sqlite3.connect('membros.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, progresso FROM membros")
        membros = cursor.fetchall()
    except Exception as e:
        print(f"Erro ao buscar membros para adição: {e}")
        membros = []
    finally:
        conn.close()
    
    return render_template('adicionar_membro.html', membros=membros)

# Rota para aumentar o progresso de um membro
@app.route('/aumentar_progresso', methods=['POST'])
def aumentar_progresso():
    membro_id = request.form.get('membro_id')
    if membro_id:
        try:
            conn = sqlite3.connect('membros.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE membros SET progresso = MIN(progresso + 10, 100) WHERE id = ?", (membro_id,))
            conn.commit()
            print(f"Progresso aumentado para o membro ID {membro_id}.")
        except Exception as e:
            print(f"Erro ao aumentar progresso: {e}")
        finally:
            conn.close()
    return redirect(url_for('adicionar_membro'))

# Rota para diminuir o progresso de um membro
@app.route('/diminuir_progresso', methods=['POST'])
def diminuir_progresso():
    membro_id = request.form.get('membro_id')
    if membro_id:
        try:
            conn = sqlite3.connect('membros.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE membros SET progresso = MAX(progresso - 10, 0) WHERE id = ?", (membro_id,))
            conn.commit()
            print(f"Progresso diminuído para o membro ID {membro_id}.")
        except Exception as e:
            print(f"Erro ao diminuir progresso: {e}")
        finally:
            conn.close()
    return redirect(url_for('adicionar_membro'))

# Rota para remover membro
@app.route('/remover', methods=['POST'])
def remover_membro():
    membro_id = request.form.get('membro_id')
    if membro_id:
        try:
            conn = sqlite3.connect('membros.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM membros WHERE id = ?", (membro_id,))
            conn.commit()
            print(f"Membro ID {membro_id} removido.")
        except Exception as e:
            print(f"Erro ao remover membro: {e}")
        finally:
            conn.close()
    return redirect(url_for('adicionar_membro'))

# Rota para logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)



