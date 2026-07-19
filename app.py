import streamlit as st
import psycopg2
import pandas as pd
import time
from datetime import date

# Configuração da página e Estilo Customizado
st.set_page_config(page_title="Pulse", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    /* Aplica a fonte apenas em elementos de texto, não em ícones ou botões */
    div, p, h1, h2, h3, h4, h5, h6, span {
        font-family: 'Inter', sans-serif !important;
    }
    
    .exercicio-container { 
        border: 1px solid #444; 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 15px; 
        background-color: #1a1a1a; 
    }
    
    .info-exercicio {
        line-height: 1.6;
    }
    
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("PULSE")

DATABASE_URL = "postgresql://postgres.fcinidlhstrvnijrjsym:aKl9XHr8W3VLuICT@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

def conectar():
    return psycopg2.connect(DATABASE_URL)

aba_treino, aba_fichas, aba_metricas = st.tabs(["Treino do Dia", "Configurar Ficha", "Métricas"])

# ----------------- ABA 1: TREINO -----------------
with aba_treino:
    data_treino = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
    treino_hoje = st.selectbox("Selecione a ficha:", ["Treino A", "Treino B", "Treino C", "Treino D", "Treino E"])
    
    conn = conectar()
    df_preview = pd.read_sql_query("SELECT exercicio, series, repeticoes, imagem_url FROM public.fichas_personal WHERE nome_treino = %s", conn, params=(treino_hoje,))
    conn.close()
    
    with st.expander("Visualizar exercícios da ficha selecionada"):
        if not df_preview.empty:
            for _, row in df_preview.iterrows():
                col1, col2 = st.columns([1, 3])
                img_url = row.get('imagem_url')
                if img_url and isinstance(img_url, str) and len(img_url.strip()) > 5:
                    try:
                        col1.image(img_url, width=80)
                    except:
                        col1.write("Sem imagem")
                else:
                    col1.write("Sem imagem")
                
                # Exibição mais limpa
                col2.markdown(f"<div class='info-exercicio'><strong>{row['exercicio']}</strong><br><small>{row['series']} Séries | {row['repeticoes']} Repetições</small></div>", unsafe_allow_html=True)
        else:
            st.write("Ficha vazia.")

    if st.button("Iniciar Descanso (60s)"):
        with st.empty():
            for seconds in range(60, 0, -1):
                st.write(f"Descanso: {seconds} segundos")
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
                col_info.markdown(f"<strong>{row['exercicio']}</strong><br>{row['series']} x {row['repeticoes']}", unsafe_allow_html=True)
                carga = col_input.number_input("kg", value=carga_ant, key=f"c_{i}")
                feito = col_check.checkbox("Feito", key=f"ch_{i}")
                resultados[row['exercicio']] = {'carga': carga, 'feito': feito}
                st.markdown('</div>', unsafe_allow_html=True)

            observacao = st.text_area("Observações:")
            
            if st.form_submit_button("Salvar Treino"):
                conn = conectar()
                cur = conn.cursor()
                for ex, dados in resultados.items():
                    if dados['feito']:
                        cur.execute("INSERT INTO public.historico_treinos (data, nome_treino, exercicio, carga_kg, observacao) VALUES (%s, %s, %s, %s, %s)", 
                                    (data_treino, treino_hoje, ex, dados['carga'], observacao))
                conn.commit()
                conn.close()
                st.session_state['treino_ativo'] = False
                st.success("Treino salvo com sucesso!")
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
    st.subheader("Seus Treinos")
    lista_treinos = ["Treino A", "Treino B", "Treino C", "Treino D", "Treino E"]
    
    for t in lista_treinos:
        with st.expander(f"Visualizar {t}"):
            conn = conectar()
            df_t = pd.read_sql_query("SELECT id, exercicio, series, repeticoes FROM public.fichas_personal WHERE nome_treino = %s", conn, params=(t,))
            conn.close()
            
            if not df_t.empty:
                for _, row in df_t.iterrows():
                    col1, col2 = st.columns([5, 1])
                    col1.markdown(f"{row['exercicio']} <br><small>{row['series']} séries x {row['repeticoes']} reps</small>", unsafe_allow_html=True)
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
        # Garante que a coluna de data seja datetime
        df_h['data'] = pd.to_datetime(df_h['data'])
        
        # Pivo dos dados
        df_pivot = df_h.pivot(index='data', columns='exercicio', values='carga_kg')
        
        # Formata o índice para exibir como DD/MM/YYYY no gráfico
        df_pivot.index = df_pivot.index.strftime('%d/%m/%Y')
        
        st.line_chart(df_pivot)
    else:
        st.write("Nenhum dado registrado ainda.")