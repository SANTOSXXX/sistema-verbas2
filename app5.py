import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🕵️ Diagnóstico Profundo (Raio-X)")

try:
    # 1. Inicia a conexão
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 2. Pega o link que está salvo nos seus Secrets
    url_salva = st.secrets["connections"]["gsheets"]["spreadsheet"]
    st.write(f"🔗 Analisando link: `{url_salva[:40]}...`")

    # 3. Tenta abrir o arquivo diretamente para ver a estrutura interna
    # Isso usa a biblioteca base (gspread) para "olhar" o arquivo sem converter dados
    arquivo = conn.client.open_by_url(url_salva)
    
    st.success(f"✅ Arquivo Conectado: **{arquivo.title}**")
    
    # 4. Lista EXATAMENTE como as abas se chamam
    st.subheader("📋 Abas encontradas pelo Robô:")
    
    abas = arquivo.worksheets()
    encontrou_lancamentos = False
    
    for aba in abas:
        # Mostra o nome entre aspas para vermos se tem espaço escondido
        st.code(f"Nome real: '{aba.title}'")
        if aba.title == "lancamentos":
            encontrou_lancamentos = True

    st.markdown("---")
    if encontrou_lancamentos:
        st.success("🎉 A aba 'lancamentos' FOI ENCONTRADA! O problema pode ser cache. Clique nos 3 pontinhos > Clear Cache.")
    else:
        st.error("⛔ A aba 'lancamentos' NÃO foi encontrada neste arquivo.")
        st.info("💡 Solução: Se o nome acima for 'Página1' ou 'Sheet1', renomeie na planilha. Se a lista for diferente do que você vê no Google, **você está usando o link do arquivo errado** nos Secrets.")

except Exception as e:
    st.error("❌ Erro Fatal de Conexão.")
    st.write("O Google recusou o link. Isso acontece se:")
    st.write("1. O arquivo ainda é um Excel (.xlsx) e não Planilha Google nativa.")
    st.write("2. O link nos Secrets está errado/cortado.")
    st.error(f"Detalhe do erro: {e}")
