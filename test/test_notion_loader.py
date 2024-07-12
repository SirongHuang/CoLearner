import pytest
from unittest.mock import Mock, patch
from colearner.notion_loader import NotionLoader  # Adjust the import path as necessary

@pytest.fixture
def notion_loader():
    return NotionLoader()

############ Test cases for get_plain_text_from_block ############
class Test_Plain_Text_Extractor:
    def test_text_block_with_plain_text(self, notion_loader):
        block = {
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'plain_text': 'Hello, world!'}]
            }
        }
        assert notion_loader.get_plain_text_from_block(block) == 'Hello, world!'
        
    def test_block_without_type(self, notion_loader):
        block = {
            'paragraph': {
                'rich_text': [{'plain_text': 'Hello, world!'}]
            }
        }
        assert notion_loader.get_plain_text_from_block(block) == ''

    def test_rich_text_key_missing(self, notion_loader):
        block = {
            'type': 'paragraph',
            'paragraph': {
            }
        }
        assert notion_loader.get_plain_text_from_block(block) == ''
        
    def test_plain_text_key_missing(self, notion_loader):
        block = {
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'unsupported_key': 'This should not be returned'}]
            }
        }
        assert notion_loader.get_plain_text_from_block(block) == ''
        
    def test_empty_rich_text_list(self, notion_loader):
        block = {
            'type': 'paragraph',
            'paragraph': {
                'rich_text': []
            }
        }
        assert notion_loader.get_plain_text_from_block(block) == ''
        
    def test_empty_plain_text_list(self, notion_loader):
        block = {
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'plain_text': ''}]
            }
        }
        assert notion_loader.get_plain_text_from_block(block) == ''
        
    def test_plain_text_is_not_str(self, notion_loader):
        block = {
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'plain_text': 123}]
            }
        }
        assert notion_loader.get_plain_text_from_block(block) == '123'
        
    def test_plain_text_is_not_str2(self, notion_loader):
        block = {
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'plain_text': ['1', '2', '3']}]
            }
        }
        assert notion_loader.get_plain_text_from_block(block) == str(['1', '2', '3'])

    def test_unsupported_block_type(self, notion_loader):
        block = {
            'type': 'unsupported_type',
            'unsupported_type': {
                'rich_text': [{'plain_text': 'This should not be returned'}]
            }
        }
        assert notion_loader.get_plain_text_from_block(block) == ''
    
    
############ Test cases for recursive_text_search and related functions and class ############    

# Mock data for get_block
mock_get_block_data = {
    'results': [
        {
            'type': 'random_block',
            'id': 'random_block_id',
            'has_children': False
        },
        {
            'type': 'base_text_block_1',
            'id': 'base_text_block_id_1',
            'has_children': False
        },
        {
            'type': 'child_page',
            'id': 'child_page_id',
            'child_page': {'title': 'Child Page Title'},
            'has_children': True
        },
        {
            'type': 'base_text_block_2',
            'id': 'base_text_block_id_2',
            'has_children': False
        }
    ]
}

# Mock data for nested child blocks
mock_get_block_data_nested = {
    'results': [
        {
            'type': 'text_block',
            'id': 'nested_text_block_id',
            'has_children': False
        }
    ]
}

# Mock the return value of get_plain_text_from_block
mock_plain_text = {
    'base_text_block_id_1': 'Sample text in base text block 1',
    'base_text_block_id_2': 'Sample text in base text block 2',
    'nested_text_block_id': 'Nested sample text'
}

# Mock functions
mock_get_block = Mock(side_effect=lambda id: mock_get_block_data_nested if id == 'child_page_id' else mock_get_block_data)
mock_get_plain_text_from_block = Mock(side_effect=lambda block: mock_plain_text.get(block['id'], ''))
mock_append_new_data_to_file_notion = Mock()

@pytest.fixture
def setup_mocks():
    with patch('colearner.notion_loader.NotionLoader.get_block', mock_get_block), \
         patch('colearner.notion_loader.NotionLoader.get_plain_text_from_block', mock_get_plain_text_from_block), \
         patch('colearner.notion_loader.NotionLoader.append_new_data_to_file_notion', mock_append_new_data_to_file_notion):
        yield


def test_recursive_text_search_basic(setup_mocks):
    page = NotionLoader(page_id = 'root_id', page_name='base')
    page.recursive_text_search(id = page.page_id, parent = page.page_name)
    print(page.page_text)
    
    assert len(page.page_text) == 4
    assert page.page_text[0] == {
        'text': 'Sample text in base text block 1',
        'id': 'base_text_block_id_1',
        'type': 'base_text_block_1',
        'parent': 'base'
    }
    assert page.page_text[1] == {
        'text': 'Sample text in base text block 2',
        'id': 'base_text_block_id_2',
        'type': 'base_text_block_2',
        'parent': 'base'
    }
    assert page.page_text[2] == {
        'text': 'Child Page Title',
        'id': 'child_page_id',
        'type': 'child_page',
        'parent': 'Child Page Title'
    }
    assert page.page_text[3] == {
        'text': 'Nested sample text',
        'id': 'nested_text_block_id',
        'type': 'text_block',
        'parent': 'Child Page Title'
    }
    
def test_recursive_text_search_with_write_to_file(setup_mocks):
    """ Check if append_new_data_to_file_notion writes correct number of lines to output file."""
    page = NotionLoader(page_id = 'root_id', page_name='base')
    page.recursive_text_search(id = page.page_id, parent = page.page_name, write_to_file=True)

    assert mock_append_new_data_to_file_notion.called
    assert mock_append_new_data_to_file_notion.call_count == 4

