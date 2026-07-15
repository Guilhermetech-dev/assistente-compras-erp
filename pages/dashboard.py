import streamlit as st
import pandas as pd
from database.database import get_connection

st.set_page_config(page_title="Dashboard | Assistente de Compras", layout="wide")

st.title("🏠 Dashboard Gerencial")
st.markdown("---")

conn = get_connection()

# ==========================================
# 1. CÁLCULO DAS MÉTRICAS REAIS
# ==========================================

# Total de Produtos e Fornecedores
total_prod = pd.read_sql("SELECT COUNT(id) FROM produtos WHERE ativo = 1", conn).iloc[0,0]
total_forn = pd.read_sql("SELECT COUNT(id) FROM fornecedores WHERE ativo = 1", conn).iloc[0,0]

# Total de cotações ativas
total_cotacoes = pd.read_sql("SELECT COUNT(id) FROM precos WHERE ativo = 1", conn).iloc[0,0]

# Produtos sem nenhum preço cadastrado (Subquery no SQL)
query_sem_preco = """
    SELECT COUNT(id) FROM produtos 
    WHERE ativo = 1 AND id NOT IN (SELECT DISTINCT produto_id FROM precos)
"""
sem_preco = pd.read_sql(query_sem_preco, conn).iloc[0,0]

# Movimentações do Histórico (Aumentos e Reduções)
aumentos = pd.read_sql("SELECT COUNT(id) FROM historico_precos WHERE preco_novo > preco_antigo", conn).iloc[0,0]
reducoes = pd.read_sql("SELECT COUNT(id) FROM historico_precos WHERE preco_novo < preco_antigo", conn).iloc[0,0]

# ==========================================
# 2. EXIBIÇÃO NO TOPO (Visão Geral)
# ==========================================
st.markdown("### 📊 Visão Geral do Sistema")
col1, col2, col3, col4 = st.columns(4)

col1.metric("📦 Produtos Cadastrados", total_prod)
col2.metric("🏢 Fornecedores", total_forn)
col3.metric("💲 Preços Lançados", total_cotacoes)

# Destaca em vermelho se houver muitos produtos sem preço
if sem_preco > 0:
    col4.metric("⚠️ Produtos Sem Preço", sem_preco, delta="Requer atenção", delta_color="inverse")
else:
    col4.metric("✅ Produtos Sem Preço", "0", delta="Tudo cotado!", delta_color="normal")

st.markdown("---")

# ==========================================
# 3. EXIBIÇÃO INFERIOR (Análise de Mercado)
# ==========================================
st.markdown("### 📉 Termômetro de Mercado (Todo o período)")
c1, c2, c3 = st.columns(3)

c1.metric("📈 Aumentos de Preço", aumentos, help="Quantidade de vezes que um fornecedor subiu o preço.")
c2.metric("📉 Reduções de Preço", reducoes, help="Quantidade de vezes que um fornecedor baixou o preço.")

# Saldo de Movimentações (Métrica customizada para ver se o mercado está inflacionando para você)
saldo_mov = reducoes - aumentos
if saldo_mov > 0:
    c3.metric("Balanço de Variações", "Positivo", delta=f"{saldo_mov} reduções a mais", delta_color="normal")
elif saldo_mov < 0:
    c3.metric("Balanço de Variações", "Negativo", delta=f"{abs(saldo_mov)} aumentos a mais", delta_color="inverse")
else:
    c3.metric("Balanço de Variações", "Neutro", delta="Estável", delta_color="off")

st.markdown("---")

# ==========================================
# 4. ÚLTIMAS ATUALIZAÇÕES (Tabela Rápida)
# ==========================================
st.markdown("### ⏱️ Últimos Preços Atualizados")
query_ultimos = """
    SELECT 
        p.nome as Produto,
        f.nome as Fornecedor,
        pr.preco_unitario as [Preço (R$)],
        pr.data_atualizacao as Data
    FROM precos pr
    JOIN produtos p ON pr.produto_id = p.id
    JOIN fornecedores f ON pr.fornecedor_id = f.id
    ORDER BY pr.id DESC
    LIMIT 5
"""
df_ultimos = pd.read_sql(query_ultimos, conn)

if not df_ultimos.empty:
    df_ultimos['Preço (R$)'] = df_ultimos['Preço (R$)'].apply(lambda x: f"R$ {x:.2f}")
    st.dataframe(df_ultimos, use_container_width=True, hide_index=True)
else:
    st.info("Nenhuma atualização recente encontrada.")

conn.close()