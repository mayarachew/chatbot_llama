import streamlit as st
import openai
from pinecone import Pinecone
import json

# -------------------------
# CONFIGURAÇÃO GROQ E PINECONE
# -------------------------

openai.api_key = st.secrets.get("GROQ_API_KEY")
openai.api_base = "https://api.groq.com/openai/v1"
model_id = "llama-3.3-70b-versatile"

pinecone_api_key = st.secrets.get("PINECONE_API_KEY")

# -------------------------
# CARREGA BASE DE NOTÍCIAS
# -------------------------

with open("database/noticias_g1.json", "r", encoding="utf-8") as f:
    noticias = json.load(f)

# st.write(noticias)

# -------------------------
# GERA EMBEDDINGS
# -------------------------

pc = Pinecone(api_key=pinecone_api_key)

# Criar índice se não existir
index_name = "quickstart-py"

if not pc.has_index(index_name):
    pc.create_index_for_model(
        name=index_name,
        cloud="aws",
        region="us-east-1",
        embed={
            "model":"llama-text-embed-v2",
            "field_map":{"text": "chunk_text"}
        }
    )

# Conectar ao índice
dense_index = pc.Index(index_name)

# Inserir base de noticias
dense_index.upsert_records("noticias-namespace", noticias)

# -------------------------
# FUNÇÃO DE BUSCA
# -------------------------

def buscar_noticias(pergunta, k=10):
    # query_emb = embedding_model.encode(pergunta).tolist()
    # Search the dense index and rerank results
    results = dense_index.search(
        namespace="noticias-namespace",
        query={
            "top_k": k,
            "inputs": {
                'text': pergunta
            }
        }
    )

    docs = []
    for hit in results['result']['hits']:
        docs.append({
            "texto": hit['fields']['chunk_text'],
            "texto_completo": hit['fields']['texto_completo'],
            "link": hit['fields']['link']
        })

    return docs

# -----------------------------
# INTERFACE STREAMLIT - SIDEBAR
# -----------------------------

st.sidebar.title("Fique por dentro das principais notícias do G1 de hoje")
st.sidebar.markdown("A base de dados utilizada contém notícias de que aparecem na página principal no dia 24/09/2025 extraídas por Crawler do G1, envolvendo manchetes principais, tecnologia e economia.")

st.sidebar.markdown("---")
st.sidebar.info("🔹 Projeto de Notícias G1 com RAG e Llama")

# -------------------------------
# INTERFACE STREAMLIT - MAIN PAGE
# -------------------------------

st.markdown("### Chatbot de Notícias G1")

pergunta = st.text_input("Digite sua pergunta:")

if st.button("Perguntar") and pergunta.strip():
    with st.spinner("🔄 Buscando notícias e gerando resposta..."):
        try:
            # Busca notícias mais relevantes
            noticias_relevantes = buscar_noticias(pergunta, k=5)
            contexto_texto = "\n\n".join([f"Titulo: {n['texto']} | (Link: {n['link']}) | Texto completo: {n['texto_completo'][:100]}" for n in noticias_relevantes])

            # Pergunta ao modelo usando contexto
            resposta = openai.ChatCompletion.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "Você é um assistente útil e preciso, que responde perguntas com base nas notícias fornecidas. Sempre inclua links das notícias quando relevante."},
                    {"role": "user", "content": f"Use estas notícias para responder a pergunta abaixo:\n\n{contexto_texto}\n\nPergunta: {pergunta}"}
                ],
                temperature=0.3
            )

            st.markdown("**Resposta:**")
            st.write(resposta["choices"][0]["message"]["content"])

            st.markdown("**Notícias usadas como contexto:**")
            for n in noticias_relevantes:
                st.markdown(f"- [{n['link']}]({n['link']})")

        except Exception as e:
            st.error(f"⚠️ Ocorreu um erro ao consultar o modelo: {e}")

st.markdown("---")
st.markdown("© 2025 - Gabriel Cardoso, Gisele Oliveira, Mayara Chew, Thaisa Guio e Victor Resende \nProjeto de Inteligência Artificial da ADA")
