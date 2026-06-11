"""Tests for create_todo.py — single and batch todo creation, dedup, optional fields."""
import pytest
from unittest.mock import patch
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import create_todo as ct


@pytest.fixture(autouse=True)
def mock_set_brand():
    with patch('create_todo.set_brand') as mocked:
        yield mocked


MOCK_PAGE = {'id': 'todo-id-001', 'url': 'https://notion.so/todo-001'}
MOCK_EXISTING_PAGE = {'id': 'todo-id-existing', 'url': 'https://notion.so/todo-existing'}


class TestFindExistingTodo:
    @patch('create_todo.DB_IDS', {'marketing_todos': ''})
    def test_returns_none_when_db_id_missing(self):
        assert ct.find_existing_todo('any task') is None

    @patch('create_todo.query_database', return_value=[MOCK_EXISTING_PAGE])
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_returns_page_when_found(self, mock_db):
        result = ct.find_existing_todo('Review — MCP is the new API — LinkedIn (PM)')
        assert result['id'] == 'todo-id-existing'
        mock_db.assert_called_once_with(
            'real-db-id',
            filter_obj={'property': 'Task', 'title': {'equals': 'Review — MCP is the new API — LinkedIn (PM)'}},
        )

    @patch('create_todo.query_database', return_value=[])
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_returns_none_when_not_found(self, mock_db):
        assert ct.find_existing_todo('Unknown Task') is None


class TestCreateTodo:
    @patch('create_todo.find_existing_todo', return_value=MOCK_EXISTING_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_returns_existing_without_creating(self, mock_find):
        result = ct.create_todo({'task': 'Review — MCP is the new API — LinkedIn (PM)', 'priority': '🔥 High', 'brand': 'youmi'})
        assert result['action'] == 'existing'
        assert result['task_id'] == 'todo-id-existing'

    @patch('create_todo.find_existing_todo', return_value=None)
    @patch('create_todo.create_page', return_value=MOCK_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_creates_when_not_found(self, mock_create, mock_find):
        result = ct.create_todo({'task': 'Review — Test Post', 'priority': '🔥 High', 'brand': 'youmi'})
        assert result['action'] == 'created'
        assert result['task_id'] == 'todo-id-001'
        mock_create.assert_called_once()

    @patch('create_todo.find_existing_todo', return_value=None)
    @patch('create_todo.create_page', return_value=MOCK_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_returns_expected_fields(self, mock_create, mock_find):
        result = ct.create_todo({'task': 'Review — Test Post', 'priority': '🔥 High', 'brand': 'youmi'})
        assert result['task_id'] == 'todo-id-001'
        assert result['task'] == 'Review — Test Post'
        assert result['priority'] == '🔥 High'

    @patch('create_todo.find_existing_todo', return_value=None)
    @patch('create_todo.create_page', return_value=MOCK_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_default_priority_is_high(self, mock_create, mock_find):
        result = ct.create_todo({'task': 'Review — Test', 'brand': 'youmi'})
        assert result['priority'] == '🔥 High'

    @patch('create_todo.find_existing_todo', return_value=None)
    @patch('create_todo.create_page', return_value=MOCK_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_channel_added_when_provided(self, mock_create, mock_find):
        ct.create_todo({'task': 'Review', 'channel': 'LinkedIn', 'brand': 'youmi'})
        props = mock_create.call_args[0][1]
        assert props['Channel'] == {'select': {'name': 'LinkedIn'}}

    @patch('create_todo.find_existing_todo', return_value=None)
    @patch('create_todo.create_page', return_value=MOCK_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_channel_omitted_when_not_provided(self, mock_create, mock_find):
        ct.create_todo({'task': 'Review', 'brand': 'youmi'})
        props = mock_create.call_args[0][1]
        assert 'Channel' not in props

    @patch('create_todo.find_existing_todo', return_value=None)
    @patch('create_todo.create_page', return_value=MOCK_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_asset_id_added_as_relation(self, mock_create, mock_find):
        ct.create_todo({'task': 'Review', 'asset_id': 'asset-123', 'brand': 'youmi'})
        props = mock_create.call_args[0][1]
        assert props['Linked Asset'] == {'relation': [{'id': 'asset-123'}]}

    @patch('create_todo.find_existing_todo', return_value=None)
    @patch('create_todo.create_page', return_value=MOCK_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_status_always_not_started(self, mock_create, mock_find):
        ct.create_todo({'task': 'Review', 'brand': 'youmi'})
        props = mock_create.call_args[0][1]
        assert props['Status'] == {'status': {'name': 'Not Started'}}

    @patch('create_todo.DB_IDS', {'marketing_todos': ''})
    def test_raises_when_db_id_missing(self):
        with pytest.raises(ValueError, match="NOTION_DB_MARKETING_TODOS"):
            ct.create_todo({'task': 'Review', 'brand': 'youmi'})

    @patch('create_todo.find_existing_todo', return_value=None)
    @patch('create_todo.create_page', return_value=MOCK_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_brand_field_triggers_set_brand(self, mock_create, mock_find, mock_set_brand):
        ct.create_todo({'task': 'Review', 'brand': 'other'})
        mock_set_brand.assert_called_once_with('other')

    @patch('create_todo.find_existing_todo', return_value=None)
    @patch('create_todo.create_page', return_value=MOCK_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_no_brand_field_raises(self, mock_create, mock_find, mock_set_brand):
        with pytest.raises(ValueError, match='brand is required'):
            ct.create_todo({'task': 'Review'})
        mock_set_brand.assert_not_called()


class TestCreateTodoBatch:
    @patch('create_todo.find_existing_todo', return_value=None)
    @patch('create_todo.create_page', return_value=MOCK_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_batch_returns_list(self, mock_create, mock_find):
        items = [
            {'task': 'Review — Post A', 'priority': '🔥 High', 'brand': 'youmi'},
            {'task': 'Design — Carousel B', 'priority': '🟡 Medium', 'brand': 'youmi'},
            {'task': 'Publish — Post A', 'priority': '🔥 High', 'brand': 'youmi'},
        ]
        results = [ct.create_todo(item) for item in items]
        assert len(results) == 3
        assert mock_create.call_count == 3

    @patch('create_todo.find_existing_todo', return_value=MOCK_EXISTING_PAGE)
    @patch('create_todo.create_page', return_value=MOCK_PAGE)
    @patch('create_todo.DB_IDS', {'marketing_todos': 'real-db-id'})
    def test_batch_skips_existing(self, mock_create, mock_find):
        items = [
            {'task': 'Review — Post A', 'priority': '🔥 High', 'brand': 'youmi'},
            {'task': 'Publish — Post A', 'priority': '🔥 High', 'brand': 'youmi'},
        ]
        results = [ct.create_todo(item) for item in items]
        assert all(r['action'] == 'existing' for r in results)
        mock_create.assert_not_called()
