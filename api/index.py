from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
import os

app = Flask(__name__)

# Configurações do Supabase
URL: str = os.environ.get("SUPABASE_URL")
KEY: str = os.environ.get("SUPABASE_KEY")

def get_supabase_client(token=None):
    # Se recebermos um token de usuário, o cliente agirá como esse usuário
    if token:
        client = create_client(URL, KEY)
        client.postgrest.auth(token)
        return client
    return create_client(URL, KEY)

@app.route('/')
def index():
    return render_template('index.html')

# --- HELPER PARA ROTAS PROTEGIDAS ---
def get_token():
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return None

# --- API INSUMOS ---
@app.route('/api/insumos', methods=['GET', 'POST'])
def handle_insumos():
    token = get_token()
    if not token: return jsonify({"error": "Não autorizado"}), 401
    
    sb = get_supabase_client(token)
    try:
        if request.method == 'GET':
            response = sb.table('insumos').select("*").order('id').execute()
            return jsonify(response.data)
        elif request.method == 'POST':
            data = request.json
            custo = float(data['preco']) / float(data['quantidade']) if float(data['quantidade']) > 0 else 0
            data['custo_unitario'] = custo
            response = sb.table('insumos').insert(data).execute()
            return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/insumos/<int:id>', methods=['DELETE'])
def delete_insumo(id):
    token = get_token()
    sb = get_supabase_client(token)
    sb.table('insumos').delete().eq('id', id).execute()
    return jsonify({"success": True})

# --- API RECEITAS ---
@app.route('/api/receitas', methods=['GET', 'POST'])
def handle_receitas():
    token = get_token()
    sb = get_supabase_client(token)
    try:
        if request.method == 'GET':
            response = sb.table('receitas').select("*").order('id').execute()
            return jsonify(response.data)
        elif request.method == 'POST':
            response = sb.table('receitas').insert(request.json).execute()
            return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/receitas/<int:id>', methods=['DELETE'])
def delete_receita(id):
    token = get_token()
    sb = get_supabase_client(token)
    sb.table('receitas').delete().eq('id', id).execute()
    return jsonify({"success": True})

# --- API FECHAMENTOS ---
@app.route('/api/fechamentos', methods=['GET', 'POST'])
def handle_fechamentos():
    token = get_token()
    sb = get_supabase_client(token)
    try:
        if request.method == 'GET':
            response = sb.table('fechamentos').select("*").order('id', desc=True).execute()
            return jsonify(response.data)
        elif request.method == 'POST':
            data = request.json
            f, d, p, c, s = float(data['fundo_caixa']), float(data['caixa_dinheiro']), float(data['caixa_pix']), float(data['caixa_cartao']), float(data['despesas_dia'])
            data['total_global'] = d + p + c
            data['esperado_gaveta'] = f + d - s
            response = sb.table('fechamentos').insert(data).execute()
            return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/fechamentos/<int:id>', methods=['PUT', 'DELETE'])
def update_fechamento(id):
    token = get_token()
    sb = get_supabase_client(token)
    if request.method == 'PUT':
        data = request.json
        f, d, s = float(data['fundo_caixa']), float(data['caixa_dinheiro']), float(data['despesas_dia'])
        data['total_global'] = d + float(data['caixa_pix']) + float(data['caixa_cartao'])
        data['esperado_gaveta'] = f + d - s
        sb.table('fechamentos').update(data).eq('id', id).execute()
        return jsonify({"success": True})
    elif request.method == 'DELETE':
        sb.table('fechamentos').delete().eq('id', id).execute()
        return jsonify({"success": True})