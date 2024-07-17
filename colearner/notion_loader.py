""" Dedicated module for loading data from Notion API. Inspired by langchain_community.document_loaders.notiondb.py """

import os
import re
import requests
import random
from typing import Any, Dict, List
from langchain_core.documents import Document
from langchain_community.document_loaders.base import BaseLoader
import ast
from typing import List, Dict, Any
from itertools import groupby
from operator import itemgetter


class NotionLoader(BaseLoader):
    """
    A data class to represent a Notion page. Helps to collect data as progressing goes.
    """
    
    def __init__(self, 
        page_url: str = '',
        notion_api_key: str = '', 
        save_path: str = ''
    ) -> None:
        
        if not page_url:
            raise ValueError("Share link must be provided")
        
        self.page_url = page_url
        self.page_id = self._extract_page_id_from_url(self.page_url)
        self.page_name = self._extract_page_name_from_page_id(self.page_id) #TODO: check if this will generate a random name each time app restarts if the page name is not retrievable
        self.page_text = []
        self.page_children = []
        self.notion_api_key = os.getenv("NOTION_API_KEY") if notion_api_key == '' else notion_api_key
        self.save_path = os.getenv("DATA_DIR")+"/notion_data" if save_path == '' else save_path
    
    
    def _extract_page_id_from_url(self, url:str) -> str:
        """ Extract the page_id from the Notion page share link URL. """
        
        pattern = r"[\?\/\-=]([A-Za-z0-9]+)[?&]pvs=4"
        if match := re.search(pattern, url):
            self.page_id = match.group(1)
        else: 
            raise ValueError("Invalid URL. Please provide a valid Notion page URL.")
        return self.page_id
    
    
    def _extract_page_name_from_page_id(self, page_id) -> str:
        """ Extract the page name from the page_id from Notion API. """
        
        url = f"https://api.notion.com/v1/pages/{self.page_id}"
        headers = {
            "Authorization": f"Bearer {os.getenv('NOTION_API_KEY')}",
            "Notion-Version": "2022-06-28"  # Use the latest API version
        }

        # Make the API request
        response = requests.get(url, headers=headers)
       
        # Extract the page title from the response
        if response.status_code == 200:
            page_data = response.json()
            page_name = page_data["properties"]["title"]["title"][0]["plain_text"]
            return page_name
        else:
            print(f"Error occurred when extracting page name: {response.status_code}\nError message: {response.text}")
            self.page_name = 'NotionPage__id_'+str(random.random())
            print('Generating random page name: ', self.page_name)
        
        return self.page_name
    
    
    def load(self, write_to_file:bool =True) -> List[Document]:
        """ Load data from Notion API. """
        
        file_path = self.save_path+'/'+self.page_name+'.txt'
        
        # recursively search for all texts in the page, and write to a file
        self._recursive_text_search(id = self.page_id, parent = self.page_name, write_to_file=write_to_file)
        
        # load the data from the file into list of dictionaries
        data = self._read_notion_loader_output(file_path)
        
        # group the data by parent key
        grouped_data = self._group_by_key_groupby(data, 'parent')
        
        # create a list of Document objects from the list of dictionaries
        docs = []
        for group in grouped_data:
            subgroup_text = ""
            subgroup = grouped_data[group]
            for item in subgroup:
                if item['type'] != 'child_page':
                    subgroup_text += item['text'] + "\n"
            doc = Document(page_content=subgroup_text, metadata={"source": file_path, "page_name": group})
            docs.append(doc)
        
        return docs
        
        
    def _get_block(self, block_id:str) -> List[Dict[str, Any]]:
        """
        Get the response from the Notion API for a given block_id.
        
        returns:
            dict: json response which represents the block
            
        This output dictionary should contain 'results' which is a list of dictionaries containing the sub-blocks.
        """
        
        url = f"https://api.notion.com/v1/blocks/{block_id}/children"
        
        headers = {
        "Authorization": f"Bearer {self.notion_api_key}",
        "Notion-Version": "2022-06-28"  # Use the latest API version
        }

        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            page_data = response.json()
            return page_data
        else:
            raise Exception(f"Error: {response.status_code}\nError message: {response.text}")
        
        
    def _get_plain_text_from_block(self, block:List[Dict[str, Any]]) -> str:
        """
        Extract plain text from objects that contains text.
        Supported objects: paragraph, heading_1, heading_2, heading_3, bulleted_list_item, 
                        numbered_list_item, to_do, toggle, quote, code, embed
        
        args:   
            block (dict): a dictionary containing the block data
        returns:    
            str: plain text strings if the block contains plain text, 
                return '' otherwise in case of the following errors.
                    - if the block does not have key: type
                    - if the block type is not supported
                    - if the supported block does not have key: rich_text or plain_text
                    - if rich_text is an empty list
        """
        
        block_types_that_contains_text = ['paragraph', 'heading_1', 'heading_2', 'heading_3', 
                                        'bulleted_list_item', 'numbered_list_item', 
                                        'to_do', 'toggle','quote','code','embed']
        
        try:                                                      # If the block does not have a type key, return an empty string
            block_type = block['type']
        except KeyError:
            print('Type key is missing')
            return ''
        
        if block_type in block_types_that_contains_text:          # Check if the block type is one of the supported types that can contain text
            
            try:                                                  # If the block does not have a rich_text key, return an empty string                             
                rich_text = block[block_type]['rich_text']      
            except KeyError:
                print('Rich text key is missing')
                return ''
                
            if block[block_type]['rich_text'] != []:              # Check if the block actually contains text               
                plain_text = rich_text[0].get('plain_text', '')   # If plain_text key is missing, return an empty string
                return str(plain_text)
            else:
                #print('Rich text is empty')
                return ''                                         # If the block does not contain text, return an empty string
        else:
            #print('Unsupported block type:', block_type)         
            return ''
        
        
    def _append_new_data_to_file(self, file_path:str, data_list:List[Dict[str, Any]]) -> None: 
        """
        Appends items from data_list to the file specified by file_path,
        ensuring that only new items (not already in the file) are appended.
        Each new item is written on a new line.
        """
        
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write('')
        
        # Step 1: Read existing content
        with open(file_path, 'r', encoding='utf-8') as file:
            existing_data = file.readlines()
            existing_data = [line.strip() for line in existing_data]  # Remove newline characters

        # Step 2 & 3: Append only new items
        with open(file_path, 'a', encoding='utf-8') as file:
            for item in data_list:
                if str(item) not in existing_data:  # Check if item is new
                    file.write(f"{item}\n")  # Step 4
        
        
    def _append_new_data_to_file_notion(self, base_page:str, data_list:List[Dict[str, Any]]) -> None:
        """Append new data to a file with the name of the base page in Notion data folder. """
        
        os.makedirs(self.save_path, exist_ok=True)    
        self._append_new_data_to_file(file_path=f'{self.save_path}/{base_page}.txt', data_list=data_list)
    
    
    def _recursive_text_search(self, id:str, parent='base', 
                            debug=False, write_to_file=False) -> tuple:
        """
        Search for texts recursively from given a page_id or database_id.
        Write the output to a file if write_to_file is True.
        """
        
        base_blocks = self._get_block(id)['results'] # list of dicts (nested blocks)
        
        # first search text in base blocks
        for block in base_blocks:
                
            text = self._get_plain_text_from_block(block)
            
            # if the block contains text, append it to the output collection
            if text != '' and text != None:
                text_output = {'text': text, 'id': block['id'], 'type': block['type'], 'parent': parent}
                self.page_text.append(text_output)
                
                if debug:
                    print(text_output)
                
                if write_to_file:
                    self._append_new_data_to_file_notion(self.page_name, self.page_text)
        
        # then do recursive search for children pages 
        for block in base_blocks:
            # if the block is children page, append the title text dict to the output collection
            if block['type'] == 'child_page':
                parent = block['child_page']['title']   # set parent variable for the page's child blocks
                children_page = {'text': block['child_page']['title'], 
                                    'id': block['id'], 
                                    'type': block['type'], 
                                    'parent': parent}
                self.page_children.append(children_page)
                self.page_text.append(children_page)
                
                if debug:
                    print('=========child_page==========')
                    print(parent)
                
                if write_to_file:
                    self._append_new_data_to_file_notion(self.page_name, self.page_text)

            if block["has_children"]:
                self._recursive_text_search(id = block["id"], parent = parent, 
                                        debug = debug, write_to_file = write_to_file)
                
        return parent


    def _read_notion_loader_output(self, file_path) -> List[Dict[str, Any]]:
        """ Read data from notion_loader output file and return a list of dictionaries. """
        
        data = []
        with open(file_path,'r', encoding='utf-8') as f: 
            for line in f:
                dict_data = ast.literal_eval(line.strip()) 
                data.append(dict_data)             
        return data


    def _group_by_key_groupby(self, data:List[Dict[str, Any]], key:str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group a list of dictionaries by a specific key using itertools.groupby.
        
        Args:
        data (list): List of dictionaries to group.
        key (str): The key to group by.
        
        Returns:
        dict: A dictionary where keys are the grouped values and values are lists of dictionaries.
        """
        
        sorted_data = sorted(data, key=itemgetter(key))
        
        return {k: list(v) for k, v in groupby(sorted_data, key=itemgetter(key))}
    
