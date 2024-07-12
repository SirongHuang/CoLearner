import streamlit as st
from colearner.rag import configure_retriever

from langchain_openai import ChatOpenAI

from langchain_core.documents import Document   
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory, StreamlitChatMessageHistory 
from langchain_core.runnables.history import RunnableWithMessageHistory


class Context_with_History_Chatbot:
    """ Streamlit Chatbot with context and history-awareness """
    
    def __init__(self, model = "gpt-3.5-turbo" ):
        self.llm = ChatOpenAI(model=model, temperature=0)
        self.relevant_context = None 
        self.msgs = StreamlitChatMessageHistory("chat_history")   # streamlit chat message history 
        self.avatars = {"human":"🤯", "ai":"🤖"}
        self.display_Streamlit_chat_history()

    def display_Streamlit_chat_history(self):
        if len(self.msgs.messages) == 0:
            self.msgs.add_ai_message("How can I help you?")
            
        for msg in self.msgs.messages:
            st.chat_message(msg.type, avatar=self.avatars[msg.type]).write(msg.content)
        
    def get_qa_chain(self, retriever):
        """ Get the question answering chain with chat history and context docs """

        history_aware_retriever_system_prompt = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", history_aware_retriever_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(self.llm, 
                                                                 retriever, 
                                                                 contextualize_q_prompt)
        
        qa_system_prompt = """You are an assistant for question-answering tasks. \
        Use the following pieces of retrieved context and given chat history to answer the question. \
        If you don't know the answer, just say that you don't know. \
        Use three sentences maximum and keep the answer concise.\

        {context}"""
        
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)    # retrieve relevant docs
        qa_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)  # question answering chain with chat history and context docs
        
        final_chain = RunnableWithMessageHistory(
            qa_chain,
            lambda session_id: self.msgs,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        return final_chain
    
    def streaming_output(self, response):
        """ Process the streaming output from the chain as text """
        text = ''
        i = 0 
        for chunk in response:
            if i == 1:
                self.relevant_context = chunk['context']
            if i >= 2: 
                text = chunk['answer']
                yield text + " "
            i += 1
            
