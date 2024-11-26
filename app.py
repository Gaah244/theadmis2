import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, make_response
from flask import Flask, render_template, request, redirect, url_for, session, make_response

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
# Rota para a página de missões
@app.route('/missao')
def missoes():
    return render_template('missoes.html')
# Rota para o dashboard
@app.route('/dashboard')
def dashboard():
    estatisticas = obter_estatisticas()
    return render_template('dashboard.html', estatisticas=estatisticas)
# Rota para login
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
# Rota para aceitar os termos
@app.route('/aceitar_termos', methods=['POST'])
def aceitar_termos():
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('termsAccepted', 'true', max_age=60*60*24*365)  # O cookie expira em 1 ano
    return resp

    # Atualiza o status de aceitação dos termos no banco de dados
    try:
        membro_id = request.form.get('membro_id')  # Você precisa passar o ID do membro ao aceitar os termos
        if membro_id:
            conn = sqlite3.connect('membros.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE membros SET aceitou_termos = 1 WHERE id = ?", (membro_id,))
            conn.commit()
    except Exception as e:
        print(f"Erro ao atualizar aceitação de termos: {e}")
    finally:
        conn.close()

    return resp

if __name__ == '__main__':
    app.run(debug=True)