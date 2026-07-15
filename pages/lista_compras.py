import streamlit as st
import pandas as pd
from database.database import get_connection

st.set_page_config(page_title="Lista de Compras | Assistente de Compras", layout="wide")

st.title("🛒 Montar Lista de Compras")
st.markdown("---")

# Inicializa o "carrinho" na memória do sistema, se não existir
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}

conn = get_connection()
df_produtos = pd.read_sql("SELECT id, nome, marca FROM produtos WHERE ativo = 1", conn)

if df_produtos.empty:
    st.warning("⚠️ Você precisa cadastrar produtos antes de montar uma lista.")
else:
    # Divide a tela: 70% para adicionar itens, 30% para ver o resumo
    col_add, col_resumo = st.columns([7, 3])
    
    with col_add:
        st.subheader("O que está faltando no estoque?")
        
        lista_produtos = df_produtos.apply(lambda row: f"{row['id']} - {row['nome']} ({row['marca']})", axis=1).tolist()
        
        with st.form("form_add_carrinho", clear_on_submit=True):
            c1, c2, c3 = st.columns([5, 2, 2])
            produto_selecionado = c1.selectbox("Selecione o Produto", lista_produtos)
            quantidade = c2.number_input("Quantidade (Caixas/Pacotes)", min_value=1, step=1, value=1)
            
            # Botão centralizado verticalmente com os campos
            st.markdown("<br>", unsafe_allow_html=True)
            btn_add = c3.form_submit_button("➕ Adicionar", type="secondary", use_container_width=True)
            
            if btn_add:
                prod_id = int(produto_selecionado.split(" - ")[0])
                nome_prod = produto_selecionado.split(" - ")[1]
                
                # Se o produto já está na lista, apenas soma a quantidade
                if prod_id in st.session_state.carrinho:
                    st.session_state.carrinho[prod_id]['quantidade'] += quantidade
                else:
                    # Se não está, adiciona um novo registro
                    st.session_state.carrinho[prod_id] = {
                        'nome': nome_prod,
                        'quantidade': quantidade
                    }
                # Rerun para atualizar a tela instantaneamente
                st.rerun()

    with col_resumo:
        st.subheader("Sua Lista 📝")
        
        if not st.session_state.carrinho:
            st.info("Sua lista está vazia. Adicione produtos ao lado.")
        else:
            # Mostra os itens já adicionados
            for prod_id, dados in list(st.session_state.carrinho.items()):
                # Container para alinhar nome, qtd e botão de apagar
                c_texto, c_btn = st.columns([4, 1])
                c_texto.write(f"**{dados['quantidade']}x** {dados['nome']}")
                
                if c_btn.button("❌", key=f"del_{prod_id}", help="Remover item"):
                    del st.session_state.carrinho[prod_id]
                    st.rerun()
            
            st.markdown("---")
            
            # O botão que aciona a "inteligência" do sistema
            st.markdown("Tudo certo com a lista?")
            if st.button("🚀 Calcular Melhor Compra", type="primary", use_container_width=True):
                # Redireciona o usuário para a tela de Pedido (Onde está o motor de decisão)
                st.switch_page("pages/pedido.py")

conn.close()