import os
import re
import random
from dotenv import load_dotenv
load_dotenv()
from posthog import page
import streamlit as st
from colearner import chatbot
from colearner.utils import create_folder, save_file, get_file_hash, all_items_exist
from colearner.pdf_loader import load_pdf 
from colearner.rag import configure_retriever
from colearner.chatbot import Context_with_History_Chatbot
from colearner.unstructured_loader import load_unstructured_file   
from colearner.notion_loader import NotionLoader

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
    print("=======   ...Configuring retriever after app restart...   =======", '\n') 
    st.session_state.retriever = configure_retriever(update=False)              

# raw doc ids from the vectorstore, e.g., 'hash-0', 'hash-1', 'hash-2'                                                      #TODO: is session state the best way to store these values?
st.session_state.doc_ids = list(set([id.split('-')[0] for id in st.session_state.retriever.vectorstore.get()['ids']]))

# doc names from the vectorstore, duplication due to multiple docs of the same document                             
st.session_state.doc_names = [st.session_state.retriever.vectorstore.get(id+'-0')['metadatas'][0]['source'].split('/')[-1] 
                                for id in st.session_state.doc_ids]

if 'checkboxes' not in st.session_state:
    st.session_state.checkboxes = [True] * len(st.session_state.doc_ids)

if 'file_uploader_key' not in st.session_state:
    st.session_state.file_uploader_key = 'default'

# -------------- functions to manage session states -------------

def reset_file_uploader():
    """ Resets the file uploader key to force uploaded_files to be cleared. """
    st.session_state.file_uploader_key = str(st.session_state.file_uploader_key) + str(random.random())    

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


# --------------- file uploader: local files ---------------
                                                           
with st.sidebar.form("my-form", clear_on_submit=True):
    uploaded_files = st.file_uploader("📃File Uploader",  
                                       key=st.session_state.file_uploader_key, accept_multiple_files=True)
    st.write("Formats: PDF, microsoft docs, images, audio, txt, csv, xls, json, html, epub...")
    submitted = st.form_submit_button("Upload")
    
    print("===========   Session states:   ===========")    
    for key, value in st.session_state.items():
        print(key, ":", value)


# ---------------- file uploader: notion API ----------------

expand = st.sidebar.expander("📚 Notion",                            
                                expanded=False) 
if notion_id := st.sidebar.text_input("Notion Page ID"):
    if notion_name := st.sidebar.text_input("Write a name for the page"):
        page = NotionLoader(page_id=notion_id, page_name=notion_name)
    else:
        page = NotionLoader(page_id=notion_id)
    page.recursive_text_search(id = page.page_id, parent = page.page_name, write_to_file=True)
      
# ------------------------------------------------------------
#
#                    Document management UI
#
# ------------------------------------------------------------                                                                

# ------------------------ sidebar UI ------------------------

expand = st.sidebar.expander("📚 Manage Documents",                            
                                expanded=True) 
expand.write("Select the documents you want to chat with. ")
    
    
# -------------- buttons to manage all checkboxes --------------    

button_col1, button_col2, button_col3 = expand.columns(3)

if button_col1.button('Deselect'):                                                                  
    st.session_state.checkboxes = [False] * len(st.session_state.checkboxes)
if button_col2.button('Select'):                                                                   
    st.session_state.checkboxes = [True] * len(st.session_state.checkboxes)
if button_col3.button('Remove'):       
    form = st.form(key='confirmation_box')
    name = form.text('❗❗❗ Are you sure you want to delete all docs?')
    submit = form.form_submit_button('Yes')
    if submit:                                            
        st.session_state.checkboxes = [True] * len(st.session_state.checkboxes)
        try:
            for i in range(len(st.session_state.doc_ids)+1):
                delete_document(i)
        except:
            pass
        st.rerun()    


# -------------- create checkboxes on app restart from vectorDB docs --------------

checkbox_col1, checkbox_col2 = expand.columns([0.8,0.2], vertical_alignment='top')  

# Loop through all the documents in the vectorDB and create a checkbox for each
for i, (id, doc_name) in enumerate(zip(st.session_state.doc_ids, st.session_state.doc_names)):           
    if len(st.session_state.checkboxes) > 0:
        checkbox_col1.checkbox(key=id,                                                               
                        label=doc_name, 
                        value=st.session_state.checkboxes[i])

        # create a delete button for each checkbox
        if checkbox_col2.button("✖", key=f"delete_{i}", type='primary'):                                                                                                       
            delete_document(i)
            st.rerun()    

        
# ------------------------------------------------------------
#
#               New Uploaded File Processing
#
# ------------------------------------------------------------       
            
if uploaded_files:                                                                                               
    
    save_file_dir = os.getenv('DATA_DIR') + "uploaded_files/pdf/"
    create_folder(save_file_dir)  
    
    new_file_hashes = [get_file_hash(file) for file in uploaded_files]     
    new_file_names = [file.name for file in uploaded_files]      
    reset_file_uploader()                                                              # Reset the file uploader to avoid reprocessing 
    
    if all_items_exist(new_file_hashes, st.session_state.doc_ids):                     # If none of the uploaded files are new, skip all processing         
        print("Duplicated upload detected. Skipping the processing.",'\n')           
    
    else:                                                                              # For non-duplicated new file, process it as follows: 
        print("Some of the uploaded files are not in VectorDB. Processing...",'\n')        
                                                               
                                                                                      
        for file, new_file_hash, new_file_name in zip(uploaded_files, new_file_hashes, new_file_names):    
            if new_file_hash not in st.session_state.doc_ids:                          # If the new file is already in the vectorDB, skip it               
                file_path = save_file_dir + new_file_name                               
                save_file(file, file_path)                                                         # 1. save the file locally

                if file_path.endswith('.pdf'):                                                     # 2. load the new PDF as langchain document 
                    new_pdf_doc = load_pdf(file_path)     
                else:                                            
                    new_pdf_doc = load_unstructured_file(file_path)                                #TODO: slow for loading single file, change logic to multi-file
                                          
                try:
                    st.session_state.retriever = configure_retriever(                              # 3. update the ChromaDB and retriever 
                                                        doc_hash = new_file_hash,                 
                                                        docs = new_pdf_doc, 
                                                        update=True)
                except Exception as e:
                    print("Error occurred when updating the retriever with the new PDF.")
                    print(e)                                                                       
                    
                st.session_state.doc_ids.append(new_file_hash)                                     # 4. update the session states                    
                st.session_state.checkboxes.append(True)
                st.session_state.doc_names.append(new_file_name)
                
                print("=======    Updating checkbox UI   =======")
                print(f"There are {len(st.session_state.checkboxes)} checkboxes.")    
                print("Their ids are: ", st.session_state.doc_ids)        
                print("Their names are: ", st.session_state.doc_names)       
                
                k = len(st.session_state.checkboxes)                        
                print(f"Created the new {k}th checkbox.")
                checkbox_col1.checkbox(key=new_file_hash,                                          # 5. update the checkbox UI                
                                    label=new_file_name, 
                                    value=True)          
                if checkbox_col2.button("✖", key=f"delete_{k}", type='primary'):                                                                          
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
