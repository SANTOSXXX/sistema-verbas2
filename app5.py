import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🕵️ Diagnóstico de Conexão")

try:
    # Tenta conectar
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Tenta ler qualquer coisa da planilha (sem especificar aba)
    st.write("Tentando ler a planilha inteira...")
    df = conn.read()
    
    st.success("✅ Conexão BEM SUCEDIDA!")
    st.write("O Google Sheets retornou os seguintes dados (primeiras linhas):")
    st.dataframe(df.head())

except Exception as e:
    st.error("❌ A conexão falhou.")
    st.error(f"Erro detalhado: {e}")
    
    st.markdown("---")
    st.markdown("### 🛠️ O que verificar agora:")
    st.markdown("""
    1. **Link nos Secrets:** Verifique se o link começa com `https://docs.google.com/spreadsheets/d/` e termina logo depois do ID (antes ou depois do `/edit`).
    2. **Aspas:** Verifique se o link está dentro de aspas duplas `""` no arquivo secrets.
    3. **Permissão:** Confirme se a planilha está como **"Qualquer pessoa com o link"** pode **"Editar"**.
    """)
