import importlib.util
import unittest
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

from redis.exceptions import TimeoutError as RedisTimeoutError

from shared.ai_queue_protocol import AI_ANALYSIS_QUEUE_KEY


ROOT = Path(__file__).resolve().parent.parent


def _load_module(module_name: str, relative_path: str) -> ModuleType:
    module_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


worker_package = ModuleType("worker")
worker_package.__path__ = [str(ROOT / "worker")]

worker_model_stub = ModuleType("worker.model")
worker_model_stub.load_prediction_model = MagicMock()
worker_model_stub.predict_pneumonia = MagicMock()

with patch.dict(
    sys.modules,
    {
        "worker": worker_package,
        "worker.model": worker_model_stub,
    },
):
    worker_redis_client_module = _load_module(
        "worker.redis_client",
        "worker/redis_client.py",
    )
    worker_main_module = _load_module(
        "worker.main",
        "worker/main.py",
    )

create_redis_client = worker_redis_client_module.create_redis_client
consume_next_task = worker_main_module.consume_next_task


class WorkerMainTest(unittest.TestCase):
    def test_consume_next_task_keeps_worker_alive_on_brpop_timeout(self) -> None:
        redis_client = MagicMock()
        redis_client.brpop.side_effect = RedisTimeoutError("Timeout reading from socket")

        consumed = consume_next_task(redis_client)

        self.assertFalse(consumed)
        redis_client.brpop.assert_called_once_with(
            AI_ANALYSIS_QUEUE_KEY,
            timeout=0,
        )


class WorkerRedisClientTest(unittest.TestCase):
    def test_create_redis_client_disables_socket_read_timeout(self) -> None:
        with patch.object(worker_redis_client_module.Redis, "from_url") as from_url:
            create_redis_client("redis://redis:6379/0")

        from_url.assert_called_once_with(
            "redis://redis:6379/0",
            decode_responses=True,
            socket_timeout=None,
            health_check_interval=30,
        )


if __name__ == "__main__":
    unittest.main()
