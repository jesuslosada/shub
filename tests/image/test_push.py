import mock
import pytest
from click.testing import CliRunner
from shub import exceptions as shub_exceptions
from shub.image.push import cli


@pytest.fixture
def test_mock():
    """Mock for shub image test command"""
    with mock.patch('shub.image.push.test_cmd') as m:
        yield m


@pytest.mark.usefixtures('project_dir')
def test_cli_with_apikey_login(docker_client_mock, test_mock):
    docker_client_mock.login.return_value = {"Status": "Login Succeeded"}
    docker_client_mock.push.return_value = [
        {"stream": "In process"},
        {"status": "Successfully pushed"}
    ]
    runner = CliRunner()
    result = runner.invoke(cli, ["dev", "--version", "test"])
    assert result.exit_code == 0
    docker_client_mock.push.assert_called_with(
        'registry/user/project:test', decode=True,
        insecure_registry=False, stream=True)
    test_mock.assert_called_with("dev", "test")


@pytest.mark.usefixtures('project_dir')
def test_cli_with_progress(docker_client_mock, test_mock):
    docker_client_mock.login.return_value = {"Status": "Login Succeeded"}
    docker_client_mock.push.return_value = [
        {"status": "The push refers to a repository [some/image]"},
        {"status": "Preparing", "progressDetail": {}, "id": "abc"},
        {"status": "Preparing", "progressDetail": {}, "id": "def"},
        {"status": "Preparing", "progressDetail": {}, "id": "egh"},
        {"status": "Waiting", "progressDetail": {}, "id": "abc"},
        {"status": "Waiting", "progressDetail": {}, "id": "egh"},
        {"status": "Pushing", "progressDetail": {"current": 512, "total": 24803}, "id": "abc"},
        {"status": "Layer already exists", "progressDetail": {}, "id": "def"},
        {"status": "Pushing", "progressDetail": {"current": 57344, "total": 26348}, "id": "egh"},
        {"status": "Pushing", "progressDetail": {"current": 24805, "total": 24803}, "id": "abc"},
        {"status": "Pushed", "progressDetail": {}, "id": "abc"},
        {"status": "Successfully pushed"}
    ]
    runner = CliRunner()
    result = runner.invoke(cli, ["dev", "--version", "test"])
    assert result.exit_code == 0
    import re
    assert re.match(
        'Login to registry succeeded.\n'
        'Pushing registry/user/project:test to the registry.\n\r'
        'Layers:   0%|          | 0/1\r          \r'
        'Layers:   0%|          | 0/1\r          \r'
        'Layers:   0%|          | 0/2\r          \r'
        'Layers:   0%|          | 0/3\r          \r'
        'Layers:   0%|          | 0/3\r          \r'
        'Layers:   0%|          | 0/3\n\r'
        'abc:   0%|          | 0.00/24.8K [?B/s]\x1b[A\r'
        '          \r'
        'Layers:   0%|          | 0/3\n\n\r'
        'egh:   0%|          | 0.00/26.3K [?B/s]\x1b[A\x1b[A\r'
        '          \r'
        'Layers:  33%|███▎      | 1/3\r'
        'Layers:  67%|██████▋   | 2/3\n\r'
        'abc: 100%|██████████| 24.8K/24.8K [[.0-9]MB/s]\n\r'
        'egh: 100%|██████████| 26.3K/26.3K [[.0-9]MB/s]\n'
        'The image registry/user/project:test pushed successfully.\n',
        result.output)


@pytest.mark.usefixtures('project_dir')
def test_cli_with_custom_login(docker_client_mock, test_mock):
    docker_client_mock.login.return_value = {"Status": "Login Succeeded"}
    docker_client_mock.push.return_value = [
        {"stream": "In process"},
        {"status": "Successfully pushed"}
    ]
    runner = CliRunner()
    result = runner.invoke(
        cli, ["dev", "--version", "test", "--username", "user",
              "--password", "pass", "--email", "mail"])
    assert result.exit_code == 0
    docker_client_mock.login.assert_called_with(
        email=u'mail', password=u'pass',
        reauth=False, registry='registry', username=u'user')
    docker_client_mock.push.assert_called_with(
        'registry/user/project:test', decode=True,
        insecure_registry=False, stream=True)
    test_mock.assert_called_with("dev", "test")


@pytest.mark.usefixtures('project_dir')
def test_cli_with_insecure_registry(docker_client_mock, test_mock):
    docker_client_mock.login.return_value = {"Status": "Login Succeeded"}
    docker_client_mock.push.return_value = [
        {"stream": "In process"},
        {"status": "Successfully pushed"}
    ]
    runner = CliRunner()
    result = runner.invoke(
        cli, ["dev", "--version", "test", "--insecure"])
    assert result.exit_code == 0
    assert not docker_client_mock.login.called
    docker_client_mock.push.assert_called_with(
        'registry/user/project:test', decode=True,
        insecure_registry=True, stream=True)
    test_mock.assert_called_with("dev", "test")


@pytest.mark.usefixtures('project_dir')
def test_cli_with_login_username_only(docker_client_mock, test_mock):
    docker_client_mock.login.return_value = {"Status": "Login Succeeded"}
    docker_client_mock.push.return_value = [
        {"stream": "In process"},
        {"status": "Successfully pushed"}
    ]
    runner = CliRunner()
    result = runner.invoke(
        cli, ["dev", "--version", "test", "--apikey", "apikey"])
    assert result.exit_code == 0
    docker_client_mock.login.assert_called_with(
        email=None, password=' ',
        reauth=False, registry='registry', username='apikey')
    docker_client_mock.push.assert_called_with(
        'registry/user/project:test', decode=True,
        insecure_registry=False, stream=True)
    test_mock.assert_called_with("dev", "test")


@pytest.mark.usefixtures('project_dir')
def test_cli_login_fail(docker_client_mock, test_mock):
    docker_client_mock.login.return_value = {"Status": "Login Failed!"}
    runner = CliRunner()
    result = runner.invoke(
        cli, ["dev", "--version", "test", "--username", "user",
              "--password", "pass", "--email", "mail"])
    assert result.exit_code == shub_exceptions.RemoteErrorException.exit_code
    test_mock.assert_called_with("dev", "test")


@pytest.mark.usefixtures('project_dir')
def test_cli_push_fail(docker_client_mock, test_mock):
    docker_client_mock.login.return_value = {"Status": "Login Succeeded"}
    docker_client_mock.push.return_value = [{"error": "Failed:(", "errorDetail": ""}]
    runner = CliRunner()
    result = runner.invoke(
        cli, ["dev", "--version", "test", "--username", "user",
              "--password", "pass", "--email", "mail"])
    assert result.exit_code == shub_exceptions.RemoteErrorException.exit_code
    test_mock.assert_called_with("dev", "test")


@pytest.mark.usefixtures('project_dir')
@pytest.mark.parametrize('skip_tests_flag', ['-S', '--skip-tests'])
def test_cli_skip_tests(docker_client_mock, test_mock, skip_tests_flag):
    docker_client_mock.login.return_value = {"Status": "Login Succeeded"}
    docker_client_mock.push.return_value = [
        {"stream": "In process"},
        {"status": "Successfully pushed"}
    ]
    runner = CliRunner()
    result = runner.invoke(cli, ["dev", "--version", "test", skip_tests_flag])
    assert result.exit_code == 0
    docker_client_mock.push.assert_called_with(
        'registry/user/project:test', decode=True,
        insecure_registry=False, stream=True)
    assert test_mock.call_count == 0
