from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
import os
from datetime import datetime

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
    if request.method == 'GET':
        response = supabase.table('insumos').select("*").order('id').execute()
        return jsonify(response.data)
    
    novo = request.json
    novo['custo_unitario'] = float(novo['preco']) / float(novo['quantidade'])
    supabase.table('insumos').insert(novo).execute()
    return jsonify({"success": True})

@app.route('/api/insumos/<int:id>', methods=['PUT', 'DELETE'])
def update_insumo(id):
    if request.method == 'DELETE':
        supabase.table('insumos').delete().eq('id', id).execute()
    elif request.method == 'PUT':
        dados = request.json
        dados['custo_unitario'] = float(dados['preco']) / float(dados['quantidade'])
        supabase.table('insumos').update(dados).eq('id', id).execute()
    return jsonify({"success": True})

# --- API RECEITAS ---
@app.route('/api/receitas', methods=['GET', 'POST'])
def handle_receitas():
    if request.method == 'GET':
        response = supabase.table('receitas').select("*").order('id').execute()
        return jsonify(response.data)
    
    nova = request.json
    supabase.table('receitas').insert(nova).execute()
    return jsonify({"success": True})

@app.route('/api/receitas/<int:id>', methods=['DELETE'])
def delete_receita(id):
    supabase.table('receitas').delete().eq('id', id).execute()
    return jsonify({"success": True})

# --- API FECHAMENTO (MÉTODO FINANCEIRO EXPRESSO) ---
@app.route('/api/fechamentos', methods=['GET', 'POST'])
def handle_fechamentos():
    if request.method == 'GET':
        response = supabase.table('fechamentos').select("*").order('id', desc=True).execute()
        return jsonify(response.data)
    
    f = request.json
    f['data'] = datetime.now().strftime("%d/%m/%Y %H:%M")
    # Cálculos automáticos de consultoria
    f['total_global'] = float(f['caixa_dinheiro']) + float(f['caixa_pix']) + float(f['caixa_cartao'])
    f['esperado_gaveta'] = float(f['fundo_caixa']) + float(f['caixa_dinheiro']) - float(f['despesas_dia'])
    
    supabase.table('fechamentos').insert(f).execute()
    return jsonify({"success": True})

@app.route('/api/fechamentos/<int:id>', methods=['PUT', 'DELETE'])
def update_fechamento(id):
    if request.method == 'DELETE':
        supabase.table('fechamentos').delete().eq('id', id).execute()
    elif request.method == 'PUT':
        f = request.json
        f['total_global'] = float(f['caixa_dinheiro']) + float(f['caixa_pix']) + float(f['caixa_cartao'])
        f['esperado_gaveta'] = float(f['fundo_caixa']) + float(f['caixa_dinheiro']) - float(f['despesas_dia'])
        supabase.table('fechamentos').update(f).eq('id', id).execute()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)