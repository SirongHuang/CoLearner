import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma


@st.cache_resource(ttl="1h")
def configure_retriever(_docs):
    """
    Configure retriever for RAG model. Split documents, create embeddings and store in vectordb, and define retriever.
    
    - Input: list of documents
    - Output: retriever object
    
    - Splitter: RecursiveCharacterTextSplitter
    - Embeddings: HuggingFaceEmbeddings
    - Vectordb: ChromaDB (save to disk if CHROMADB_PATH provided as env variable, otherwise stores in memory)
    - Retrieval: mmr
    """
    
    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(_docs)

    # Create embeddings and store in vectordb
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    if os.getenv('CHROMADB_PATH'):
        vectordb = Chroma.from_documents(splits, embedding_function, persist_directory=os.getenv('CHROMADB_PATH'))

    else: 
        vectordb = Chroma.from_documents(splits, embedding_function)

    # Define retriever
    retriever = vectordb.as_retriever(search_type="mmr", search_kwargs={"k": 2, "fetch_k": 4})

    return retriever