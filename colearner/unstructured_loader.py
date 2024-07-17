from colearner.utils import runtime

from langchain_community.document_loaders import UnstructuredFileLoader

@runtime
def unstructured_loader(file_paths):
    """ Load unstructured files into Langchain Documents from the given list of paths. """
    
    loader = UnstructuredFileLoader(file_paths, mode="single")
    docs = loader.load()
    
    return docs