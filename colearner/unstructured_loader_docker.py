from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_core.documents import Document
from typing import List
import sys

def aggregate_documents(docs: List[Document]) -> List[Document]:
    """
    Aggregate document contents by filename and page number.
    
    Args:   
        docs: list of dictionaries, each dictionary contains the following keys:
            - 'page_content': str
            - 'metadata': dict, containing the following keys:
                - 'filename': str,
                - 'current_page_number': int
                
        list of dictionaries, each dictionary contains the following:
            - 'page_content': str
            - 'metadata': dict, containing the following keys:
                - 'source': str, the file name of the document
                - 'current_page_number': int
    """
    
    output = []

    for i, doc in enumerate(docs):
        current_file_name  = doc.metadata['filename']
        current_page_number = doc.metadata['page_number']
        if i == 0:
            prev_file_name = current_file_name
            prev_page_number = current_page_number
            page_contents = [doc.page_content]

        page_contents.append(doc.page_content)
        
        # aggregate file content when a new file or page starts, or at the end of the list (for the last doc)
        if current_page_number != prev_page_number or current_file_name != prev_file_name or i == len(docs)-1:
            print(f"Aggregating file: {prev_file_name}, page: {prev_page_number}",'\n')

            # 1. append the aggregated doc to the output
            aggregated_doc = Document(page_content=' '.join(page_contents), 
                                        metadata={'source': prev_file_name, 'page_number': prev_page_number})
            output.append(aggregated_doc)
            
            print(aggregated_doc,'\n')
            
            # 2. change the prev values to the new values and reset the page_contents
            prev_file_name = current_file_name
            prev_page_number = current_page_number
            page_contents = []        

            
    return output


def load_unstructured_files(temp_file_name: str) -> List[Document]:
    """ 
    Load unstructured files and return a list of Langchain Documents containing the page content and metadata.

    Args:
        temp_file_path: str, the path to a text file containing the file paths of the files to be loaded.
        
    Returns:
        list of langchain documents with metadata of page number and file name.
    """
    with open('data/uploaded_files/tmp/' + temp_file_name, 'r') as f:           #TODO: change how path is defined
        filepaths = ['data/uploaded_files/'+line.replace('\n','') for line in f.readlines()]
    print("Accessing filepaths", filepaths)
    
    loader = UnstructuredFileLoader(filepaths, mode='elements')
    raw_docs = loader.load()
    docs = aggregate_documents(raw_docs)
        
    return docs
    
    
    
if __name__ == "__main__":
    print("=======================Starting Unstructured Loader=======================")
    tmp_file_name_arg = sys.argv[1]
    docs = load_unstructured_files(tmp_file_name_arg)
    
