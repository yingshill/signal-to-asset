"""Tests for create_asset.py — property building, content truncation, block construction, dedup."""
import pytest
from unittest.mock import patch, call
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import create_asset as ca


MOCK_CREATED_PAGE = {'id': 'asset-id-001', 'url': 'https://notion.so/asset-001'}
MOCK_EXISTING_PAGE = {
    'id': 'asset-id-existing',
    'url': 'https://notion.so/asset-existing',
    'properties': {
        'Channel': {'type': 'select', 'select': {'name': 'LinkedIn'}},
        'Type': {'type': 'select', 'select': {'name': 'Post'}},
    },
}


class TestFindExistingAsset:
    @patch('create_asset.DB_IDS', {'marketing_assets': ''})
    def test_returns_none_when_db_id_missing(self):
        assert ca.find_existing_asset('any name') is None

    @patch('create_asset.query_database', return_value=[MOCK_EXISTING_PAGE])
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_returns_page_when_found(self, mock_db):
        result = ca.find_existing_asset('MCP is the new API — LinkedIn (PM)')
        assert result['id'] == 'asset-id-existing'
        mock_db.assert_called_once_with(
            'real-db-id',
            filter_obj={'property': 'Asset Name', 'title': {'equals': 'MCP is the new API — LinkedIn (PM)'}},
        )

    @patch('create_asset.query_database', return_value=[])
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_returns_none_when_not_found(self, mock_db):
        assert ca.find_existing_asset('Unknown Asset') is None

    @patch('create_asset.query_database', return_value=[MOCK_EXISTING_PAGE])
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_scopes_lookup_by_project_when_provided(self, mock_db):
        result = ca.find_existing_asset('MCP is the new API — LinkedIn (PM)', 'proj-123')
        assert result['id'] == 'asset-id-existing'
        mock_db.assert_called_once_with(
            'real-db-id',
            filter_obj={
                'and': [
                    {'property': 'Asset Name', 'title': {'equals': 'MCP is the new API — LinkedIn (PM)'}},
                    {'property': 'Project', 'relation': {'contains': 'proj-123'}},
                ],
            },
        )


class TestCreateAsset:
    BASE_DATA = {
        'asset_name': 'MCP is the new API — LinkedIn (PM)',
        'type': 'Post',
        'channel': 'LinkedIn',
        'hook': 'This is the hook',
        'content': 'This is the content body.',
        'topic': ['AI', 'Workflow'],
    }

    @patch('create_asset.find_existing_asset', return_value=MOCK_EXISTING_PAGE)
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_returns_existing_without_creating(self, mock_find):
        result = ca.create_asset(self.BASE_DATA)
        assert result['action'] == 'existing'
        assert result['asset_id'] == 'asset-id-existing'
        assert result['content_truncated'] is False

    @patch('create_asset.find_existing_asset', return_value=None)
    @patch('create_asset.create_page', return_value=MOCK_CREATED_PAGE)
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_creates_when_not_found(self, mock_create, mock_find):
        result = ca.create_asset(self.BASE_DATA)
        assert result['action'] == 'created'
        assert result['asset_id'] == 'asset-id-001'
        mock_create.assert_called_once()

    @patch('create_asset.find_existing_asset', return_value=None)
    @patch('create_asset.create_page', return_value=MOCK_CREATED_PAGE)
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_returns_expected_fields(self, mock_create, mock_find):
        result = ca.create_asset(self.BASE_DATA)
        assert result['asset_name'] == 'MCP is the new API — LinkedIn (PM)'
        assert result['channel'] == 'LinkedIn'
        assert result['type'] == 'Post'

    @patch('create_asset.find_existing_asset', return_value=None)
    @patch('create_asset.create_page', return_value=MOCK_CREATED_PAGE)
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_topic_as_string_wrapped_in_list(self, mock_create, mock_find):
        data = {**self.BASE_DATA, 'topic': 'AI'}
        ca.create_asset(data)
        props = mock_create.call_args[0][1]
        assert props['Topic'] == {'multi_select': [{'name': 'AI'}]}

    @patch('create_asset.find_existing_asset', return_value=None)
    @patch('create_asset.create_page', return_value=MOCK_CREATED_PAGE)
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_content_truncated_at_1900_chars(self, mock_create, mock_find):
        data = {**self.BASE_DATA, 'content': 'x' * 2000}
        result = ca.create_asset(data)
        props = mock_create.call_args[0][1]
        content_val = props['Content']['rich_text'][0]['text']['content']
        assert len(content_val) == 1900
        assert result['content_truncated'] is True

    @patch('create_asset.find_existing_asset', return_value=None)
    @patch('create_asset.create_page', return_value=MOCK_CREATED_PAGE)
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_content_not_truncated_when_short(self, mock_create, mock_find):
        result = ca.create_asset(self.BASE_DATA)
        assert result['content_truncated'] is False

    @patch('create_asset.find_existing_asset', return_value=None)
    @patch('create_asset.create_page', return_value=MOCK_CREATED_PAGE)
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_project_id_added_as_relation(self, mock_create, mock_find):
        data = {**self.BASE_DATA, 'project_id': 'proj-123'}
        ca.create_asset(data)
        props = mock_create.call_args[0][1]
        assert props['Project'] == {'relation': [{'id': 'proj-123'}]}
        mock_find.assert_called_once_with('MCP is the new API — LinkedIn (PM)', 'proj-123')

    @patch('create_asset.find_existing_asset', return_value=None)
    @patch('create_asset.create_page', return_value=MOCK_CREATED_PAGE)
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_no_children_when_no_content(self, mock_create, mock_find):
        data = {'asset_name': 'Test — LinkedIn (PM)', 'type': 'Post', 'channel': 'LinkedIn'}
        ca.create_asset(data)
        children = mock_create.call_args[0][2]
        assert children is None

    @patch('create_asset.find_existing_asset', return_value=None)
    @patch('create_asset.create_page', return_value=MOCK_CREATED_PAGE)
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_carousel_brief_adds_children(self, mock_create, mock_find):
        data = {**self.BASE_DATA, 'carousel_brief': 'Design brief here'}
        ca.create_asset(data)
        children = mock_create.call_args[0][2]
        assert children is not None
        types = [b['type'] for b in children]
        assert 'heading_2' in types
        assert 'bookmark' in types

    @patch('create_asset.find_existing_asset', return_value=None)
    @patch('create_asset.create_page', return_value=MOCK_CREATED_PAGE)
    @patch('create_asset.DB_IDS', {'marketing_assets': 'real-db-id'})
    def test_slides_added_as_heading3_blocks(self, mock_create, mock_find):
        data = {**self.BASE_DATA, 'slides': [
            {'title': 'Slide 1 — Hook', 'content': 'Hook text'},
            {'title': 'Slide 2 — Body', 'content': 'Body text'},
        ]}
        ca.create_asset(data)
        children = mock_create.call_args[0][2]
        assert children is not None
        h3_blocks = [b for b in children if b['type'] == 'heading_3']
        assert len(h3_blocks) == 2

    @patch('create_asset.DB_IDS', {'marketing_assets': ''})
    def test_raises_when_db_id_missing(self):
        with pytest.raises(ValueError, match="NOTION_DB_MARKETING_ASSETS"):
            ca.create_asset(self.BASE_DATA)
