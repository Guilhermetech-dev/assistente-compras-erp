import streamlit as st
import pandas as pd
from database.database import get_connection

st.set_page_config(page_title="Produtos | Assistente de Compras", layout="wide")

st.title("📦 Gestão de Produtos")
st.markdown("---")

# Agora temos 3 abas!
aba_cadastro, aba_lista, aba_editar = st.tabs(["➕ Cadastrar Novo", "📋 Lista de Produtos", "✏️ Editar Produto"])

# ==========================================
# ABA 1: FORMULÁRIO DE CADASTRO
# ==========================================
with aba_cadastro:
    with st.form("form_produto", clear_on_submit=True):
        st.subheader("Informações do Produto")
        
        col1, col2 = st.columns(2)
        codigo_interno = col1.text_input("Código Interno")
        codigo_barras = col2.text_input("Código de Barras")
        
        nome = st.text_input("Nome do Produto * (Obrigatório)")
        
        col3, col4 = st.columns(2)
        marca = col3.text_input("Marca (Ex: Totalplast, Copobras)")
        categoria = col4.selectbox("Categoria", ["Potes", "Copos", "Tampas", "Talheres", "Bandejas", "Sacos", "Outros"])
        
        col5, col6 = st.columns(2)
        unidade = col5.selectbox("Unidade de Venda", ["Caixa", "Fardo", "Pacote", "Milheiro"])
        qtd_por_caixa = col6.number_input("Quantidade por Caixa/Pacote", min_value=1, value=100)
        
        observacoes = st.text_area("Observações (Opcional)")
        
        submit = st.form_submit_button("Salvar Produto", type="primary", use_container_width=True)
        
        if submit:
            if nome.strip() == "":
                st.error("⚠️ O Nome do Produto é obrigatório!")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO produtos (codigo_barras, codigo_interno, nome, marca, categoria, unidade, qtd_por_caixa, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (codigo_barras, codigo_interno, nome, marca, categoria, unidade, qtd_por_caixa, observacoes))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Produto '{nome}' cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ==========================================
# ABA 2: LISTAGEM DE PRODUTOS
# ==========================================
with aba_lista:
    st.subheader("Produtos Cadastrados")
    
    conn = get_connection()
    query = """
        SELECT 
            id as ID, 
            codigo_interno as Código, 
            nome as Nome, 
            marca as Marca, 
            categoria as Categoria, 
            qtd_por_caixa as [Qtd/Caixa] 
        FROM produtos 
        WHERE ativo = 1
    """
    df_produtos = pd.read_sql(query, conn)
    conn.close()
    
    if not df_produtos.empty:
        st.dataframe(df_produtos, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum produto cadastrado ainda.")

# ==========================================
# ABA 3: EDIÇÃO DE PRODUTOS
# ==========================================
with aba_editar:
    st.subheader("Alterar dados de um produto existente")
    
    conn = get_connection()
    df_edit = pd.read_sql("SELECT id, nome, marca FROM produtos WHERE ativo = 1", conn)
    
    if not df_edit.empty:
        # Prepara a lista para o campo de busca
        lista_edit = df_edit.apply(lambda row: f"{row['id']} - {row['nome']} ({row['marca']})", axis=1).tolist()
        produto_selecionado = st.selectbox("🔍 Selecione o produto que deseja alterar:", lista_edit)
        
        # Pega o ID do produto selecionado
        prod_id = int(produto_selecionado.split(" - ")[0])
        
        # Puxa os dados atuais desse produto específico no banco
        cursor = conn.cursor()
        cursor.execute("SELECT codigo_interno, codigo_barras, nome, marca, categoria, unidade, qtd_por_caixa, observacoes FROM produtos WHERE id = ?", (prod_id,))
        dados_atuais = cursor.fetchone()
        
        # Desempacota os dados
        c_int, c_bar, p_nome, p_marca, p_cat, p_un, p_qtd, p_obs = dados_atuais
        
        # O formulário de edição (já preenchido com os valores atuais)
        with st.form("form_editar_produto", clear_on_submit=False):
            col1, col2 = st.columns(2)
            novo_codigo_interno = col1.text_input("Código Interno", value=c_int if c_int else "")
            novo_codigo_barras = col2.text_input("Código de Barras", value=c_bar if c_bar else "")
            
            novo_nome = st.text_input("Nome do Produto *", value=p_nome)
            
            col3, col4 = st.columns(2)
            novo_marca = col3.text_input("Marca", value=p_marca if p_marca else "")
            
            # Descobre o índice da categoria atual para deixar pré-selecionado
            categorias = ["Potes", "Copos", "Tampas", "Talheres", "Bandejas", "Sacos", "Outros"]
            idx_cat = categorias.index(p_cat) if p_cat in categorias else 0
            novo_categoria = col4.selectbox("Categoria", categorias, index=idx_cat)
            
            col5, col6 = st.columns(2)
            unidades = ["Caixa", "Fardo", "Pacote", "Milheiro"]
            idx_un = unidades.index(p_un) if p_un in unidades else 0
            novo_unidade = col5.selectbox("Unidade de Venda", unidades, index=idx_un)
            
            novo_qtd_por_caixa = col6.number_input("Quantidade por Caixa/Pacote", min_value=1, value=int(p_qtd) if p_qtd else 1)
            
            novo_observacoes = st.text_area("Observações (Opcional)", value=p_obs if p_obs else "")
            
            # Botão de salvar alterações
            submit_edit = st.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True)
            
            if submit_edit:
                if novo_nome.strip() == "":
                    st.error("⚠️ O Nome do Produto é obrigatório!")
                else:
                    try:
                        cursor.execute('''
                            UPDATE produtos 
                            SET codigo_interno=?, codigo_barras=?, nome=?, marca=?, categoria=?, unidade=?, qtd_por_caixa=?, observacoes=?
                            WHERE id=?
                        ''', (novo_codigo_interno, novo_codigo_barras, novo_nome, novo_marca, novo_categoria, novo_unidade, novo_qtd_por_caixa, novo_observacoes, prod_id))
                        conn.commit()
                        st.success(f"✅ Produto atualizado com sucesso!")
                        # O st.rerun() força a página a recarregar para atualizar a aba de Lista imediatamente
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")
    else:
        st.info("Nenhum produto cadastrado para editar.")
        
    conn.close()