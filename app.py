from distutils.command import upload
import os
import re
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from colearner import chatbot
from colearner.utils import create_folder, save_file, get_file_hash
from colearner.pdf_loader import load_pdf 
from colearner.rag import configure_retriever
from colearner.chatbot import Context_with_History_Chatbot


debug = True
if debug:
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~NEW RUN~~~~~~~~~~~~~~~~~~~~~~~~~~~", '\n')

# ------------------------------------------------------------
#
#                       Basic UI Setup 
#
# ------------------------------------------------------------

# ------------------------ app title ------------------------

st.set_page_config(page_title="CoLearner: Chat with your documents", page_icon="🧙")
st.header("🧙 CoLearner: Chat with your documents")

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    
# ---------------------- session states ----------------------

if "retriever" not in st.session_state:                                          
    print("=======   Retriever configured for the first time   =======", '\n') 
    st.session_state.retriever = configure_retriever(update=False)              
           
# raw doc ids from the vectorstore, e.g., 'hash-0', 'hash-1', 'hash-2'                          
st.session_state.doc_ids = list(set([id.split('-')[0] for id in st.session_state.retriever.vectorstore.get()['ids']]))

# doc names from the vectorstore, duplication due to multiple docs of the same document                             
st.session_state.doc_names = [st.session_state.retriever.vectorstore.get(id+'-0')['metadatas'][0]['source'].split('/')[-1] 
                                for id in st.session_state.doc_ids]

if 'checkboxes' not in st.session_state:
    st.session_state.checkboxes = [True] * len(st.session_state.doc_ids)


# ---------------------- file uploader ----------------------
                                                           
with st.sidebar.form("my-form", clear_on_submit=True):
    uploaded_files = st.file_uploader("FILE UPLOADER",  accept_multiple_files=True)
    submitted = st.form_submit_button("Upload")

# ------------------------------------------------------------
#
#                    Document management UI
#
# ------------------------------------------------------------                                                                


# ------------------------- sidebar -------------------------

expand = st.sidebar.expander("Manage Documents",                            
                                icon=":material/folder_open:") 
expand.write("Select the documents you want to chat with.")
    
    
# -------------- buttons to manage all checkboxes --------------    
    
button_col1, button_col2 = expand.columns(2)
if button_col1.button('Deselect all'):                                                                  
    st.session_state.checkboxes = [False] * len(st.session_state.checkboxes)
if button_col2.button('Select all'):                                                                   
    st.session_state.checkboxes = [True] * len(st.session_state.checkboxes)


# -------------- function to delete single checkbox --------------

def delete_document(delete_index):
    """ Deletes the document from the vectorDB and updates the UI. """                                                              
    print(f"Delete button clicked on {delete_index}")
    
    pattern = f'^{re.escape(st.session_state.doc_ids[delete_index])}-'
    
    all_ids = st.session_state.retriever.vectorstore.get()['ids']
    ids_to_delete = [id for id in all_ids if re.match(pattern, id)]
    
    if ids_to_delete:
        st.session_state.retriever.vectorstore.delete(ids=ids_to_delete)
        print(f"Deleted {len(ids_to_delete)} documents matching the pattern: {pattern}")
    else:
        print(f"No documents found matching the pattern: {pattern}")
    
    st.session_state.doc_ids.pop(delete_index)
    st.session_state.checkboxes.pop(delete_index)
    st.session_state.doc_names.pop(delete_index)


# -------------- create checkboxes on app restart from vectorDB docs --------------

checkbox_col1, checkbox_col2 = expand.columns([5,1])  

for i, (id, doc_name) in enumerate(zip(st.session_state.doc_ids, st.session_state.doc_names)):           # Creates a checkbox for each document   
    
    print(i, id, doc_name, st.session_state.doc_ids[i], st.session_state.doc_names[i], st.session_state.checkboxes[i])
    checkbox_col1.checkbox(key=id,                                                               
                    label=doc_name, 
                    value=st.session_state.checkboxes[i])
                    
    if checkbox_col2.button("✖", key=f"delete_{i}"):                                                     # Creates a delete button for each document                                                  
        delete_document(i)
        st.experimental_rerun()    


# ------------------------------------------------------------
#
#               New Uploaded File Processing
#
# ------------------------------------------------------------       

# If a new file is uploaded, or when app refreshes + uploaded file exists  
if uploaded_files:                                                               #TODO: this part requires testing to make sure it's not running unnecessarily or should run when needed                                  
    
    save_file_dir = os.getenv('DATA_FOLDER_PATH') + "uploaded_files/pdf/"
    create_folder(save_file_dir)  
    
    new_file_hash = get_file_hash(uploaded_files[-1])     
    new_file_name = uploaded_files[-1].name           
    
    if new_file_hash in st.session_state.doc_ids:                                # For duplicated file, checked against VectorDB         
        print("Duplicated upload detected. Skipping the processing.",'\n')           # skip all processing 
        #uploaded_files = []
    
    else:                                   
        print("Uploaded file not in VectorDB. Processing...",'\n')               # For non-duplicated new file, process it as follows:    
        file_path = save_file_dir + new_file_name
        save_file(uploaded_files[-1], file_path)                                      # 1. save the file locally

        new_pdf_doc = load_pdf(file_path)                                             # 2. load the new PDF as langchain document    
        
        if debug == True:
            print("=======    ID & Name of the new file   =======")
            print(new_file_hash,'\n', new_file_name, '\n')
            print("=======    Docs   =======")
            print("Total number of documents in the PDF: ", len(new_pdf_doc))
            print("Here is part of the content of first doc: ", '\n')
            print(new_pdf_doc[0].page_content[50:], '\n')    
                                                           
        try:
            st.session_state.retriever = configure_retriever(                         # 3. update the ChromaDB and retriever 
                                                doc_hash = new_file_hash,                 
                                                docs = new_pdf_doc, 
                                                update=True)
        except Exception as e:
            print("Error occurred when updating the retriever with the new PDF.")
            print(e)                                                                       
               
        st.session_state.doc_ids.append(new_file_hash)                                # 4. update the session states                    
        st.session_state.checkboxes.append(True)
        st.session_state.doc_names.append(new_file_name)
                
        k = len(st.session_state.checkboxes)                        
        print(f"Created the {k}th checkbox.")
        checkbox_col1.checkbox(key=new_file_hash,                                     # 5. update the checkbox UI                
                               label=new_file_name, 
                               value=True)          
        if checkbox_col2.button("✖", key=f"delete_{k}"):                                                                          
            delete_document(i)
            st.rerun()                                          
                                            

# ------------------------------------------------------------
#
#               Create Chatbot and RAG chain
#
# ------------------------------------------------------------     
 
chatbot = Context_with_History_Chatbot(model = "gpt-3.5-turbo")
final_chain = chatbot.get_qa_chain(st.session_state.retriever)


# ------------------------------------------------------------
#
#                        Chatbot UI
#
# ------------------------------------------------------------     

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
