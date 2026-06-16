from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Configurações de Conexão (Pegas das variáveis de ambiente da Vercel)
URL: str = os.environ.get("SUPABASE_URL")
KEY: str = os.environ.get("SUPABASE_KEY")

def get_supabase_client(token=None):
    """
    Cria um cliente Supabase. Se um token de usuário (JWT) for fornecido,
    o cliente atuará com as permissões daquele usuário logado.
    """
    client = create_client(URL, KEY)
    if token:
        client.postgrest.auth(token)
    return client

def get_token():
    """
    Extrai o token de autenticação enviado pelo navegador no cabeçalho.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return None

@app.route('/')
def index():
    return render_template('index.html')

# --- API INSUMOS ---
@app.route('/api/insumos', methods=['GET', 'POST'])
def handle_insumos():
    token = get_token()
    if not token:
        return jsonify({"error": "Acesso negado. Faça login."}), 401
    
    sb = get_supabase_client(token)
    try:
        if request.method == 'GET':
            response = sb.table('insumos').select("*").order('id').execute()
            return jsonify(response.data)
        
        elif request.method == 'POST':
            data = request.json
            # Cálculo automático do custo unitário antes de salvar
            preco = float(data.get('preco', 0))
            qtd = float(data.get('quantidade', 0))
            data['custo_unitario'] = preco / qtd if qtd > 0 else 0
            
            response = sb.table('insumos').insert(data).execute()
            return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/insumos/<int:id>', methods=['PUT', 'DELETE'])
def gerenciar_insumo(id):
    token = get_token()
    if not token: return jsonify({"error": "Não autorizado"}), 401
    
    sb = get_supabase_client(token)
    
    if request.method == 'PUT':
        data = request.json
        # Refaz o cálculo de custo por grama caso o preço ou peso sejam editados
        preco = float(data.get('preco', 0))
        qtd = float(data.get('quantidade', 0))
        data['custo_unitario'] = preco / qtd if qtd > 0 else 0
        
        response = sb.table('insumos').update(data).eq('id', id).execute()
        return jsonify(response.data)
        
    elif request.method == 'DELETE':
        sb.table('insumos').delete().eq('id', id).execute()
        return jsonify({"success": True})

# --- API RECEITAS ---
@app.route('/api/receitas', methods=['GET', 'POST'])
def handle_receitas():
    token = get_token()
    if not token: return jsonify({"error": "Não autorizado"}), 401
    
    sb = get_supabase_client(token)
    try:
        if request.method == 'GET':
            response = sb.table('receitas').select("*").order('id').execute()
            return jsonify(response.data)
        
        elif request.method == 'POST':
            # Salva a receita (o cálculo já vem pronto do frontend)
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

# --- API FECHAMENTOS (CAIXA EXPRESSO) ---
@app.route('/api/fechamentos', methods=['GET', 'POST'])
def handle_fechamentos():
    token = get_token()
    if not token: return jsonify({"error": "Não autorizado"}), 401
    
    sb = get_supabase_client(token)
    try:
        if request.method == 'GET':
            response = sb.table('fechamentos').select("*").order('id', desc=True).execute()
            return jsonify(response.data)
        
        elif request.method == 'POST':
            data = request.json
            
            # --- CORREÇÃO: Forçando a Data/Hora pelo Python (Fuso do Brasil) ---
            # Pegamos o horário do servidor e subtraímos 3 horas (Horário de Brasília)
            agora_br = datetime.utcnow() - timedelta(hours=3)
            data['data'] = agora_br.isoformat()
            # -------------------------------------------------------------------
            
            # Cálculos financeiros
            fundo = float(data.get('fundo_caixa', 0))
            sangria = float(data.get('despesas_dia', 0))
            dinheiro = float(data.get('caixa_dinheiro', 0))
            pix = float(data.get('caixa_pix', 0))
            cartao = float(data.get('caixa_cartao', 0))
            
            data['total_global'] = dinheiro + pix + cartao
            data['esperado_gaveta'] = fundo + dinheiro - sangria
            
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
        fundo = float(data.get('fundo_caixa', 0))
        sangria = float(data.get('despesas_dia', 0))
        dinheiro = float(data.get('caixa_dinheiro', 0))
        
        data['total_global'] = dinheiro + float(data.get('caixa_pix', 0)) + float(data.get('caixa_cartao', 0))
        data['esperado_gaveta'] = fundo + dinheiro - sangria
        
        sb.table('fechamentos').update(data).eq('id', id).execute()
        return jsonify({"success": True})
        
    elif request.method == 'DELETE':
        sb.table('fechamentos').delete().eq('id', id).execute()
        return jsonify({"success": True})

# Necessário para rodar localmente se desejar, mas a Vercel ignora isso
if __name__ == '__main__':
    app.run(debug=True)