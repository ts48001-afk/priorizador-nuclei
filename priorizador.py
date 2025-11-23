# Thiago Pereira da Silva
# Lucas Metodio
# Victor Donega
# Cintia Ramos


import os
import json
import pandas as pd
from subprocess import Popen, PIPE
import uuid


# ------------------------------------------------------------
# Função para rodar o Nuclei com json-export
# ------------------------------------------------------------
def executar_nuclei(host):
    temp_name = f"nuclei_{uuid.uuid4().hex}.json"

    comando = [
        "nuclei",
        "-u", host,
        "-as",
        "-json-export", temp_name
    ]

    print(f"🚀 Executando Nuclei em: {host}")
    proc = Popen(comando, stdout=PIPE, stderr=PIPE, text=True)
    stdout, stderr = proc.communicate()

    # Nuclei gera um arquivo JSON ao invés de imprimir no terminal
    if not os.path.exists(temp_name):
        print("❌ Nuclei não gerou arquivo JSON (0 achados ou erro).")
        return []

    try:
        with open(temp_name, "r") as f:
            dados = json.load(f)
    except:
        print("❌ Erro ao ler o JSON exportado.")
        dados = []

    os.remove(temp_name)
    return dados

# ------------------------------------------------------------
# Carregar inventário
# ------------------------------------------------------------
try:
    inventario = pd.read_csv("inventario.csv")
    print("📘 Inventário carregado com sucesso!")
    print(inventario)
    print()
except FileNotFoundError:
    print("❌ ERRO: O arquivo 'inventario.csv' não foi encontrado!")
    exit()

todos_achados = []

# ------------------------------------------------------------
# Executar Nuclei para cada host
# ------------------------------------------------------------
for _, linha in inventario.iterrows():
    host = linha["host"]
    criticidade = linha["criticidade"]

    resultados = executar_nuclei(host)

    if len(resultados) == 0:
        print(f"✔ 0 vunerabilidades encontradas.\n")
        continue

    print(f"🔎 {len(resultados)} vunerabilidades encontradas!\n")

    for r in resultados:
        r["host"] = host
        r["criticidade_host"] = criticidade
        todos_achados.append(r)

# ------------------------------------------------------------
# Resultado final
# ------------------------------------------------------------
if len(todos_achados) == 0:
    print("⚠ Nenhum achado encontrado em nenhum host!")
    exit()

df = pd.DataFrame(todos_achados)

df.to_csv("resultado_priorizado.csv", index=False)
df.to_json("resultado_priorizado.json", orient="records", indent=4)

print("✅ Arquivos gerados:")
print(" - resultado_priorizado.csv")
print(" - resultado_priorizado.json")

# ------------------------------------------------------------
# Ordenação por prioridade
# ------------------------------------------------------------
# ------------------------------------------------------------
# Ordenação por prioridade
# ------------------------------------------------------------
print("\n📌 Sequência de Prioridade dos Achados:")
print("=======================================")

# Se não houver achados, sair elegantemente
if df.empty:
    print("⚠ Nenhum achado encontrado — impossível calcular prioridade.")
    print("=======================================\n")
    exit()

# Peso de severidade
peso = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1
}

# Se a coluna "severity" não existir, criar com "info"
if "severity" not in df.columns:
    df["severity"] = "info"

# Normalizar
df["severity"] = df["severity"].fillna("info").astype(str).str.lower()

# Adicionar coluna de peso
df["peso_severidade"] = df["severity"].apply(lambda s: peso.get(s, 1))

# Ordenar: severidade e criticidade do host
df_ordenado = df.sort_values(
    by=["peso_severidade", "criticidade_host"],
    ascending=[False, False]
)

# Exibir no terminal
for _, r in df_ordenado.iterrows():
    print(f"""
🔻 PRIORIDADE: {r['severity'].upper()} | Host Crit: {r['criticidade_host']}
    🖥 Host: {r['host']}
    📌 Template: {r.get('template-id', 'N/A')}
    📝 Nome: {r.get('name', 'N/D')}
    🌐 Afeta: {r.get('matched-at', 'N/A')}
    """)

print("=======================================")
print("📊 Prioridade calculada com sucesso!\n")

print("\n🎉 Processo finalizado com sucesso!")
