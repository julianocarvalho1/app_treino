import psycopg2

DATABASE_URL = "postgresql://postgres.fcinidlhstrvnijrjsym:aKl9XHr8W3VLuICT@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

try:
    conn = psycopg2.connect(DATABASE_URL)
    print("CONEXÃO ESTABELECIDA COM SUCESSO!")
    conn.close()
except Exception as e:
    print(f"ERRO DE CONEXÃO: {e}")