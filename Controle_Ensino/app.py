from flask import Flask, render_template, request, redirect, url_for, flash, make_response
import json

app = Flask(__name__)
app.config.from_object('config.Config')

# Função para recuperar dados do cookie
def get_user_data():
    data = request.cookies.get('user_data')
    if data:
        data = json.loads(data)
    else:
        data = {"users": [], "current_user": None}

    # Verificar se o administrador já está na lista de usuários, caso contrário, adicioná-lo
    admin_exists = any(user['username'] == 'administrador' for user in data['users'])
    if not admin_exists:
        data['users'].append({"username": "administrador", "password": "adm", "dietas": []})

    return data


# Rota para a página inicial
@app.route('/')
def home():
    data = get_user_data()
    if data['current_user']:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        data = get_user_data()

        # Verifica se o usuário existe
        for user in data['users']:
            if user['username'] == username and user['password'] == password:
                resp = make_response(redirect(url_for('dashboard')))
                data['current_user'] = username
                resp.set_cookie('user_data', json.dumps(data))
                return resp
        flash("Nome de usuário ou senha incorretos.")
    return render_template('login.html')

def is_admin():
    data = get_user_data()
    return data['current_user'] == 'administrador'

# Página de registro
# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        data = get_user_data()

        # Verifica se o nome de usuário é "administrador" ou se já existe
        if username == 'administrador':
            flash("Não é possível registrar um usuário com este nome.")
            return render_template('register.html')

        for user in data['users']:
            if user['username'] == username:
                flash("Nome de usuário já existe.")
                return render_template('register.html')

        # Adiciona o novo usuário
        data['users'].append({"username": username, "password": password, "dietas": []})
        resp = make_response(redirect(url_for('login')))
        resp.set_cookie('user_data', json.dumps(data))
        return resp
    return render_template('register.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    data = get_user_data()
    if not data['current_user']:
        return redirect(url_for('login'))

    current_user = data['current_user']
    is_admin_user = is_admin()

    if request.method == 'POST':
        nome_dieta = request.form['nome_dieta']
        calorias = request.form['calorias']
        cardapio = request.form.getlist('cardapio')
        for user in data['users']:
            if user['username'] == current_user:
                user['dietas'].append({"nome_dieta": nome_dieta, "calorias": calorias, "cardapio": cardapio})
                break
        resp = make_response(redirect(url_for('dashboard')))
        resp.set_cookie('user_data', json.dumps(data))
        return resp

    for user in data['users']:
        if user['username'] == current_user:
            dietas = user['dietas']
            break
    return render_template('dashboard.html', dietas=dietas, is_admin=is_admin_user)

# Exibir e editar cardápio da dieta
@app.route('/dieta/<int:dieta_id>', methods=['GET', 'POST'])
def exibir_dieta(dieta_id):
    data = get_user_data()
    current_user = data['current_user']

    if request.method == 'POST':
        cardapio_atualizado = request.form.getlist('cardapio')
        for user in data['users']:
            if user['username'] == current_user:
                user['dietas'][dieta_id]['cardapio'] = cardapio_atualizado
                break
        resp = make_response(redirect(url_for('exibir_dieta', dieta_id=dieta_id)))
        resp.set_cookie('user_data', json.dumps(data))
        return resp

    for user in data['users']:
        if user['username'] == current_user:
            dieta = user['dietas'][dieta_id]
            break

    return render_template('dieta.html', dieta=dieta, dieta_id=dieta_id)

# Rota para excluir uma dieta
@app.route('/dieta/delete/<int:dieta_id>', methods=['POST'])
def deletar_dieta(dieta_id):
    data = get_user_data()
    current_user = data['current_user']

    for user in data['users']:
        if user['username'] == current_user:
            user['dietas'].pop(dieta_id)
            break

    resp = make_response(redirect(url_for('dashboard')))
    resp.set_cookie('user_data', json.dumps(data))
    return resp

# Logout
@app.route('/logout')
def logout():
    data = get_user_data()
    data['current_user'] = None
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('user_data', json.dumps(data))
    return resp


# Rota para listar usuários (apenas para o administrador)
@app.route('/listar_usuarios', methods=['GET', 'POST'])
def listar_usuarios():
    if not is_admin():
        return redirect(url_for('dashboard'))

    data = get_user_data()

    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')

        if action == 'delete':
            data['users'] = [user for user in data['users'] if user['username'] != username]
        elif action == 'update':
            new_username = request.form.get('new_username')
            for user in data['users']:
                if user['username'] == username:
                    user['username'] = new_username
                    break
        resp = make_response(redirect(url_for('listar_usuarios')))
        resp.set_cookie('user_data', json.dumps(data))
        return resp

    return render_template('listar_usuarios.html', users=data['users'])


if __name__ == '__main__':
    app.run(debug=True)
