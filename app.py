import streamlit as st
import psycopg2
import pandas as pd
import time
from datetime import date

# Configuração da página
st.set_page_config(page_title="PULSE", layout="centered")

st.markdown("""
    <style>
    .exercicio-container { border: 1px solid #333; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #1a1a1a; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("PULSE")

DATABASE_URL = "postgresql://postgres.fcinidlhstrvnijrjsym:aKl9XHr8W3VLuICT@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

def conectar():
    return psycopg2.connect(DATABASE_URL)

# Criando as abas
aba_treino, aba_fichas, aba_metricas = st.tabs(["Treino do Dia", "Configurar Ficha", "Métricas e XP"])

# ----------------- ABA 1: TREINO -----------------
with aba_treino:
    data_treino = st.date_input("Data", value=date.today())
    treino_hoje = st.selectbox("Selecione a ficha:", ["Treino A", "Treino B", "Treino C", "Treino D", "Treino E"])
    
    conn = conectar()
    df_preview = pd.read_sql_query("SELECT exercicio, series, repeticoes, imagem_url FROM public.fichas_personal WHERE nome_treino = %s", conn, params=(treino_hoje,))
    conn.close()
    
    with st.expander("Visualizar exercícios da ficha selecionada"):
        if not df_preview.empty:
            for _, row in df_preview.iterrows():
                col1, col2 = st.columns([1, 3])
                if row['imagem_url']: col1.image(row['imagem_url'], width=80)
                col2.write(f"**{row['exercicio']}** - {row['series']}x {row['repeticoes']}")
        else:
            st.write("Ficha vazia.")

    if st.button("Iniciar Descanso (60s)"):
        with st.empty():
            for seconds in range(60, 0, -1):
                st.write(f"Descanso: {seconds} segundos restantes")
                time.sleep(1)
            st.write("Descanso finalizado!")

    if st.button("Carregar Treino"):
        st.session_state['treino_ativo'] = True
    
    if st.session_state.get('treino_ativo'):
        conn = conectar()
        df_exercicios = pd.read_sql_query("SELECT id, exercicio, series, repeticoes, imagem_url FROM public.fichas_personal WHERE nome_treino = %s", conn, params=(treino_hoje,))
        df_memoria = pd.read_sql_query("SELECT exercicio, carga_kg FROM public.historico_treinos ORDER BY data DESC", conn)
        conn.close()

        with st.form("form_treino"):
            resultados = {}
            for i, row in df_exercicios.iterrows():
                mem = df_memoria[df_memoria['exercicio'] == row['exercicio']]
                carga_ant = float(mem.iloc[0]['carga_kg']) if not mem.empty else 0.0
                
                st.markdown(f'<div class="exercicio-container">', unsafe_allow_html=True)
                col_img, col_info, col_input, col_check = st.columns([1, 2, 1, 1])
                if row['imagem_url']: col_img.image(row['imagem_url'], width=60)
                col_info.write(f"**{row['exercicio']}**\n{row['series']}x{row['repeticoes']}")
                carga = col_input.number_input("kg", value=carga_ant, key=f"c_{i}")
                feito = col_check.checkbox("Feito", key=f"ch_{i}")
                resultados[row['exercicio']] = {'carga': carga, 'feito': feito}
                st.markdown('</div>', unsafe_allow_html=True)

            observacao = st.text_area("Observações do treino:")
            
            if st.form_submit_button("Finalizar e Salvar"):
                conn = conectar()
                cur = conn.cursor()
                for ex, dados in resultados.items():
                    if dados['feito']:
                        cur.execute("INSERT INTO public.historico_treinos (data, nome_treino, exercicio, carga_kg, observacao) VALUES (%s, %s, %s, %s, %s)", 
                                    (data_treino, treino_hoje, ex, dados['carga'], observacao))
                conn.commit()
                conn.close()
                st.session_state['treino_ativo'] = False
                st.success("Treino salvo!")
                st.rerun()

# ----------------- ABA 2: CONFIGURAR FICHA -----------------
with aba_fichas:
    st.subheader("Adicionar Exercício")
    with st.form("nova_ficha", clear_on_submit=True):
        n_treino = st.selectbox("Treino", ["Treino A", "Treino B", "Treino C", "Treino D", "Treino E"])
        exer = st.text_input("Exercício")
        ser = st.number_input("Séries", 1)
        rep = st.text_input("Repetições")
        link_img = st.text_input("Link da Imagem")
        if st.form_submit_button("Adicionar"):
            conn = conectar()
            cur = conn.cursor()
            cur.execute("INSERT INTO public.fichas_personal (nome_treino, exercicio, series, repeticoes, imagem_url) VALUES (%s, %s, %s, %s, %s)", (n_treino, exer, ser, rep, link_img))
            conn.commit()
            conn.close()
            st.rerun()
    
    st.divider()
    st.subheader("Seus Treinos Cadastrados")
    
    # Lista os treinos para separar por blocos
    lista_treinos = ["Treino A", "Treino B", "Treino C", "Treino D", "Treino E"]
    
    for t in lista_treinos:
        with st.expander(f"Visualizar {t}"):
            conn = conectar()
            df_t = pd.read_sql_query("SELECT id, exercicio, series, repeticoes FROM public.fichas_personal WHERE nome_treino = %s", conn, params=(t,))
            conn.close()
            
            if not df_t.empty:
                for _, row in df_t.iterrows():
                    col1, col2 = st.columns([5, 1])
                    col1.write(f"{row['exercicio']} - {row['series']}x{row['repeticoes']}")
                    if col2.button("X", key=f"del_{row['id']}"):
                        conn = conectar()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM public.fichas_personal WHERE id = %s", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
            else:
                st.write("Nenhum exercício nesta ficha.")

# ----------------- ABA 3: MÉTRICAS -----------------
with aba_metricas:
    conn = conectar()
    df_h = pd.read_sql_query("SELECT * FROM public.historico_treinos", conn)
    conn.close()
    if not df_h.empty:
        st.line_chart(df_h.pivot(index='data', columns='exercicio', values='carga_kg'))
    else:
        st.write("Sem dados de treino ainda.")