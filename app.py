import streamlit as st
import psycopg2
import pandas as pd
import time
from datetime import date

# Configuracao da pagina
st.set_page_config(page_title="Pulse", layout="centered")

# Inicializa variaveis no session_state
if 'cor_base' not in st.session_state:
    st.session_state.cor_base = '#2A0D0D' 
if 'usuarios_dinamicos' not in st.session_state:
    st.session_state.usuarios_dinamicos = []

# CSS Dinamico
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    .pulse-content {{ font-family: 'Inter', sans-serif !important; }}
    
    .stApp {{
        background-color: {st.session_state.cor_base};
    }}
    
    /* Remove o fundo cinza e a borda padrao dos formularios do Streamlit */
    div[data-testid="stForm"] {{
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
    }}
    
    div[data-testid="stButton"] > button, 
    div[data-testid="stFormSubmitButton"] > button {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }}
    
    div[data-testid="stButton"] > button:hover, 
    div[data-testid="stFormSubmitButton"] > button:hover {{
        background-color: rgba(255, 255, 255, 0.25) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        color: #FFFFFF !important;
    }}
    
    #MainMenu {{visibility: hidden;}} 
    footer {{visibility: hidden;}} 
    header {{background-color: transparent !important;}}
    </style>
""", unsafe_allow_html=True)

DATABASE_URL = "postgresql://postgres.fcinidlhstrvnijrjsym:aKl9XHr8W3VLuICT@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

def conectar():
    return psycopg2.connect(DATABASE_URL)

# ----------------- LOGICA DE USUARIOS -----------------
def get_todos_usuarios():
    try:
        conn = conectar()
        df = pd.read_sql_query("SELECT DISTINCT nome_treino FROM public.fichas_personal", conn)
        conn.close()
        
        users = set(["Juliano"])
        for t in df['nome_treino'].dropna():
            if "_" in t:
                users.add(t.split("_")[0])
                
        for u in st.session_state.usuarios_dinamicos:
            users.add(u)
            
        return sorted(list(users))
    except:
        return ["Juliano"]

def get_nome_treino_db(treino, usuario):
    if usuario == "Juliano":
        return treino
    return f"{usuario}_{treino}"

# ----------------- MENU LATERAL (PERFIL) -----------------
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>Perfil de Usuario</h2>", unsafe_allow_html=True)
    
    lista_usuarios = get_todos_usuarios()
    usuario_ativo = st.selectbox("Quem esta treinando?", lista_usuarios)
    
    st.divider()
    st.markdown("<small>Criar novo perfil:</small>", unsafe_allow_html=True)
    novo_usuario = st.text_input("Nome:", key="input_novo_user")
    if st.button("Adicionar Perfil"):
        if novo_usuario and novo_usuario not in lista_usuarios:
            st.session_state.usuarios_dinamicos.append(novo_usuario)
            st.rerun()

st.markdown("<div class='pulse-content'><h1 style='color: white;'>PULSE</h1></div>", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def carregar_fichas_do_banco(treino_formatado):
    conn = conectar()
    df = pd.read_sql_query("SELECT id, exercicio, series, repeticoes, imagem_url FROM public.fichas_personal WHERE nome_treino = %s", conn, params=(treino_formatado,))
    conn.close()
    return df

@st.cache_data(ttl=600)
def carregar_historico_recente():
    conn = conectar()
    df = pd.read_sql_query("SELECT exercicio, carga_kg, data, nome_treino FROM public.historico_treinos ORDER BY data DESC", conn)
    conn.close()
    return df

# ----------------- FUNCAO VISUAL DOS EXERCICIOS (REDUZIDO PARA MOBILE) -----------------
def renderizar_cartao_exercicio(row, index):
    bg_color = "rgba(255, 255, 255, 0.04)" if index % 2 == 0 else "rgba(255, 255, 255, 0.08)"
    
    img_url = row.get('imagem_url')
    if img_url and isinstance(img_url, str) and len(img_url.strip()) > 5:
        # Imagem reduzida para 60x60px e margens menores
        img_tag = f'<div style="flex-shrink: 0; width: 60px; height: 60px; margin-right: 14px; border-radius: 8px; background-color: white; padding: 2px; display: flex; align-items: center; justify-content: center;"><a href="{img_url}" target="_blank" style="display: block; width: 100%; height: 100%;"><img src="{img_url}" style="width: 100%; height: 100%; object-fit: contain; border-radius: 5px;"></a></div>'
    else:
        img_tag = '<div style="flex-shrink: 0; width: 60px; height: 60px; margin-right: 14px; display:flex; align-items:center; justify-content:center; background:rgba(255,255,255,0.1); border-radius:8px; font-size: 11px; color: rgba(255,255,255,0.6); text-align: center; font-weight: 600;">S/ Foto</div>'
        
    # Fontes, espacamentos e tags de series/reps ajustados para ficarem compactos
    html = f'<div style="display: flex; align-items: center; padding: 12px; border-radius: 12px; margin-bottom: 10px; background-color: {bg_color}; border: 1px solid rgba(255,255,255,0.06); box-shadow: 0 2px 6px rgba(0,0,0,0.1);">{img_tag}<div class="pulse-content" style="line-height: 1.3; color: #FFFFFF; flex-grow: 1;"><div style="font-size: 14px; font-weight: 600; margin-bottom: 8px; letter-spacing: 0.2px;">{row["exercicio"]}</div><div style="display: flex; gap: 8px; font-size: 11px;"><span style="background-color: rgba(255,255,255,0.15); padding: 3px 8px; border-radius: 5px; font-weight: 500;">{row["series"]} Series</span><span style="background-color: rgba(255,255,255,0.15); padding: 3px 8px; border-radius: 5px; font-weight: 500;">{row["repeticoes"]} Reps</span></div></div></div>'
    
    st.markdown(html, unsafe_allow_html=True)

# ----------------- ABAS -----------------
aba_treino, aba_fichas, aba_metricas = st.tabs(["Treino do Dia", "Configurar Ficha", "Metricas"])

# ----------------- ABA 1: TREINO -----------------
with aba_treino:
    col_data, col_cor = st.columns([5, 1])
    with col_data:
        data_treino = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
    with col_cor:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) 
        st.session_state.cor_base = st.color_picker("Cor do Tema", st.session_state.cor_base, label_visibility="collapsed")

    treino_hoje = st.selectbox("Selecione a ficha:", ["Treino A", "Treino B", "Treino C", "Treino D", "Treino E"])
    treino_db = get_nome_treino_db(treino_hoje, usuario_ativo)
    
    df_preview = carregar_fichas_do_banco(treino_db)
    
    with st.expander("Visualizar exercicios da ficha selecionada"):
        if not df_preview.empty:
            for i, row in df_preview.iterrows():
                renderizar_cartao_exercicio(row, i)
        else:
            st.write("Ficha vazia para este perfil.")

    # Controle do Temporizador de Descanso
    st.divider()
    col_tempo, col_btn_descanso = st.columns([2, 3])
    with col_tempo:
        tempo_descanso = st.number_input("Descanso (seg)", min_value=10, value=60, step=10)
    with col_btn_descanso:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button(f"Iniciar Descanso"):
            with st.empty():
                for seconds in range(tempo_descanso, 0, -1):
                    st.write(f"Descanso: {seconds}s")
                    time.sleep(1)
                st.write("Descanso finalizado!")

    st.divider()

    if st.button("Carregar Treino"):
        st.session_state['treino_ativo'] = True
    
    if st.session_state.get('treino_ativo'):
        df_exercicios = carregar_fichas_do_banco(treino_db)
        df_memoria_full = carregar_historico_recente()
        
        treinos_padrao = ["Treino A", "Treino B", "Treino C", "Treino D", "Treino E"]
        if usuario_ativo == "Juliano":
            df_memoria = df_memoria_full[df_memoria_full['nome_treino'].isin(treinos_padrao)]
        else:
            df_memoria = df_memoria_full[df_memoria_full['nome_treino'].str.startswith(f"{usuario_ativo}_", na=False)]

        with st.form("form_treino", border=False):
            resultados = {}
            for i, row in df_exercicios.iterrows():
                mem = df_memoria[df_memoria['exercicio'] == row['exercicio']]
                carga_ant = float(mem.iloc[0]['carga_kg']) if not mem.empty else 0.0
                
                renderizar_cartao_exercicio(row, i)
                
                col_input, col_series, col_check = st.columns([1.5, 1.5, 1])
                carga = col_input.number_input("Carga (kg)", value=carga_ant, key=f"c_{i}")
                series_feitas = col_series.number_input("Series feitas", min_value=0, step=1, value=0, key=f"s_{i}")
                
                st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True) 
                feito = col_check.checkbox("Feito", key=f"ch_{i}")
                
                resultados[row['exercicio']] = {'carga': carga, 'series_feitas': series_feitas, 'feito': feito}
                
                st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)

            # --- SESSAO DE CARDIO ---
            st.markdown("<hr style='border-top: 1px solid rgba(255,255,255,0.1); margin: 25px 0;'>", unsafe_allow_html=True)
            st.markdown("<div class='pulse-content' style='font-size: 18px; font-weight: 600; color: white; margin-bottom: 5px;'>Cardio do Dia</div>", unsafe_allow_html=True)
            
            # Adicionado o titulo "Modalidade" para igualar a altura da caixa "Tempo (min)"
            col_cardio, col_tempo_c = st.columns([2, 1])
            with col_cardio:
                tipo_cardio = st.selectbox("Modalidade", ["Nenhum", "Esteira", "Bike", "Corrida ao ar livre", "Eliptico"])
            with col_tempo_c:
                tempo_cardio = st.number_input("Tempo (min)", min_value=0, step=5, value=0, key="tempo_cardio_input")

            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            observacao = st.text_area("Observacoes gerais:")
            
            # --- BOTAO SALVAR ---
            if st.form_submit_button("Salvar Treino"):
                conn = conectar()
                cur = conn.cursor()
                
                for ex, dados in resultados.items():
                    if dados['feito'] or dados['series_feitas'] > 0:
                        obs_final = f"({dados['series_feitas']} series concluidas) {observacao}" if dados['series_feitas'] > 0 else observacao
                        cur.execute("INSERT INTO public.historico_treinos (data, nome_treino, exercicio, carga_kg, observacao) VALUES (%s, %s, %s, %s, %s)", 
                                    (data_treino, treino_db, ex, dados['carga'], obs_final))
                
                if tipo_cardio != "Nenhum" and tempo_cardio > 0:
                    nome_ex_cardio = f"Cardio: {tipo_cardio}"
                    cur.execute("INSERT INTO public.historico_treinos (data, nome_treino, exercicio, carga_kg, observacao) VALUES (%s, %s, %s, %s, %s)", 
                                (data_treino, treino_db, nome_ex_cardio, tempo_cardio, "Minutos de cardio"))

                conn.commit()
                conn.close()
                st.session_state['treino_ativo'] = False
                st.cache_data.clear()
                st.success("Treino salvo com sucesso!")
                st.rerun()

# ----------------- ABA 2: CONFIGURAR FICHA -----------------
with aba_fichas:
    st.subheader(f"Adicionar Exercicio para {usuario_ativo}")
    with st.form("nova_ficha", clear_on_submit=True, border=False):
        n_treino = st.selectbox("Treino", ["Treino A", "Treino B", "Treino C", "Treino D", "Treino E"])
        exer = st.text_input("Exercicio")
        ser = st.number_input("Series", 1)
        rep = st.text_input("Repeticoes")
        link_img = st.text_input("Link da Imagem")
        
        if st.form_submit_button("Adicionar"):
            treino_db = get_nome_treino_db(n_treino, usuario_ativo)
            conn = conectar()
            cur = conn.cursor()
            cur.execute("INSERT INTO public.fichas_personal (nome_treino, exercicio, series, repeticoes, imagem_url) VALUES (%s, %s, %s, %s, %s)", (treino_db, exer, ser, rep, link_img))
            conn.commit()
            conn.close()
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    st.subheader(f"Treinos de {usuario_ativo}")
    lista_treinos = ["Treino A", "Treino B", "Treino C", "Treino D", "Treino E"]
    for t in lista_treinos:
        with st.expander(f"Visualizar {t}"):
            treino_db = get_nome_treino_db(t, usuario_ativo)
            df_t = carregar_fichas_do_banco(treino_db)
            if not df_t.empty:
                for i, row in df_t.iterrows():
                    renderizar_cartao_exercicio(row, i)
                    if st.button("Remover Exercicio", key=f"del_{row['id']}"):
                        conn = conectar()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM public.fichas_personal WHERE id = %s", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.write("Nenhum exercicio nesta ficha.")

# ----------------- ABA 3: METRICAS -----------------
with aba_metricas:
    st.subheader(f"Progresso de {usuario_ativo}")
    df_memoria_full = carregar_historico_recente()
    
    if not df_memoria_full.empty:
        treinos_padrao = ["Treino A", "Treino B", "Treino C", "Treino D", "Treino E"]
        if usuario_ativo == "Juliano":
            df_h = df_memoria_full[df_memoria_full['nome_treino'].isin(treinos_padrao)].copy()
        else:
            df_h = df_memoria_full[df_memoria_full['nome_treino'].str.startswith(f"{usuario_ativo}_", na=False)].copy()

        if not df_h.empty:
            df_h['data'] = pd.to_datetime(df_h['data'])
            df_pivot = df_h.pivot(index='data', columns='exercicio', values='carga_kg')
            df_pivot.index = df_pivot.index.strftime('%d/%m/%Y')
            st.line_chart(df_pivot)
        else:
            st.write("Nenhum dado registrado ainda para este perfil.")
    else:
        st.write("Banco de dados vazio.")