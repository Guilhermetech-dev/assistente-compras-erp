import streamlit as st
import pandas as pd
from database.database import get_connection

st.set_page_config(page_title="Melhor Compra | Assistente de Compras", layout="wide")

st.title("📄 Sugestão de Melhor Compra")
st.markdown("---")

# 1. Verifica se tem algo no carrinho
if 'carrinho' not in st.session_state or not st.session_state.carrinho:
    st.warning("⚠️ Sua lista de compras está vazia.")
    if st.button("Voltar para Lista"):
        st.switch_page("pages/lista_compras.py")
    st.stop() # Para a execução da página aqui

# 2. Busca todos os preços dos itens que estão no carrinho
conn = get_connection()
prod_ids = tuple(st.session_state.carrinho.keys())

# Formatação segura para a query SQL (cria ?,?,? baseado na quantidade de itens)
placeholders = ','.join('?' * len(prod_ids))
query = f"""
    SELECT 
        pr.produto_id,
        p.nome as produto_nome,
        pr.fornecedor_id,
        f.nome as fornecedor_nome,
        f.pedido_minimo,
        pr.preco_unitario
    FROM precos pr
    JOIN fornecedores f ON pr.fornecedor_id = f.id
    JOIN produtos p ON pr.produto_id = p.id
    WHERE pr.produto_id IN ({placeholders}) AND pr.ativo = 1
"""
df_precos = pd.read_sql(query, conn, params=prod_ids)
conn.close()

# 3. O ALGORITMO: Processa a melhor combinação
pedidos_por_fornecedor = {}
itens_sem_preco = []
economia_total = 0.0 # Para calcular o quanto você salvou

for prod_id, dados_carrinho in st.session_state.carrinho.items():
    qtd = dados_carrinho['quantidade']
    nome_prod = dados_carrinho['nome']
    
    # Filtra apenas os preços deste produto específico
    df_prod = df_precos[df_precos['produto_id'] == prod_id]
    
    if df_prod.empty:
        itens_sem_preco.append(nome_prod)
        continue
        
    # Acha a linha do Menor Preço e a linha do Maior Preço (para cálculo de economia)
    idx_min = df_prod['preco_unitario'].idxmin()
    melhor_opcao = df_prod.loc[idx_min]
    
    preco_maximo_mercado = df_prod['preco_unitario'].max()
    preco_un = melhor_opcao['preco_unitario']
    
    economia_total += (preco_maximo_mercado - preco_un) * qtd
    
    forn_id = melhor_opcao['fornecedor_id']
    forn_nome = melhor_opcao['fornecedor_nome']
    minimo = melhor_opcao['pedido_minimo']
    
    subtotal = preco_un * qtd
    
    # Organiza os itens "vencedores" por fornecedor
    if forn_id not in pedidos_por_fornecedor:
        pedidos_por_fornecedor[forn_id] = {
            "fornecedor_nome": forn_nome,
            "pedido_minimo": minimo,
            "total": 0.0,
            "itens": []
        }
        
    pedidos_por_fornecedor[forn_id]['itens'].append({
        "produto": melhor_opcao['produto_nome'],
        "qtd": qtd,
        "preco_un": preco_un,
        "subtotal": subtotal
    })
    pedidos_por_fornecedor[forn_id]['total'] += subtotal

# 4. EXIBIÇÃO DOS RESULTADOS
col1, col2 = st.columns([7, 3])

with col1:
    st.subheader("📦 Pedidos Separados por Fornecedor (Otimizado)")
    
    if not pedidos_por_fornecedor:
        st.error("Não foi possível gerar pedidos. Nenhum produto do carrinho tem preço cadastrado.")
    
    for forn_id, dados in pedidos_por_fornecedor.items():
        # Cria um "card" (expander) para cada fornecedor
        with st.expander(f"🏢 Pedido: {dados['fornecedor_nome']} - Total: R$ {dados['total']:.2f}", expanded=True):
            
            # Mostra a tabela de itens que devem ser comprados dele
            df_exibicao = pd.DataFrame(dados['itens'])
            df_exibicao.columns = ['Produto', 'Qtd', 'Preço Unitário (R$)', 'Subtotal (R$)']
            # Formatação
            df_exibicao['Preço Unitário (R$)'] = df_exibicao['Preço Unitário (R$)'].apply(lambda x: f"R$ {x:.2f}")
            df_exibicao['Subtotal (R$)'] = df_exibicao['Subtotal (R$)'].apply(lambda x: f"R$ {x:.2f}")
            
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
            
            # Verificação CRUCIAL de Logística
            if dados['total'] >= dados['pedido_minimo']:
                st.success(f"✅ Valor atinge o pedido mínimo de R$ {dados['pedido_minimo']:.2f}.")
            else:
                falta = dados['pedido_minimo'] - dados['total']
                st.error(f"⚠️ Atenção! Falta R$ {falta:.2f} para atingir o pedido mínimo deste fornecedor (Min: R$ {dados['pedido_minimo']:.2f}).")

with col2:
    st.subheader("💡 Resumo Estratégico")
    
    if pedidos_por_fornecedor:
        total_geral = sum(dados['total'] for dados in pedidos_por_fornecedor.values())
        st.metric("Total da Compra", f"R$ {total_geral:.2f}")
        
        # Métrica de Ouro: Mostra quanto dinheiro o sistema salvou do usuário
        if economia_total > 0:
            st.metric("Economia Gerada", f"R$ {economia_total:.2f}", delta="Comparado ao fornecedor mais caro", delta_color="normal")
        
        st.markdown("---")
        if st.button("🔄 Limpar Lista e Recomeçar", use_container_width=True):
            st.session_state.carrinho = {}
            st.rerun()

    # Avisa se o usuário pediu algo que não tinha preço cadastrado em lugar nenhum
    if itens_sem_preco:
        st.markdown("---")
        st.warning("⚠️ **Itens ignorados por falta de preço:**")
        for item in itens_sem_preco:
            st.write(f"- {item}")