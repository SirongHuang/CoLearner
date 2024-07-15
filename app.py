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
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~NEW RUN~~~~~~~~~~~~~~~~~~~~~~~~~~~", '\n')


##### Create save_dir ##### 
save_file_dir = os.getenv('DATA_FOLDER_PATH') + "uploaded_files/pdf/"
create_folder(save_file_dir)    


##### UI: basic setup ##### 
st.set_page_config(page_title="CoLearner: Chat with your documents", page_icon="🧙")
st.header("🧙 CoLearner: Chat with your documents")

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


##### UI: User uploading PDFs ##### 
uploaded_files = st.sidebar.file_uploader(label='Upload PDF files', type=['pdf'], accept_multiple_files=True)                                                                # stop running the rest of the script if no files are uploaded


##### Setup session states #####
if "retriever" not in st.session_state:                                          
    print("=======   Retriever configured for the first time   =======", '\n') 
    st.session_state.retriever = configure_retriever(update=False)              

if "unique_doc_ids" not in st.session_state:                                     
    st.session_state.unique_doc_ids = list(set([id.split('-')[0] for id in st.session_state.retriever.vectorstore.get()['ids']]))

if 'checkboxes' not in st.session_state:
    st.session_state.checkboxes = [True] * len(st.session_state.unique_doc_ids)

##### UI: create checkbox for managing docs in vectorDB #####
vectorDB_doc_names = [st.session_state.retriever.vectorstore.get(id+'-0')['metadatas'][0]['source'].split('/')[-1] 
                             for id in st.session_state.unique_doc_ids]
                                                                                    
expand = st.sidebar.expander("Manage Documents",                            
                                icon=":material/folder_open:") 
expand.write("Select the documents you want to chat with.")
    
col1, col2 = expand.columns(2)
if col1.button('Deselect all'):                                                           # Creates a button to deselect all checkboxes
    st.session_state.checkboxes = [False] * len(st.session_state.checkboxes)
if col2.button('Select all'):                                                             # Creates a button to select all checkboxes
    st.session_state.checkboxes = [True] * len(st.session_state.checkboxes)

for i, (id, doc_name) in enumerate(zip(st.session_state.unique_doc_ids,vectorDB_doc_names)):    # Creates a checkbox for each document     
    expand.checkbox(key=id,                                                               
                    label=doc_name, 
                    value=st.session_state.checkboxes[i],
                    on_change=lambda value, i=i: st.session_state.checkboxes.__setitem__(i, not st.session_state.checkboxes[i]),
                    args=(i,))

##### If a new file is uploaded, or when app refreshes + uploaded file exists: #####    
if uploaded_files:                                                               #TODO: this part requires testing to make sure it's not running unnecessarily or should run when needed                                  
    new_file_hash = get_file_hash(uploaded_files[-1])                           
    
    if new_file_hash in st.session_state.unique_doc_ids:                         # For duplicated file, checked against VectorDB         
        print("Duplicated upload detected. Skipping the processing.",'\n')       # skip all processing 
        pass
    else:                                   
        print("Uploaded file not in VectorDB. Processing...",'\n')               # For non-duplicated new file,      
        file_path = save_file_dir + uploaded_files[-1].name
        save_file(uploaded_files[-1], file_path)                                    # 1. save the file locally

        new_pdf_doc = load_pdf(file_path)                                           # 2. load the new PDF as langchain document    
        
        if debug == True:
            print("=======    ID & Name of the new file   =======")
            print(new_file_hash,'\n', uploaded_files[-1].name, '\n')
            print("=======    Docs   =======")
            print("Total number of documents in the PDF: ", len(new_pdf_doc))
            print("Here is part of the content of first doc: ", '\n')
            print(new_pdf_doc[0].page_content[200:], '\n')    
                                                           
        try:
            st.session_state.retriever = configure_retriever(                       # 3. update the ChromaDB and retriever 
                                                doc_hash = new_file_hash,                 
                                                docs = new_pdf_doc, 
                                                update=True)
        except Exception as e:
            print("Error occurred when updating the retriever with the new PDF.")
            print(e)
                                                                                    # 4. query the VectorDB with doc unique id & get file name    
               
        doc_name = st.session_state.retriever.vectorstore.get(new_file_hash+'-0')['metadatas'][0]['source'].split('/')[-1] 
                                                                                    
        expand.checkbox(key=new_file_hash, label=doc_name, value=True)              # 5. update the app UI to include the new doc in vecotorDB
        
        
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
