from dotenv import load_dotenv
from openai import chat
load_dotenv()

from colearner import chatbot
from langchain_core.documents import Document  
from colearner.rag import configure_retriever
from colearner.chatbot import Context_with_History_Chatbot

import streamlit as st


st.set_page_config(page_title="CoLearner: Chat with your documents", page_icon="🧙")
st.title("🧙 CoLearner: Chat with your documents")

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


debug = True

# some toy data 
pdfs = [Document(page_content="My mom's name is Qiu", metadata={"source": "https://mom.com"}),
        Document(page_content="My dad's name is Jun", metadata={"source": "https://dad.com"}),
        Document(page_content="My dog's name is Chong", metadata={"source": "https://dog.com"})]

retriever = configure_retriever(pdfs)

chatbot = Context_with_History_Chatbot()
final_chain = chatbot.get_qa_chain(retriever)


if user_query := st.chat_input(placeholder="Ask me anything!"):
    st.chat_message("human", avatar=chatbot.avatars["human"]).write(user_query)
    
    response = final_chain.stream({'input':user_query}, config={"configurable": {"session_id": 'any'}})
        
    with st.chat_message("ai", avatar=chatbot.avatars["ai"]):
        st.write_stream(chatbot.streaming_output(response))
                    
    if debug:
        print("##############################################################################################")
        print("=======    Context   =======", '\n')
        print(chatbot.relevant_context,'\n')
        print("======= Chat History =======",'\n')
        for message in chatbot.msgs.messages:
            print(message.content)  #Fix: not sure why there is a double printing behavior here... 
        print("##############################################################################################")
