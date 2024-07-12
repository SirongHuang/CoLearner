from langchain_community.document_loaders import PyPDFLoader

def load_pdf(pdf_path:str) -> list:
    """Load a PDF file and return a list of documents."""
    loader = PyPDFLoader(pdf_path)
    doc = loader.load()
    return doc