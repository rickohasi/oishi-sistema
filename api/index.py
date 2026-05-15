from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
import os

app = Flask(__name__)

# Configuração via Variáveis de Ambiente (Vercel)
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route('/')
def index():
    return render_template('index.html')

# --- API INSUMOS ---
@app.route('/api/insumos', methods=['GET', 'POST'])
def handle_insumos():
    try:
        if request.method == 'GET':
            response = supabase.table('insumos').select("*").order('id').execute()
            return jsonify(response.data)
        elif request.method == 'POST':
            data = request.json
            try:
                custo_unitario = float(data['preco']) / float(data['quantidade'])
            except (ValueError, ZeroDivisionError):
                custo_unitario = 0
            data['custo_unitario'] = custo_unitario
            response = supabase.table('insumos').insert(data).execute()
            return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/insumos/<int:id>', methods=['DELETE'])
def delete_insumo(id):
    supabase.table('insumos').delete().eq('id', id).execute()
    return jsonify({"message": "Insumo deletado"})

# --- API RECEITAS ---
@app.route('/api/receitas', methods=['GET', 'POST'])
def handle_receitas():
    try:
        if request.method == 'GET':
            response = supabase.table('receitas').select("*").order('id').execute()
            return jsonify(response.data)
        elif request.method == 'POST':
            data = request.json
            response = supabase.table('receitas').insert(data).execute()
            return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/receitas/<int:id>', methods=['DELETE'])
def delete_receita(id):
    supabase.table('receitas').delete().eq('id', id).execute()
    return jsonify({"message": "Receita deletada"})

# --- API FECHAMENTOS ---
@app.route('/api/fechamentos', methods=['GET', 'POST'])
def handle_fechamentos():
    try:
        if request.method == 'GET':
            response = supabase.table('fechamentos').select("*").order('id', desc=True).execute()
            return jsonify(response.data)
        elif request.method == 'POST':
            data = request.json
            fundo = float(data.get('fundo_caixa', 0))
            sangria = float(data.get('despesas_dia', 0))
            dinheiro = float(data.get('caixa_dinheiro', 0))
            pix = float(data.get('caixa_pix', 0))
            cartao = float(data.get('caixa_cartao', 0))
            
            total_global = dinheiro + pix + cartao
            esperado_gaveta = fundo + dinheiro - sangria
            
            data['total_global'] = total_global
            data['esperado_gaveta'] = esperado_gaveta
            
            response = supabase.table('fechamentos').insert(data).execute()
            return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/fechamentos/<int:id>', methods=['PUT', 'DELETE'])
def update_fechamento(id):
    if request.method == 'PUT':
        data = request.json
        fundo = float(data.get('fundo_caixa', 0))
        sangria = float(data.get('despesas_dia', 0))
        dinheiro = float(data.get('caixa_dinheiro', 0))
        pix = float(data.get('caixa_pix', 0))
        cartao = float(data.get('caixa_cartao', 0))
        
        total_global = dinheiro + pix + cartao
        esperado_gaveta = fundo + dinheiro - sangria
        
        data['total_global'] = total_global
        data['esperado_gaveta'] = esperado_gaveta
        
        response = supabase.table('fechamentos').update(data).eq('id', id).execute()
        return jsonify(response.data)
    elif request.method == 'DELETE':
        supabase.table('fechamentos').delete().eq('id', id).execute()
        return jsonify({"message": "Fechamento deletado"})