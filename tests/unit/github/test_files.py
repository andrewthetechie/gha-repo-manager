import pytest
from github.GithubException import UnknownObjectException

from repo_manager.gh import files
from repo_manager.gh.files import copy_file
from repo_manager.gh.files import RemoteSrcNotFoundError
from repo_manager.schemas import FileConfig

VALID_CONFIG = {
    "src_file": "tests/unit/schemas/test_file.py",
    "dest_file": "test",
}


class MockBlob:
    @property
    def sha(self):
        return "1234"


def test_copy_file_new_local_to_dest(mocker):
    mock_repo = mocker.MagicMock()
    mock_repo.get_contents.side_effect = UnknownObjectException(status=404, data={}, headers={})
    mock_repo.create_file = mocker.MagicMock(return_value={"commit": mocker.MagicMock(sha="1234")})
    mock_repo.create_git_blob = mocker.MagicMock(return_value=MockBlob())
    this_config = FileConfig(**VALID_CONFIG, target_branch="test")
    result = copy_file(mock_repo, this_config)
    assert result == "1234"
    assert mock_repo.get_contents.call_count == 1
    assert mock_repo.create_file.call_count == 1


def test_copy_file_remote_src_not_found(mocker):
    mock_repo = mocker.MagicMock()
    mock_repo.get_contents.side_effect = UnknownObjectException(status=404, data={}, headers={})
    this_config = FileConfig(**VALID_CONFIG, remote_src=True)
    with pytest.raises(RemoteSrcNotFoundError):
        copy_file(mock_repo, this_config)


def test_copy_file_update_remote_file(mocker):
    mock_repo = mocker.MagicMock()
    files.get_remote_file_contents = mocker.MagicMock(return_value="test")
    mock_repo.get_contents = mocker.MagicMock(return_value=mocker.MagicMock(sha="1234"))
    mock_repo.update_file = mocker.MagicMock(return_value={"commit": mocker.MagicMock(sha="1234")})
    mock_repo.create_git_blob = mocker.MagicMock(return_value=MockBlob())
    this_config = FileConfig(**VALID_CONFIG, remote_src=True)
    result = copy_file(mock_repo, this_config)
    assert result == "1234"
    assert mock_repo.get_contents.call_count == 1
    assert mock_repo.update_file.call_count == 1


def test_move_file(mocker):
    files.copy_file = mocker.MagicMock(return_value="1234")
    files.delete_file = mocker.MagicMock(return_value="1234")
    this_config = FileConfig(**VALID_CONFIG, target_branch="test")
    copy, delete = files.move_file(mocker.MagicMock(), this_config)
    assert copy == "1234"
    assert delete == "1234"


def test_delete_file(mocker):
    mock_repo = mocker.MagicMock()
    mock_repo.get_contents = mocker.MagicMock(return_value=mocker.MagicMock(sha="1234"))
    mock_repo.delete_file = mocker.MagicMock(return_value={"commit": mocker.MagicMock(sha="1234")})
    this_config = FileConfig(**VALID_CONFIG, target_branch="test")
    result = files.delete_file(mock_repo, this_config)
    assert result == "1234"
