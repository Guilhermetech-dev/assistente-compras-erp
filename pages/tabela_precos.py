import streamlit as st
import pandas as pd
from datetime import date
from database.database import get_connection

st.set_page_config(page_title="Gestão de Preços | Assistente de Compras", layout="wide")

st.title("💲 Gestão de Preços")
st.markdown("---")

conn = get_connection()

# Busca as listas no banco de dados para popular os seletores
df_produtos = pd.read_sql("SELECT id, nome, marca FROM produtos WHERE ativo = 1", conn)
df_fornecedores = pd.read_sql("SELECT id, nome FROM fornecedores WHERE ativo = 1", conn)

# Trava de segurança: impede o lançamento se não houver produto ou fornecedor cadastrado
if df_produtos.empty or df_fornecedores.empty:
    st.warning("⚠️ Você precisa cadastrar pelo menos um Produto e um Fornecedor antes de lançar preços.")
else:
    # Criação das Abas
    aba_lancamento, aba_tabela = st.tabs(["📝 Lançar/Atualizar Preço", "📊 Tabela de Preços Cadastrados"])
    
    # ==========================================
    # ABA 1: LANÇAMENTO DE PREÇOS
    # ==========================================
    with aba_lancamento:
        st.subheader("Registrar nova cotação")
        
        with st.form("form_preco", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            # Formata as opções para ficarem fáceis de ler no menu suspenso
            lista_produtos = df_produtos.apply(lambda row: f"{row['id']} - {row['nome']} ({row['marca']})", axis=1).tolist()
            lista_fornecedores = df_fornecedores.apply(lambda row: f"{row['id']} - {row['nome']}", axis=1).tolist()
            
            produto_selecionado = col1.selectbox("Selecione o Produto", lista_produtos)
            fornecedor_selecionado = col2.selectbox("Selecione o Fornecedor", lista_fornecedores)
            
            col3, col4 = st.columns(2)
            preco = col3.number_input("Preço Unitário (R$)", min_value=0.01, step=0.10, format="%.2f")
            obs = col4.text_input("Observação (Ex: Promoção, Preço de tabela)")
            
            submit = st.form_submit_button("Salvar Preço", type="primary", use_container_width=True)
            
            if submit:
                # Extrai apenas o número do ID da string selecionada (ex: pega o "1" de "1 - Pote PP")
                prod_id = int(produto_selecionado.split(" - ")[0])
                forn_id = int(fornecedor_selecionado.split(" - ")[0])
                hoje = date.today().strftime("%Y-%m-%d")
                
                cursor = conn.cursor()
                
                # Verifica se já existe um preço cadastrado para essa combinação
                cursor.execute("SELECT id, preco_unitario FROM precos WHERE produto_id = ? AND fornecedor_id = ?", (prod_id, forn_id))
                preco_existente = cursor.fetchone()
                
                if preco_existente:
                    # Lógica de Atualização
                    preco_id = preco_existente[0]
                    preco_antigo = preco_existente[1]
                    
                    cursor.execute("""
                        UPDATE precos 
                        SET preco_unitario = ?, data_atualizacao = ?, observacao = ?
                        WHERE id = ?
                    """, (preco, hoje, obs, preco_id))
                    
                    # Salva no histórico para análises futuras
                    cursor.execute("""
                        INSERT INTO historico_precos (preco_id, preco_antigo, preco_novo, data_mudanca)
                        VALUES (?, ?, ?, ?)
                    """, (preco_id, preco_antigo, preco, hoje))
                    
                    st.success(f"🔄 Preço atualizado com sucesso! (Anterior: R$ {preco_antigo:.2f} ➔ Novo: R$ {preco:.2f})")
                else:
                    # Lógica de Inserção (Primeira vez)
                    cursor.execute("""
                        INSERT INTO precos (produto_id, fornecedor_id, preco_unitario, data_atualizacao, observacao)
                        VALUES (?, ?, ?, ?, ?)
                    """, (prod_id, forn_id, preco, hoje, obs))
                    
                    st.success("✅ Novo preço cadastrado com sucesso!")
                
                conn.commit()
                
    # ==========================================
    # ABA 2: VISUALIZAÇÃO GERAL
    # ==========================================
    with aba_tabela:
        st.subheader("Painel de Preços (Ordenado pelo menor valor)")
        
        # Junta as 3 tabelas para mostrar nomes em vez de IDs
        query_precos = """
            SELECT 
                p.nome as Produto,
                p.marca as Marca,
                f.nome as Fornecedor,
                pr.preco_unitario as [Preço (R$)],
                pr.data_atualizacao as [Última Atualização],
                pr.observacao as Observação
            FROM precos pr
            JOIN produtos p ON pr.produto_id = p.id
            JOIN fornecedores f ON pr.fornecedor_id = f.id
            WHERE pr.ativo = 1
            ORDER BY p.nome ASC, pr.preco_unitario ASC
        """
        df_precos = pd.read_sql(query_precos, conn)
        
        if not df_precos.empty:
            # Formata a coluna de preço para mostrar R$ 
            st.dataframe(df_precos, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum preço cadastrado ainda. Use a aba ao lado para fazer o primeiro lançamento!")

conn.close()