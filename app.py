import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date

# Configurações iniciais
SUPABASE_URL = "https://ugjzymgczcncnmuabumq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnanp5bWdjemNuY25tdWFidW1xIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM2Mjk3MjgsImV4cCI6MjA1OTIwNTcyOH0.EKW2nwefj8uO9Ie7AuUuoRsdGgIgbN4k3J1wlGXPZp4"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Hospital Jacaré Pereira - Unidade Taboão da Serra", layout="wide")

# Funções auxiliares
def calcular_idade(data_nasc):
    hoje = date.today()
    idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
    return idade

def validar_cpf(cpf):
    cpf = cpf.replace(".", "").replace("-", "").strip()
    return cpf.isdigit() and len(cpf) == 11

def validar_telefone(tel):
    tel = tel.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    return tel.isdigit() and 8 <= len(tel) <= 15

# Estilo customizado com Poppins forçado
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif !important;
        background-color: #f4f6f9;
    }

    .block-container {
        padding: 2rem;
        border-radius: 12px;
        background-color: white;
        box-shadow: 0px 0px 8px rgba(0,0,0,0.1);
    }

    h1, h2, h3 {
        color: #2c3e50;
        font-weight: 600;
        font-family: 'Poppins', sans-serif !important;
    }
    </style>
""", unsafe_allow_html=True)


# Cabeçalho atualizado (nome centralizado, sem cruz azul)
st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="margin-bottom: 0;">Saúde Mais</h1>
    <p style="color: gray; margin-top: 0;">Unidade Taboão da Serra</p>
</div>
""", unsafe_allow_html=True)

# Abas principais
abas = st.tabs(["Cadastrar Paciente", "Consultar Pacientes"])

# Aba de Cadastro
with abas[0]:
    st.markdown("<h2>Cadastro de Paciente</h2>", unsafe_allow_html=True)
    st.info("Se os meses do calendário aparecerem com nomes estranhos, desative o tradutor automático do navegador.")

    with st.form("formulario_cadastro"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome completo do paciente:")
            data_nascimento = st.date_input("Data de Nascimento", min_value=date(1900,1,1), max_value=date.today())
            idade_calculada = calcular_idade(data_nascimento)
            st.write(f"Idade calculada: {idade_calculada} anos")
            raca_cor = st.selectbox("Raça/Cor:", ["Branco", "Pardo", "Preto", "Amarelo", "Indígena", "Não informada"])
            faixa = st.selectbox("Faixa Etária do Paciente:", ["Menor de 20 Anos", "20 a 39 Anos", "40 a 59 Anos", "60 Anos ou mais"])
            cpf = st.text_input("CPF (somente números):", max_chars=14)
            telefone = st.text_input("Telefone para contato:", max_chars=15)
        with col2:
            endereco = st.text_area("Endereço completo:")
            convenio = st.selectbox("Convênio Médico:", ["Não possui", "SUS", "Particular", "Outro"])
            comorbidades = st.multiselect("Comorbidades:", ["Diabetes", "Hipertensão", "Asma", "Cardiopatia", "Nenhuma"])
            sintomas = st.text_area("Sintomas principais / motivo do atendimento:")
            classificacao_risco = st.selectbox("Classificação de risco (Protocolo de Manchester):",
                                               ["Vermelho", "Laranja", "Amarelo", "Verde", "Azul"])

        enviar = st.form_submit_button("Cadastrar")

        if enviar:
            if not nome.strip():
                st.error("Por favor, preencha o nome completo do paciente.")
            elif not validar_cpf(cpf):
                st.error("CPF inválido. Deve conter 11 números.")
            elif not validar_telefone(telefone):
                st.error("Telefone inválido. Informe números válidos (8 a 15 dígitos).")
            else:
                try:
                    data_insercao = {
                        "Nome do Paciente": nome.strip(),
                        "Data de Nascimento": str(data_nascimento),
                        "Data": str(date.today()),
                        "Hora": datetime.now().strftime("%H:%M:%S"),
                        "Idade": idade_calculada,
                        "Raça/Cor": raca_cor,
                        "Faixa Etária": faixa,
                        "CPF": cpf.strip(),
                        "Telefone": telefone.strip(),
                        "Endereço": endereco.strip(),
                        "Convênio Médico": convenio,
                        "Comorbidades": ", ".join(comorbidades) if comorbidades else "Nenhuma",
                        "Sintomas": sintomas.strip(),
                        "Classificação de Risco": classificacao_risco
                    }
                    supabase.table("dengue_table").insert(data_insercao).execute()
                    st.success("\u2705 Paciente cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")

# Aba de Consulta
with abas[1]:
    st.markdown("<h2>Consulta de Pacientes</h2>", unsafe_allow_html=True)

    @st.cache_data(ttl=300)
    def carregar_dados():
        dados = supabase.table("dengue_table").select("*").execute()
        df = pd.DataFrame(dados.data)
        if not df.empty:
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            if 'data' in df.columns:
                df['data'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True).dt.date
        return df

    df = carregar_dados()

    if df.empty:
        st.warning("Nenhum dado encontrado.")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        nome_filtro = st.text_input("Filtrar por Nome:")
    with col2:
        if 'data' in df.columns:
            datas_validas = df['data'].dropna()
            if not datas_validas.empty:
                min_data = datas_validas.min()
                max_data = datas_validas.max()
                data_range = st.date_input(
                    "Filtrar por Data do Atendimento:",
                    value=(min_data, max_data),
                    min_value=min_data,
                    max_value=max_data
                )

    if nome_filtro:
        df = df[df['nome_do_paciente'].apply(lambda x: nome_filtro.lower() in str(x).lower() if pd.notnull(x) else False)]

    if 'data_range' in locals() and len(data_range) == 2:
        df = df[(df['data'] >= data_range[0]) & (df['data'] <= data_range[1])]

    st.subheader(f"Registros encontrados: {len(df)}")
    st.dataframe(df, use_container_width=True)

    st.subheader("Exportar Dados")
    formato = st.selectbox("Formato:", ["CSV", "Excel", "JSON"])

    if st.button("Exportar"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"pacientes_export_{timestamp}"

        if formato == "CSV":
            st.download_button(
                label="Baixar CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name=f"{nome_arquivo}.csv",
                mime="text/csv"
            )
        elif formato == "Excel":
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button(
                label="Baixar Excel",
                data=output.getvalue(),
                file_name=f"{nome_arquivo}.xlsx",
                mime="application/vnd.ms-excel"
            )
        elif formato == "JSON":
            st.download_button(
                label="Baixar JSON",
                data=df.to_json(orient='records').encode('utf-8'),
                file_name=f"{nome_arquivo}.json",
                mime="application/json"
            )
