from unittest.mock import AsyncMock, patch

import pytest

from core.celery_core import check_queue_task_celery


@pytest.fixture
def mock_check_queue_task():
    with patch("core.celery_core.check_queue_task", new_callable=AsyncMock) as mock_task:
        yield mock_task


def test_check_queue_task_celery_invokes_check_queue_task(mock_check_queue_task):
    check_queue_task_celery()
    mock_check_queue_task.assert_called_once()
