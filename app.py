import os
from dotenv import load_dotenv
load_dotenv()

from colearner import chatbot
from colearner.utils import create_folder, save_file, get_file_hash
from colearner.pdf_loader import load_pdf 
from colearner.rag import configure_retriever
from colearner.chatbot import Context_with_History_Chatbot

import streamlit as st

debug = True
if debug:
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~NEW RUN~~~~~~~~~~~~~~~~~~~~~~~~~~~")

##### Create local PDF file dir ##### 
save_file_dir = os.getenv('DATA_FOLDER_PATH') + "uploaded_files/pdf/"
create_folder(save_file_dir)    

##### Setup Streamlit UI ##### 
st.set_page_config(page_title="CoLearner: Chat with your documents", page_icon="🧙")
st.header("🧙 CoLearner: Chat with your documents")

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

##### User uploading PDFs ##### 
uploaded_files = st.sidebar.file_uploader(label='Upload PDF files', type=['pdf'], accept_multiple_files=True)                                                                # stop running the rest of the script if no files are uploaded

##### Setup session states #####
if 'uploaded_file_hashes' not in st.session_state:                            # initiate a session state variable for storing hashes of uploaded files
    st.session_state.uploaded_file_hashes = []
                                                  
if "retriever" not in st.session_state:                                       # initiate a session state variable for storing the retriever
    st.session_state.retriever = configure_retriever(update=False)            # initiate the retriever for the first time
    if debug:
        print("=======   Retriever configured for the first time   =======", '\n')

##### Check for duplicates and save to disk #####    
if uploaded_files:                                                            # when files are uploaded (also when the page is refreshed and there are uploaded files)                                            
    new_file_hash = get_file_hash(uploaded_files[-1])                         # get the hash of the last uploaded file

    if new_file_hash in st.session_state.uploaded_file_hashes:                # --> duplicated upload (avoids re-processing due to duplicated uploads or app refreshes)           
        pass                                                         
    else:                                                                     # --> new upload                                                                  
        st.session_state.uploaded_file_hashes.append(new_file_hash)           # add the new file hash to session state variable
        
        file_path = save_file_dir + uploaded_files[-1].name
        save_file(uploaded_files[-1], file_path)                              # save the file locally

        new_pdf_doc = load_pdf(file_path)                                     # load the new PDF as langchain document    
        
        if debug == True:
            print("=======    id: hashes (should be list of hashes)  =======", '\n')
            print([new_file_hash])
            print("=======    docs (should be list of docs)  =======", '\n')
            print(new_pdf_doc)                                  
        
        st.session_state.retriever = configure_retriever(                     # update the ChromaDB and retriever with the new PDF
                                            hashes = [new_file_hash],                 
                                            docs = new_pdf_doc, 
                                            update=True)
        
    if debug == True:
        print("=======    Uploaded_files   =======", '\n')
        print(uploaded_files)
        print("=======    Embeddings in VectorDB   =======", '\n')
        print(st.session_state.retriever.vectorstore.get())
        print("=======    Session states   =======", '\n')
        print(st.session_state)    
        
##### Create Chatbot #####    
chatbot = Context_with_History_Chatbot(model = "gpt-3.5-turbo")
final_chain = chatbot.get_qa_chain(st.session_state.retriever)

##### Chat interface #####
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
            print(message.content)  
        print("##############################################################################################")

# if st.button('Reset vector database'):
#     pass