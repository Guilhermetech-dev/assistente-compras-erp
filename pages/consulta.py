import streamlit as st
import pandas as pd
from database.database import get_connection

st.set_page_config(page_title="Consulta | Assistente de Compras", layout="wide")

st.title("🔎 Consulta Inteligente de Preços")
st.markdown("---")

conn = get_connection()

# Busca apenas os produtos que JÁ POSSUEM algum preço cadastrado
query_prods = """
    SELECT DISTINCT p.id, p.nome, p.marca
    FROM produtos p
    JOIN precos pr ON p.id = pr.produto_id
    WHERE p.ativo = 1
"""
df_produtos = pd.read_sql(query_prods, conn)

if df_produtos.empty:
    st.info("💡 Nenhum produto com preço cadastrado. Use a tela de 'Tabela de Preços' para fazer os primeiros lançamentos.")
else:
    # Prepara a lista para o campo de busca
    lista_produtos = df_produtos.apply(lambda row: f"{row['id']} - {row['nome']} ({row['marca']})", axis=1).tolist()
    
    st.markdown("### O que você quer comprar hoje?")
    # O selectbox do Streamlit funciona automaticamente como uma barra de pesquisa se o usuário começar a digitar
    produto_selecionado = st.selectbox("Digite ou selecione o produto:", [""] + lista_produtos)
    
    if produto_selecionado != "":
        # Extrai o ID do produto
        prod_id = int(produto_selecionado.split(" - ")[0])
        nome_produto = produto_selecionado.split(" - ")[1]
        
        # Busca os preços desse produto específico, ordenando do mais barato para o mais caro
        query_precos = """
            SELECT 
                f.nome as Fornecedor,
                pr.preco_unitario as Preco_Raw,
                pr.data_atualizacao as Data
            FROM precos pr
            JOIN fornecedores f ON pr.fornecedor_id = f.id
            WHERE pr.produto_id = ? AND pr.ativo = 1
            ORDER BY pr.preco_unitario ASC
        """
        df_resultado = pd.read_sql(query_precos, conn, params=(prod_id,))
        
        if not df_resultado.empty:
            st.markdown(f"#### Comparativo de Fornecedores para: **{nome_produto}**")
            
            # Descobre qual é o menor preço (como ordenamos ASC no SQL, é sempre a primeira linha)
            menor_preco = df_resultado['Preco_Raw'].iloc[0]
            
            # Função para calcular a diferença e colocar a estrela no melhor
            def formatar_diferenca(preco):
                if preco == menor_preco:
                    return "⭐ Melhor Preço"
                else:
                    diferenca = preco - menor_preco
                    return f"+ R$ {diferenca:.2f}"
            
            # Aplica a lógica nas colunas
            df_resultado['Diferença'] = df_resultado['Preco_Raw'].apply(formatar_diferenca)
            df_resultado['Preço'] = df_resultado['Preco_Raw'].apply(lambda x: f"R$ {x:.2f}")
            
            # Removemos a coluna Raw que foi usada só para cálculo e reordenamos para exibição
            df_exibicao = df_resultado[['Fornecedor', 'Preço', 'Diferença', 'Data']]
            
            # Destaca o menor preço em um card visual antes da tabela
            st.success(f"🏆 O melhor preço atual é **R$ {menor_preco:.2f}** no fornecedor **{df_resultado['Fornecedor'].iloc[0]}**.")
            
            # Exibe a tabela formatada
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
            
        else:
            st.warning("Não foram encontrados preços para este produto.")

conn.close()