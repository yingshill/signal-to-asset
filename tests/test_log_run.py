"""Tests for log_run.py — appends run records to logs/runs.jsonl."""
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import log_run as lr


SAMPLE_RUN = {
    'brand': 'youmi',
    'project_id': 'proj-abc',
    'project_title': 'MCP is the new API',
    'assets': [
        {'asset_id': 'a1', 'asset_name': 'MCP is the new API — LinkedIn (PM)', 'action': 'created'},
        {'asset_id': 'a2', 'asset_name': 'MCP is the new API — LinkedIn (DE)', 'action': 'existing'},
    ],
    'todos': [
        {'task_id': 't1', 'task': 'Review — MCP is the new API — LinkedIn (PM)', 'action': 'created'},
        {'task_id': 't2', 'task': 'Publish — MCP is the new API — LinkedIn (PM)', 'action': 'created'},
    ],
}


class TestLogRun:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.patcher = patch.object(lr, 'LOG_FILE', self.tmp / 'runs.jsonl')
        self.patcher.start()

    def teardown_method(self):
        self.patcher.stop()

    def test_creates_log_file_and_dir(self):
        lr.log_run(SAMPLE_RUN)
        assert (self.tmp / 'runs.jsonl').exists()

    def test_log_entry_is_valid_json(self):
        lr.log_run(SAMPLE_RUN)
        line = (self.tmp / 'runs.jsonl').read_text().strip()
        entry = json.loads(line)
        assert entry['project_id'] == 'proj-abc'
        assert entry['project_title'] == 'MCP is the new API'

    def test_log_entry_has_timestamp(self):
        lr.log_run(SAMPLE_RUN)
        line = (self.tmp / 'runs.jsonl').read_text().strip()
        entry = json.loads(line)
        assert 'ts' in entry
        assert entry['ts'].endswith('+00:00')

    def test_appends_multiple_runs(self):
        lr.log_run(SAMPLE_RUN)
        lr.log_run(SAMPLE_RUN)
        lines = (self.tmp / 'runs.jsonl').read_text().strip().splitlines()
        assert len(lines) == 2
        for line in lines:
            json.loads(line)  # each line is valid JSON

    def test_returns_correct_counts(self):
        result = lr.log_run(SAMPLE_RUN)
        assert result['assets_created'] == 1
        assert result['assets_existing'] == 1
        assert result['todos_created'] == 2
        assert result['todos_existing'] == 0

    def test_handles_empty_assets_and_todos(self):
        result = lr.log_run({'brand': 'youmi', 'project_id': 'x', 'project_title': 'Empty', 'assets': [], 'todos': []})
        assert result['assets_created'] == 0
        assert result['todos_created'] == 0

    def test_log_file_path_returned(self):
        result = lr.log_run(SAMPLE_RUN)
        assert 'log_file' in result
        assert result['log_file'].endswith('runs.jsonl')

    def test_brand_persisted_in_entry(self):
        lr.log_run({**SAMPLE_RUN, 'brand': 'other'})
        entry = json.loads((self.tmp / 'runs.jsonl').read_text().strip())
        assert entry['brand'] == 'other'

    def test_missing_brand_raises(self):
        data = {k: v for k, v in SAMPLE_RUN.items() if k != 'brand'}
        with pytest.raises(ValueError, match='brand is required'):
            lr.log_run(data)

    def test_brand_returned_in_summary(self):
        result = lr.log_run({**SAMPLE_RUN, 'brand': 'other'})
        assert result['brand'] == 'other'
