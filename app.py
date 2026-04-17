import os
import re
from pathlib import Path

import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_text_splitters import CharacterTextSplitter
from transformers import pipeline


FALLBACK_RESPONSE = "Not mentioned in hostel rules."
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_REPO_ID = "google/flan-t5-base"

PDF_PATH = Path(__file__).with_name("code_of_conduct.pdf")
API_TOKEN_PATH = Path(__file__).with_name("hostel chatbot api.txt")


st.set_page_config(page_title="Hostel Chatbot")
st.title("🏠 Hostel Code of Conduct Chatbot")
st.write("Ask anything about hostel rules")


def get_hf_token() -> str:
    env_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")
    if env_token:
        return env_token.strip()

    if API_TOKEN_PATH.exists():
        token = API_TOKEN_PATH.read_text(encoding="utf-8").strip()
        if token:
            return token

    return ""


@st.cache_resource
def build_vectorstore() -> FAISS:
    loader = PyPDFLoader(str(PDF_PATH))
    documents = loader.load()

    splitter = CharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return FAISS.from_documents(chunks, embeddings)


@st.cache_resource
def build_qa_chain(_vectorstore: FAISS) -> RetrievalQA:
    hf_token = get_hf_token()
    generation_pipeline = pipeline(
        task="text2text-generation",
        model=LLM_REPO_ID,
        tokenizer=LLM_REPO_ID,
        token=hf_token or None,
        max_new_tokens=128,
        temperature=0.1,
    )
    llm = HuggingFacePipeline(pipeline=generation_pipeline)

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are a hostel rules assistant. Use only the context to answer. "
            "If the answer is not in the context, reply exactly: 'Not mentioned in hostel rules.'\n\n"
            "Keep the answer short and clear. Do not add outside facts.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n"
            "Answer:"
        ),
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=_vectorstore.as_retriever(search_kwargs={"k": TOP_K}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )


def _is_context_backed(answer: str, context: str) -> bool:
    answer_tokens = set(re.findall(r"[a-zA-Z]{3,}", answer.lower()))
    context_tokens = set(re.findall(r"[a-zA-Z]{3,}", context.lower()))

    if not answer_tokens or not context_tokens:
        return False

    overlap_ratio = len(answer_tokens & context_tokens) / max(1, len(answer_tokens))
    return overlap_ratio >= 0.15


def enforce_grounded_response(chain_result: dict) -> str:
    source_docs = chain_result.get("source_documents") or []
    answer = str(chain_result.get("result", "")).strip()

    context_parts = []
    for doc in source_docs:
        content = getattr(doc, "page_content", "")
        if content and content.strip():
            context_parts.append(content.strip())

    context_text = "\n".join(context_parts).strip()
    if not context_text:
        return FALLBACK_RESPONSE

    if not answer:
        return FALLBACK_RESPONSE

    answer_lower = answer.lower()
    if answer_lower == FALLBACK_RESPONSE.lower():
        return FALLBACK_RESPONSE

    uncertain_markers = (
        "not sure",
        "cannot determine",
        "don't know",
        "do not know",
        "no information",
        "not provided",
        "not mentioned",
        "unknown",
    )
    if any(marker in answer_lower for marker in uncertain_markers):
        return FALLBACK_RESPONSE

    if not _is_context_backed(answer, context_text):
        return FALLBACK_RESPONSE

    return answer


if not PDF_PATH.exists():
    st.error(f"PDF file not found: {PDF_PATH.name}")
    st.stop()

try:
    vectorstore = build_vectorstore()
    qa_chain = build_qa_chain(vectorstore)
except Exception as exc:
    st.error(f"Chatbot initialization failed: {exc}")
    st.stop()


query = st.text_input("💬 Ask your question:")

if query and query.strip():
    try:
        raw_result = qa_chain.invoke({"query": query.strip()})
        response = enforce_grounded_response(raw_result)
    except Exception as exc:
        st.error(f"Unable to process your question: {exc}")
    else:
        st.subheader("🤖 Answer")
        st.write(response)