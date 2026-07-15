import streamlit as st
import pandas as pd
from database.database import get_connection

st.set_page_config(page_title="Fornecedores | Assistente de Compras", layout="wide")

st.title("🏢 Gestão de Fornecedores")
st.markdown("---")

# Criação das Abas
aba_cadastro, aba_lista = st.tabs(["➕ Cadastrar Fornecedor", "📋 Lista de Fornecedores"])

# ==========================================
# ABA 1: FORMULÁRIO DE CADASTRO
# ==========================================
with aba_cadastro:
    with st.form("form_fornecedor", clear_on_submit=True):
        st.subheader("Dados de Contato")
        
        nome = st.text_input("Nome da Empresa/Fornecedor * (Obrigatório)")
        
        col1, col2, col3 = st.columns(3)
        telefone = col1.text_input("Telefone (Fixo)")
        whatsapp = col2.text_input("WhatsApp")
        email = col3.text_input("E-mail")
        
        st.markdown("---")
        st.subheader("Regras Logísticas e Comerciais")
        
        col4, col5, col6 = st.columns(3)
        pedido_minimo = col4.number_input("Pedido Mínimo (R$)", min_value=0.0, step=50.0, format="%.2f")
        frete_padrao = col5.number_input("Custo de Frete Padrão (R$)", min_value=0.0, step=10.0, format="%.2f")
        prazo_entrega_dias = col6.number_input("Prazo de Entrega (Dias)", min_value=0, step=1)
        
        # Botão de salvar
        submit = st.form_submit_button("Salvar Fornecedor", type="primary", use_container_width=True)
        
        if submit:
            if nome.strip() == "":
                st.error("⚠️ O Nome do Fornecedor é obrigatório!")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO fornecedores (nome, telefone, whatsapp, email, pedido_minimo, frete_padrao, prazo_entrega_dias)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (nome, telefone, whatsapp, email, pedido_minimo, frete_padrao, prazo_entrega_dias))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Fornecedor '{nome}' cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ==========================================
# ABA 2: LISTAGEM DE FORNECEDORES
# ==========================================
with aba_lista:
    st.subheader("Fornecedores Cadastrados")
    
    conn = get_connection()
    query = """
        SELECT 
            id as ID, 
            nome as Nome, 
            whatsapp as WhatsApp, 
            pedido_minimo as [Pedido Mínimo (R$)], 
            prazo_entrega_dias as [Prazo (Dias)]
        FROM fornecedores 
        WHERE ativo = 1
    """
    df_fornecedores = pd.read_sql(query, conn)
    conn.close()
    
    if not df_fornecedores.empty:
        # Exibe a tabela interativa
        st.dataframe(df_fornecedores, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum fornecedor cadastrado ainda. Use a aba ao lado para adicionar o primeiro!")