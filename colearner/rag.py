import os
import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb
from colearner.utils import runtime
import time


@runtime
@st.spinner("Processing data for your Chatbot...")
def configure_retriever(docs:list = [], hashes:list = [], update:bool = False):
    """
    Configure retriever for RAG model. Split documents, create embeddings and store in vectordb, and define retriever.
    - Splitter: RecursiveCharacterTextSplitter
    - Embeddings: HuggingFaceEmbeddings
    - Vectordb: ChromaDB (save to disk if CHROMADB_PATH provided as env variable, otherwise stores in memory)
    - Retrieval: mmr
    ---------------------------------------------------
    - Input: 
        - _docs: list of documents
        - hashes: list of hashes of the documents used as unique ids
        - update (default=True): if True, create or update the vectordb with new documents, otherwise load the existing vectordb. 
    - Output: retriever object
    """
    # Define the chromaDB client
    start_time = time.time()
    
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    elapsed_time = time.time() - start_time
    print(f"Elapsed time for embedding_function: {elapsed_time} seconds")
    
    start_time = time.time()
    
    persistent_client = chromadb.PersistentClient(path=os.getenv('CHROMADB_PATH'))
    elapsed_time = time.time() - start_time
    print(f"Elapsed time for persistent_client: {elapsed_time} seconds")
    
    start_time = time.time()
    
    vectordb = Chroma(
        client=persistent_client,
        collection_name="collection_name",
        embedding_function=embedding_function,
    )
    
    elapsed_time = time.time() - start_time
    print(f"Elapsed time for creating vectordb: {elapsed_time} seconds")
    
    if update:
        start_time = time.time()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        
        elapsed_time = time.time() - start_time
        print(f"Elapsed time for creating text splittings: {elapsed_time} seconds")
        
        start_time = time.time()
        vectordb.add_documents(ids=hashes, documents=docs)
        
        elapsed_time = time.time() - start_time
        print(f"Elapsed time for adding documents to vectordb: {elapsed_time} seconds")
    
    
    retriever = vectordb.as_retriever(search_type="mmr", search_kwargs={"k": 2, "fetch_k": 4})
    
    print("Retriever configured successfully!")
    
    return retriever


