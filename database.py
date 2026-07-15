import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'compras.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. PRODUTOS (Melhorado com código, quantidade por caixa e observações)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras TEXT,
            codigo_interno TEXT,
            nome TEXT NOT NULL,
            marca TEXT,
            categoria TEXT,
            unidade TEXT,
            qtd_por_caixa INTEGER DEFAULT 1,
            observacoes TEXT,
            ativo BOOLEAN DEFAULT 1
        )
    ''')

    # 2. FORNECEDORES (Melhorado com pedido mínimo, frete e prazo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            whatsapp TEXT,
            email TEXT,
            pedido_minimo REAL DEFAULT 0.0,
            frete_padrao REAL DEFAULT 0.0,
            prazo_entrega_dias INTEGER DEFAULT 0,
            ativo BOOLEAN DEFAULT 1
        )
    ''')

    # 3. PREÇOS (O coração do sistema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            fornecedor_id INTEGER,
            preco_unitario REAL NOT NULL,
            data_atualizacao DATE NOT NULL,
            observacao TEXT,
            ativo BOOLEAN DEFAULT 1,
            FOREIGN KEY (produto_id) REFERENCES produtos (id),
            FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
        )
    ''')

    # 4. HISTÓRICO DE PREÇOS (Para rastrear aumentos e reduções)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preco_id INTEGER,
            preco_antigo REAL,
            preco_novo REAL,
            data_mudanca DATE NOT NULL,
            FOREIGN KEY (preco_id) REFERENCES precos (id)
        )
    ''')

    conn.commit()
    conn.close()

init_db()