"""Parameter Store 읽기 테스트: 실제 AWS에 요청하지 않고 botocore의 Stubber로 응답을 흉내 냅니다."""
import boto3
import pytest
from botocore.stub import Stubber

from app import config

@pytest.fixture
def ssm_stub(monkeypatch):
    client = boto3.client("ssm", region_name="ap-northeast-2",
                          aws_access_key_id="test", aws_secret_access_key="test")
    monkeypatch.setattr(boto3, "client", lambda service, **kw: client)  # 앱이 만드는 클라이언트를 바꿔 끼웁니다.
    monkeypatch.setenv("SSM_PREFIX", "/book-api/")
    monkeypatch.delenv("SECRET_KEY", raising=False)    # 테스트가 끝나면 원래 값으로 돌아옵니다.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with Stubber(client) as stubber:
        yield stubber

def test_loads_parameters_into_environment(ssm_stub):
    ssm_stub.add_response(
        "get_parameters",
        {"Parameters": [{"Name": "/book-api/SECRET_KEY", "Value": "k" * 40, "Type": "SecureString"},
                        {"Name": "/book-api/DATABASE_URL", "Value": "sqlite:///./x.db", "Type": "SecureString"}]},
        {"Names": ["/book-api/SECRET_KEY", "/book-api/DATABASE_URL"], "WithDecryption": True},
    )
    config.load_ssm_parameters()
    assert config.os.environ["SECRET_KEY"] == "k" * 40
    assert config.os.environ["DATABASE_URL"] == "sqlite:///./x.db"

def test_missing_parameter_stops_startup(ssm_stub):
    ssm_stub.add_response(
        "get_parameters",
        {"Parameters": [], "InvalidParameters": ["/book-api/SECRET_KEY", "/book-api/DATABASE_URL"]},
    )
    with pytest.raises(RuntimeError, match="없는 파라미터"):
        config.load_ssm_parameters()

def test_without_prefix_does_nothing(monkeypatch):
    monkeypatch.delenv("SSM_PREFIX", raising=False)
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: pytest.fail("AWS를 부르면 안 됩니다."))
    config.load_ssm_parameters()
