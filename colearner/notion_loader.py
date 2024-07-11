""" Dedicated module for loading data from Notion API. """

import os
import requests

from dataclasses import dataclass, field

NOTION_API_KEY = os.getenv("NOTION_API_KEY")


@dataclass
class NotionPage:
    """
    A data class to represent a Notion page. Helps to collect data as progressing goes.
    """
    page_id: str                                       # id of the base page
    page_name: str                                     # name of the base page
    page_text: list = field(default_factory=list)      # list of dictionaries containing the page text with metadata,
                                                            # in the format of {'text': '...', 'id': '...', 'type': '...', 'parent': '...'}
    page_children: list = field(default_factory=list)  # list of dictionaries containing the page children with metadata,
                                                            # in the format of {'text': '...', 'id': '...', 'type': '...', 'parent': '...'}


def get_block(block_id:str) -> dict:
    """
    Get the response from the Notion API for a given block_id.
    
    returns:
        dict: json response which represents the block
        
    This output dictionary should contain 'results' which is a list of dictionaries containing the sub-blocks.
    """
    
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    
    headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28"  # Use the latest API version
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        page_data = response.json()
        return page_data
    else:
        raise Exception(f"Error: {response.status_code}\nError message: {response.text}")
    
    
def get_plain_text_from_block(block:dict) -> str:
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
    
    
def append_new_data_to_file(file_path:str, data_list:list) -> None: 
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
    
    
def append_new_data_to_file_notion(base_page:str, data_list:list) -> None:
    """Append new data to a file with the name of the base page in Notion data folder. """
    
    notion_data_path = os.getenv('NOTION_DATA_PATH')  # set this data path in .env file
    os.makedirs(notion_data_path, exist_ok=True)    
    append_new_data_to_file(file_path=f'{notion_data_path}/{base_page}.txt', data_list=data_list)


def recursive_text_search(page:NotionPage, 
                          id:str, parent='base', 
                          debug=False, 
                          write_to_file=False) -> tuple:
    """
    Search for texts recursively from given a page_id or database_id. 
    """
    
    base_blocks = get_block(id)['results'] # list of dicts (nested blocks)
    
    # first search text in base blocks
    for block in base_blocks:
            
        text = get_plain_text_from_block(block)
        
        # if the block contains text, append it to the output collection
        if text != '' and text != None:
            text_output = {'text': text, 'id': block['id'], 'type': block['type'], 'parent': parent}
            page.page_text.append(text_output)
            
            if debug:
                print(text_output)
            
            if write_to_file:
                append_new_data_to_file_notion(page.page_name, page.page_text)
    
    # then do recursive search for children pages 
    for block in base_blocks:
        # if the block is children page, append the title text dict to the output collection
        if block['type'] == 'child_page':
            parent = block['child_page']['title']   # set parent variable for the page's child blocks
            children_page = {'text': block['child_page']['title'], 
                                'id': block['id'], 
                                'type': block['type'], 
                                'parent': parent}
            page.page_children.append(children_page)
            page.page_text.append(children_page)
            
            if debug:
                print('=========child_page==========')
                print(parent)
            
            if write_to_file:
                append_new_data_to_file_notion(page.page_name, page.page_text)

        if block["has_children"]:
            recursive_text_search(page = page, id = block["id"], parent = parent, 
                                    debug = debug, write_to_file = write_to_file)
            
    return parent



    
    
