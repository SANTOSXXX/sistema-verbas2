import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- Configuração da Página ---
st.set_page_config(page_title="Gestão de Verbas (Web)", layout="wide")

# --- CREDENCIAIS DE ACESSO ---
USUARIOS = {
    "admin": {"senha": "123", "nome": "Administrador", "permissao": "admin"},
    "gv1":   {"senha": "gv1", "nome": "Gerente de Vendas 1", "permissao": "GV 1"},
    "gv2":   {"senha": "gv2", "nome": "Gerente de Vendas 2", "permissao": "GV 2"},
    "gv3":   {"senha": "gv3", "nome": "Gerente de Vendas 3", "permissao": "GV 3"},
}

# --- CSS Personalizado ---
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.3);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: inherit;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- Funções Auxiliares ---
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- CONEXÃO COM GOOGLE SHEETS ---
# Agora vai funcionar porque o arquivo é nativo!
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados(aba):
    """Lê uma aba específica da planilha e retorna um DataFrame"""
    try:
        # ttl=0 garante dados frescos
        df = conn.read(worksheet=aba, ttl=0)
        return df
    except Exception as e:
        st.error(f"⚠️ Erro ao ler a aba '{aba}'.")
        return pd.DataFrame()

def salvar_registro(aba, novo_dado_dict):
    """Lê a planilha, adiciona uma linha e salva de volta"""
    try:
        df = carregar_dados(aba)
        novo_df = pd.DataFrame([novo_dado_dict])
        df_atualizado = pd.concat([df, novo_df], ignore_index=True)
        conn.update(worksheet=aba, data=df_atualizado)
        st.toast("Dados salvos na nuvem! ☁️", icon="✅")
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

def excluir_registro(aba, index_para_excluir):
    """Exclui uma linha baseada no Index do DataFrame"""
    try:
        df = carregar_dados(aba)
        df_atualizado = df.drop(index_para_excluir)
        conn.update(worksheet=aba, data=df_atualizado)
        return True
    except Exception as e:
        st.error(f"Erro ao excluir: {e}")
        return False

# ==========================================
# LOGIN
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = {}

def login():
    st.markdown("<h1 style='text-align: center;'>☁️ Gestão Web</h1>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
                    st.session_state.logged_in = True
                    st.session_state.user_info = USUARIOS[usuario]
                    st.rerun()
                else: st.error("Acesso negado.")

def logout():
    st.session_state.logged_in = False
    st.rerun()

# ==========================================
# APP PRINCIPAL
# ==========================================
if not st.session_state.logged_in:
    login()
else:
    user_name = st.session_state.user_info['nome']
    user_perm = st.session_state.user_info['permissao']
    
    st.sidebar.markdown(f"### 👤 {user_name}")
    if st.sidebar.button("Sair"): logout()
    st.sidebar.markdown("---")
    st.title("📊 Gestão de Verbas (Online)")

    tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "📝 Lançamento", "⚙️ Gerenciar"])

    # Carrega dados
    df_lanc = carregar_dados("lancamentos")
    df_limites = carregar_dados("limites")
    df_clientes = carregar_dados("clientes")

    # --- TAB 1: DASHBOARD ---
    with tab1:
        # Se a planilha estiver vazia, cria um DataFrame vazio com as colunas certas para não dar erro
        if df_lanc.empty:
             st.info("Nenhum lançamento encontrado ainda.")
        else:
            # Tratamento de dados
            if 'data' in df_lanc.columns:
                df_lanc['data'] = pd.to_datetime(df_lanc['data'], errors='coerce').dt.date
            if 'valor' in df_lanc.columns:
                df_lanc['valor'] = pd.to_numeric(df_lanc['valor'], errors='coerce').fillna(0)
            
            c1, c2 = st.columns([1, 1])
            # Garante que existem anos/meses antes de criar o selectbox
            anos = sorted(df_lanc["ano"].unique()) if "ano" in df_lanc.columns and not df_lanc["ano"].isnull().all() else [datetime.now().year]
            meses = sorted(df_lanc["mes"].unique()) if "mes" in df_lanc.columns and not df_lanc["mes"].isnull().all() else [datetime.now().month]
            
            with c1: ano = st.selectbox("Ano", anos, index=len(anos)-1)
            with c2: mes = st.selectbox("Mês", list(range(1, 13)), index=datetime.now().month-1)

            # Filtra dados
            if "ano" in df_lanc.columns and "mes" in df_lanc.columns:
                dff = df_lanc[(df_lanc["ano"] == ano) & (df_lanc["mes"] == mes)]
            else:
                dff = pd.DataFrame()

            # Busca Metas
            meta_c, meta_n = 0.0, 0.0
            if not df_limites.empty and "ano" in df_limites.columns:
                lim_atual = df_limites[(df_limites["ano"] == ano) & (df_limites["mes"] == mes)]
                if not lim_atual.empty:
                    mc = lim_atual[lim_atual["categoria"] == "Cerveja"]["valor_limite"]
                    mn = lim_atual[lim_atual["categoria"] == "NAB (Refrigerantes)"]["valor_limite"]
                    meta_c = float(mc.iloc[0]) if not mc.empty else 0.0
                    meta_n = float(mn.iloc[0]) if not mn.empty else 0.0

            # Totais e KPIs
            tot_c = dff[dff["categoria"]=="Cerveja"]["valor"].sum() if not dff.empty and "categoria" in dff.columns else 0.0
            tot_n = dff[dff["categoria"]=="NAB (Refrigerantes)"]["valor"].sum() if not dff.empty and "categoria" in dff.columns else 0.0

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Gasto Cerveja", formatar_real(tot_c))
            k2.metric("Meta Cerveja", formatar_real(meta_c))
            k3.metric("Gasto NAB", formatar_real(tot_n))
            k4.metric("Meta NAB", formatar_real(meta_n))
            
            st.markdown("---")
            
            # Gráficos
            g1, g2 = st.columns(2)
            def plot_gauge(val, lim, tit):
                saldo = lim - val
                cor = "red" if saldo < 0 else "blue"
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val, title={'text': tit},
                    gauge={'axis': {'range': [None, max(lim*1.2, val*1.1)]}, 'bar': {'color': cor},
                           'threshold': {'line': {'color': "red", 'width': 4}, 'value': lim}}))
                fig.add_annotation(x=0.5, y=0.25, text=f"Saldo: {formatar_real(saldo)}", showarrow=False)
                fig.update_layout(height=280, margin=dict(l=20,r=20,t=40,b=20))
                return fig

            with g1: st.plotly_chart(plot_gauge(tot_c, meta_c, "Cerveja"), use_container_width=True)
            with g2: st.plotly_chart(plot_gauge(tot_n, meta_n, "NAB"), use_container_width=True)
            
            st.dataframe(dff, use_container_width=True)

    # --- TAB 2: LANÇAMENTO ---
    with tab2:
        st.header("Novo Lançamento")
        col_b, _ = st.columns([1, 2])
        cod_input = col_b.text_input("Cód. Cliente")
        nome_auto, setor_auto = "", ""
        
        if cod_input and not df_clientes.empty and "Codigo" in df_clientes.columns:
            # Conversão para string para garantir match
            df_clientes['Codigo'] = df_clientes['Codigo'].astype(str).str.strip().str.replace('.0', '')
            cod_limpo = str(cod_input).strip()
            
            cli = df_clientes[df_clientes['Codigo'] == cod_limpo]
            if not cli.empty:
                nome_auto = cli.iloc[0]['Nome_Fantasia']
                setor_auto = cli.iloc[0]['Setor']
                st.success(f"Cliente: {nome_auto}")
            else:
                st.warning("Não encontrado na aba 'clientes'.")

        with st.form("form_lcto", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            dt = c1.date_input("Data", datetime.now())
            idx_gv = 0
            dis_gv = False
            if user_perm == "GV 1": idx_gv, dis_gv = 0, True
            elif user_perm == "GV 2": idx_gv, dis_gv = 1, True
            gv = c1.selectbox("GV", ["GV 1", "GV 2"], index=idx_gv, disabled=dis_gv)
            cat = c2.selectbox("Categoria", ["Cerveja", "NAB (Refrigerantes)"])
            val = c3.number_input("Valor R$", min_value=0.0, step=10.0)
            cli_nome = c2.text_input("Nome Cliente", value=nome_auto)
            setor = c3.text_input("Setor", value=setor_auto)
            obs = st.text_area("Motivo")

            if st.form_submit_button("Salvar na Nuvem"):
                if val > 0:
                    novo_reg = {
                        "data": str(dt), "mes": dt.month, "ano": dt.year,
                        "gv": gv, "categoria": cat, "valor": val,
                        "negociacao": obs, "codigo_cliente": cod_input,
                        "cliente": cli_nome, "setor": setor
                    }
                    salvar_registro("lancamentos", novo_reg)
                    time.sleep(1)
                    st.rerun()
                else: st.error("Valor inválido")

    # --- TAB 3: GERENCIAR ---
    with tab3:
        st.header("Gerenciar")
        if not df_lanc.empty:
            st.dataframe(df_lanc.tail(15), use_container_width=True)
            idx_del = st.number_input("Index para excluir:", min_value=0, step=1)
            if st.button("🗑️ Excluir Registro"):
                if idx_del in df_lanc.index:
                    excluir_registro("lancamentos", idx_del)
                    st.success("Excluído!")
                    time.sleep(1)
                    st.rerun()
                else: st.error("Índice não existe.")

