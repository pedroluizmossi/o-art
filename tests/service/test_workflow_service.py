import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, mock_open, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from model.enum.model_type import Model
from model.enum.workflow_segment_type import WorkflowSegment
from model.enum.workflow_type import Workflow as WorkflowType
from model.workflow_model import Workflow, WorkflowCreate
from service.workflow_service import (
    WorkflowNotFound,
    create_workflow,
    delete_workflow,
    get_all_workflows,
    get_workflow_by_id,
    seed_workflow_from_json,
    update_workflow,
)


@pytest.fixture
def sample_workflow_id():
    return uuid.uuid4()


@pytest.fixture
def sample_workflow_create_data():
    return WorkflowCreate(
        name="Test Workflow",
        description="Test Description",
        model_type=Model.SDXL,
        workflow_type=WorkflowType.IMAGE,
        workflow_segment=WorkflowSegment.TEXT_TO_IMAGE,
        workflow_json={"prompt": "test prompt"},
        parameters={"width": 512, "height": 512}
    )


@pytest.fixture
def sample_workflow(sample_workflow_id):
    return Workflow(
        id=sample_workflow_id,
        name="Test Workflow",
        description="Test Description",
        model_type=Model.SDXL,
        workflow_type=WorkflowType.IMAGE,
        workflow_segment=WorkflowSegment.TEXT_TO_IMAGE,
        workflow_json={"prompt": "test prompt"},
        parameters={"width": 512, "height": 512},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.delete = AsyncMock()
    session.add = Mock()
    session.exec = AsyncMock()
    return session


class TestCreateWorkflow:
    @pytest.mark.asyncio
    async def test_create_workflow_success(self,
                                           mock_session,
                                           sample_workflow_create_data,
                                           sample_workflow):
        mock_session.refresh.return_value = None
        
        with patch('service.workflow_service.Workflow', return_value=sample_workflow):
            result = await create_workflow(mock_session, sample_workflow_create_data)
        
        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called
        assert isinstance(result, Workflow)
        assert result.name == sample_workflow_create_data.name
        assert result.description == sample_workflow_create_data.description

    @pytest.mark.asyncio
    async def test_create_workflow_exception(self, mock_session, sample_workflow_create_data):
        mock_session.commit.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError), patch('service.workflow_service.logger.exception'):
            await create_workflow(mock_session, sample_workflow_create_data)
        
        assert mock_session.rollback.called


class TestGetAllWorkflows:
    @pytest.mark.asyncio
    async def test_get_all_workflows_success(self, mock_session, sample_workflow):
        result_mock = MagicMock()
        result_mock.all.return_value = [sample_workflow]
        mock_session.exec.return_value = result_mock
        
        result = await get_all_workflows(mock_session)
        
        assert mock_session.exec.called
        assert len(result) == 1
        assert result[0] == sample_workflow

    @pytest.mark.asyncio
    async def test_get_all_workflows_exception(self, mock_session):
        mock_session.exec.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError), patch('service.workflow_service.logger.exception'):
            await get_all_workflows(mock_session)


class TestGetWorkflowById:
    @pytest.mark.asyncio
    async def test_get_workflow_by_id_success(self,
                                              mock_session,
                                              sample_workflow,
                                              sample_workflow_id):
        result_mock = MagicMock()
        result_mock.first.return_value = sample_workflow
        mock_session.exec.return_value = result_mock
        
        result = await get_workflow_by_id(mock_session, sample_workflow_id)
        
        assert mock_session.exec.called
        assert result == sample_workflow

    @pytest.mark.asyncio
    async def test_get_workflow_by_id_not_found(self, mock_session, sample_workflow_id):
        result_mock = MagicMock()
        result_mock.first.return_value = None
        mock_session.exec.return_value = result_mock
        
        with pytest.raises(WorkflowNotFound), patch('service.workflow_service.logger.warning'):
            await get_workflow_by_id(mock_session, sample_workflow_id)

    @pytest.mark.asyncio
    async def test_get_workflow_by_id_exception(self, mock_session, sample_workflow_id):
        mock_session.exec.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError), patch('service.workflow_service.logger.exception'):
            await get_workflow_by_id(mock_session, sample_workflow_id)


class TestUpdateWorkflow:
    @pytest.mark.asyncio
    async def test_update_workflow_success(self,
                                           mock_session,
                                           sample_workflow,
                                           sample_workflow_id):
        # Mock get_workflow_by_id to return our sample workflow
        with patch('service.workflow_service.get_workflow_by_id',
                   return_value=sample_workflow):
            update_data = {"name": "Updated Name", "description": "Updated Description"}
            result = await update_workflow(mock_session, sample_workflow_id, update_data)
            
            assert mock_session.add.called
            assert mock_session.commit.called
            assert mock_session.refresh.called
            assert result.name == "Updated Name"
            assert result.description == "Updated Description"

    @pytest.mark.asyncio
    async def test_update_workflow_no_changes(self,
                                              mock_session,
                                              sample_workflow,
                                              sample_workflow_id):
        # Mock get_workflow_by_id to return our sample workflow
        with patch('service.workflow_service.get_workflow_by_id',
                   return_value=sample_workflow):
            # Use same values that are already in the workflow
            update_data = {"name": sample_workflow.name, "description": sample_workflow.description}
            
            result = await update_workflow(mock_session, sample_workflow_id, update_data)
            
            assert not mock_session.commit.called
            assert not mock_session.refresh.called
            assert result == sample_workflow

    @pytest.mark.asyncio
    async def test_update_workflow_not_found(self, mock_session, sample_workflow_id):
        with patch('service.workflow_service.get_workflow_by_id',
                   side_effect=WorkflowNotFound(sample_workflow_id)):
            with pytest.raises(WorkflowNotFound):
                await update_workflow(mock_session,
                                      sample_workflow_id,
                                      {"name": "Updated Name"})

    @pytest.mark.asyncio
    async def test_update_workflow_exception(self,
                                             mock_session,
                                             sample_workflow,
                                             sample_workflow_id):
        with patch('service.workflow_service.get_workflow_by_id',
                   return_value=sample_workflow):
            mock_session.commit.side_effect = SQLAlchemyError("Database error")
            
            with pytest.raises(
                    SQLAlchemyError), patch('service.workflow_service.logger.exception'):
                await update_workflow(
                    mock_session, sample_workflow_id, {"name": "Updated Name"})
            
            assert mock_session.rollback.called


class TestDeleteWorkflow:
    @pytest.mark.asyncio
    async def test_delete_workflow_success(self,
                                           mock_session,
                                           sample_workflow,
                                           sample_workflow_id):
        with patch('service.workflow_service.get_workflow_by_id',
                   return_value=sample_workflow):
            result = await delete_workflow(mock_session, sample_workflow_id)
            
            assert mock_session.delete.called
            assert mock_session.commit.called
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_workflow_not_found(self, mock_session, sample_workflow_id):
        with patch('service.workflow_service.get_workflow_by_id',
                   side_effect=WorkflowNotFound(sample_workflow_id)):
            with pytest.raises(WorkflowNotFound):
                await delete_workflow(mock_session, sample_workflow_id)

    @pytest.mark.asyncio
    async def test_delete_workflow_exception(self,
                                             mock_session,
                                             sample_workflow,
                                             sample_workflow_id):
        with patch('service.workflow_service.get_workflow_by_id',
                   return_value=sample_workflow):
            mock_session.commit.side_effect = SQLAlchemyError("Database error")
            
            with pytest.raises(SQLAlchemyError), patch('service.workflow_service.logger.exception'):
                await delete_workflow(mock_session, sample_workflow_id)
            
            assert mock_session.rollback.called


class TestSeedWorkflowFromJson:
    @pytest.mark.asyncio
    async def test_seed_workflow_from_json_new_workflows(self, mock_session):
        json_data = [
            {
                "name": "Workflow 1",
                "description": "Description 1",
                "model_type": "STABLE_DIFFUSION",
                "workflow_type": "IMAGE",
                "workflow_segment": "TEXT_TO_IMAGE",
                "workflow_json": {"prompt": "test"}
            },
            {
                "name": "Workflow 2",
                "description": "Description 2", 
                "model_type": "STABLE_DIFFUSION",
                "workflow_type": "IMAGE",
                "workflow_segment": "TEXT_TO_IMAGE",
                "workflow_json": {"prompt": "test2"}
            }
        ]
        
        # Mock open function to return json data
        with patch('builtins.open', mock_open(read_data=json.dumps(json_data))), \
             patch('service.workflow_service.select'), \
             patch('builtins.print') as mock_print:
                
            # Mock session.exec to return None (workflow doesn't exist)
            result_mock = MagicMock()
            result_mock.first.return_value = None
            mock_session.exec.return_value = result_mock
            
            await seed_workflow_from_json(mock_session, "fake_path.json")
            
            # Should add two workflows
            assert mock_session.add.call_count == 2
            assert mock_session.commit.called
            assert mock_print.call_count == 2

    @pytest.mark.asyncio
    async def test_seed_workflow_from_json_existing_workflow(self, mock_session, sample_workflow):
        json_data = [
            {
                "name": "Test Workflow",  # Same name as sample_workflow
                "description": "New Description", 
                "model_type": "STABLE_DIFFUSION",
                "workflow_type": "IMAGE",
                "workflow_segment": "TEXT_TO_IMAGE",
                "workflow_json": {"prompt": "test"}
            }
        ]
        
        # Mock open function to return json data
        with patch('builtins.open', mock_open(read_data=json.dumps(json_data))), \
             patch('service.workflow_service.select'), \
             patch('builtins.print') as mock_print:
                
            # Mock session.exec to return existing workflow
            result_mock = MagicMock()
            result_mock.first.return_value = sample_workflow
            mock_session.exec.return_value = result_mock
            
            await seed_workflow_from_json(mock_session, "fake_path.json")
            
            # Should not add any workflows
            assert mock_session.add.call_count == 0
            assert mock_session.commit.called
            assert "already exists" in mock_print.call_args_list[0][0][0]
