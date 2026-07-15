import streamlit as st
import pandas as pd
from database.database import get_connection

st.set_page_config(page_title="Histórico | Assistente de Compras", layout="wide")

st.title("📈 Histórico de Movimentação de Preços")
st.markdown("---")

conn = get_connection()

# Busca todo o histórico cruzando os dados para pegar os nomes reais
query_historico = """
    SELECT 
        hp.data_mudanca as Data,
        p.nome as Produto,
        f.nome as Fornecedor,
        hp.preco_antigo as [Preço Antigo (R$)],
        hp.preco_novo as [Preço Novo (R$)]
    FROM historico_precos hp
    JOIN precos pr ON hp.preco_id = pr.id
    JOIN produtos p ON pr.produto_id = p.id
    JOIN fornecedores f ON pr.fornecedor_id = f.id
    ORDER BY hp.data_mudanca DESC, hp.id DESC
"""
df_historico = pd.read_sql(query_historico, conn)

if df_historico.empty:
    st.info("💡 Nenhuma mudança de preço registrada ainda. Quando você atualizar o preço de um item existente na aba 'Tabela de Preços', o registro aparecerá aqui.")
else:
    st.subheader("Acompanhamento de Aumentos e Reduções")
    
    # 1. Cria colunas de análise para facilitar a visualização
    df_historico['Variação'] = df_historico['Preço Novo (R$)'] - df_historico['Preço Antigo (R$)']
    
    # Adiciona uma tag visual de Status (Aumento = Vermelho, Redução = Verde)
    def classificar_status(valor):
        if valor > 0:
            return "🔴 Aumento"
        elif valor < 0:
            return "🟢 Redução"
        return "⚪ Sem alteração"
        
    df_historico['Status'] = df_historico['Variação'].apply(classificar_status)
    
    # 2. Formatação visual dos valores para reais (R$)
    df_historico['Preço Antigo (R$)'] = df_historico['Preço Antigo (R$)'].apply(lambda x: f"R$ {x:.2f}")
    df_historico['Preço Novo (R$)'] = df_historico['Preço Novo (R$)'].apply(lambda x: f"R$ {x:.2f}")
    df_historico['Variação'] = df_historico['Variação'].apply(lambda x: f"R$ {x:+.2f}")
    
    # 3. Filtro interativo no topo da tabela
    produtos_unicos = ["Todos"] + df_historico['Produto'].unique().tolist()
    produto_filtro = st.selectbox("🔍 Filtrar por Produto específico:", produtos_unicos)
    
    if produto_filtro != "Todos":
        # Filtra o DataFrame apenas para o produto selecionado
        df_historico = df_historico[df_historico['Produto'] == produto_filtro]
        
    # Exibe a tabela reordenando as colunas para o Status ficar no final
    colunas_finais = ['Data', 'Produto', 'Fornecedor', 'Preço Antigo (R$)', 'Preço Novo (R$)', 'Variação', 'Status']
    st.dataframe(df_historico[colunas_finais], use_container_width=True, hide_index=True)

conn.close()