import streamlit as st
import pandas as pd
import os
from database.database import DB_PATH, get_connection

st.set_page_config(page_title="Configurações | Assistente de Compras", layout="wide")

st.title("⚙️ Configurações e Manutenção")
st.markdown("---")

st.subheader("💾 Backup do Banco de Dados")
st.write("É altamente recomendável baixar um backup do seu banco de dados semanalmente. Assim você não perde seus cadastros e histórico.")

# Verifica se o arquivo de banco de dados existe e cria um botão de download
if os.path.exists(DB_PATH):
    with open(DB_PATH, "rb") as file:
        btn = st.download_button(
            label="⬇️ Fazer Download do Banco de Dados (compras.db)",
            data=file,
            file_name="backup_compras.db",
            mime="application/octet-stream",
            type="primary"
        )
else:
    st.error("Arquivo de banco de dados não encontrado.")

st.markdown("---")
st.subheader("📊 Exportar Dados para Excel (CSV)")
st.write("Baixe suas listas completas para usar em planilhas convencionais.")

col1, col2 = st.columns(2)

conn = get_connection()

# Exportar Produtos
df_export_prod = pd.read_sql("SELECT * FROM produtos", conn)
csv_prod = df_export_prod.to_csv(index=False).encode('utf-8')
col1.download_button(
    label="📦 Exportar Tabela de Produtos",
    data=csv_prod,
    file_name='produtos.csv',
    mime='text/csv',
)

# Exportar Fornecedores
df_export_forn = pd.read_sql("SELECT * FROM fornecedores", conn)
csv_forn = df_export_forn.to_csv(index=False).encode('utf-8')
col2.download_button(
    label="🏢 Exportar Tabela de Fornecedores",
    data=csv_forn,
    file_name='fornecedores.csv',
    mime='text/csv',
)

conn.close()