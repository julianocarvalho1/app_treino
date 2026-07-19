import psycopg2

# Link de conexão
DATABASE_URL = "postgresql://postgres.fcinidlhstrvnijrjsym:aKl9XHr8W3VLuICT@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

def conectar():
    return psycopg2.connect(DATABASE_URL)

try:
    conexao = conectar()
    cursor = conexao.cursor()

    # Criação das tabelas no schema public
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS public.fichas_personal (
            id SERIAL PRIMARY KEY,
            nome_treino TEXT NOT NULL, 
            exercicio TEXT NOT NULL,
            series INTEGER,
            repeticoes TEXT,
            imagem_url TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS public.historico_treinos (
            id SERIAL PRIMARY KEY,
            data DATE NOT NULL,
            nome_treino TEXT NOT NULL,
            exercicio TEXT NOT NULL,
            carga_kg REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS public.historico_cardio (
            id SERIAL PRIMARY KEY,
            data DATE NOT NULL,
            tipo TEXT NOT NULL,
            tempo_minutos INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS public.observacoes_diarias (
            id SERIAL PRIMARY KEY,
            data DATE NOT NULL,
            observacao TEXT NOT NULL
        )
    ''')

    conexao.commit()
    cursor.close()
    conexao.close()
    print("Sucesso! Tabelas criadas no Supabase.")

except Exception as e:
    print(f"Erro ao conectar: {e}")