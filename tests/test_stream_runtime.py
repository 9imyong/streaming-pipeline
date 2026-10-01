import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from aiokafka import TopicPartition

from app.application.dto import StreamSpec
from app.infrastructure.messaging.kafka.consumer import KafkaConsumerBase
from app.services.worker_stream.manager import ProcHandle, StreamProcessManager, _is_lease_valid


def manager():
    return StreamProcessManager(
        'worker-1', AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock(),
        lease_renew_interval_sec=0,
    )


def test_consumer_commits_processed_partition_only():
    async def run():
        consumer = KafkaConsumerBase('test')
        raw = AsyncMock()
        consumer._consumer = raw
        raw.getone.side_effect = [
            SimpleNamespace(topic='commands', partition=2, offset=7, value={'command': 'START'}),
            RuntimeError('end'),
        ]
        iterator = consumer.iterate()
        await anext(iterator)
        raw.commit.assert_not_awaited()
        with pytest.raises(RuntimeError, match='end'):
            await anext(iterator)
        raw.commit.assert_awaited_once_with({TopicPartition('commands', 2): 8})
    asyncio.run(run())


def test_failed_command_is_not_committed_or_skipped():
    async def run():
        consumer = KafkaConsumerBase('test')
        raw = AsyncMock()
        consumer._consumer = raw
        raw.getone.side_effect = [SimpleNamespace(
            topic='commands', partition=0, offset=1, value={'command': 'STOP'}
        ), RuntimeError('end')]
        attempts = 0
        async def handler(_topic, _value):
            nonlocal attempts
            attempts += 1
            raw.commit.assert_not_awaited()
            if attempts == 1:
                raise RuntimeError('DB unavailable')
        with patch('app.infrastructure.messaging.kafka.consumer.asyncio.sleep', new=AsyncMock()):
            with pytest.raises(RuntimeError, match='end'):
                await consumer.run_forever(handler)
        assert attempts == 2
        raw.commit.assert_awaited_once_with({TopicPartition('commands', 0): 2})
    asyncio.run(run())


def test_auto_commit_disabled():
    async def run():
        consumer = KafkaConsumerBase('test')
        with patch('aiokafka.AIOKafkaConsumer') as factory:
            factory.return_value = AsyncMock()
            await consumer.start(['commands'])
            assert factory.call_args.kwargs['enable_auto_commit'] is False
            await consumer.stop()
    asyncio.run(run())


@pytest.mark.parametrize('expires', [None, 'invalid', datetime.now(timezone.utc) - timedelta(seconds=5)])
def test_missing_or_expired_lease_cannot_run(expires):
    assert not _is_lease_valid({'assigned_worker_id': 'worker-1', 'lease_expires_at': expires}, 'worker-1')


def test_mysql_naive_utc_lease():
    expires = (datetime.now(timezone.utc) + timedelta(seconds=60)).replace(tzinfo=None)
    assert _is_lease_valid({'assigned_worker_id': 'worker-1', 'lease_expires_at': expires}, 'worker-1')


def test_spawn_loses_lease_and_stops_before_started_event():
    async def run():
        m = manager()
        spec = StreamSpec('ch1', 'rtsp://example/stream', 'hls', None, None, {}, 'worker-1')
        m.lease_store.renew.return_value = False
        m.runner.spawn.return_value = SimpleNamespace(pid=1, publishes_lifecycle_events=False)
        m.stop_stream = AsyncMock()
        await m.start_stream(spec)
        m.stop_stream.assert_awaited_once_with('ch1', reason='lease_lost')
        m._event_bus.publish_event.assert_not_awaited()
    asyncio.run(run())


def test_lease_error_stops_stream_and_keeps_renewing_other_channels():
    async def run():
        m = manager()
        m._procs = {'ch1': None, 'ch2': None}
        async def renew(channel_id, *_args):
            if channel_id == 'ch1':
                raise RuntimeError('DB unavailable')
            m._stop_event.set()
            return True
        m.lease_store.renew.side_effect = renew
        async def stop(*args, **kwargs):
            m._procs.pop(args[0], None)
        m.stop_stream = AsyncMock(side_effect=stop)
        sleep = asyncio.sleep
        async def tick(_delay):
            if m.lease_store.renew.await_count == 2:
                m._stop_event.set()
            await sleep(0)
        with patch('app.services.worker_stream.manager.asyncio.sleep', tick):
            await m._lease_renew_loop()
        m.stop_stream.assert_awaited_once_with('ch1', reason='lease_lost')
        assert m.lease_store.renew.await_count == 2
    asyncio.run(run())


def test_stop_during_restart_backoff_does_not_spawn_orphan():
    async def run():
        m = manager()
        spec = StreamSpec('ch1', 'rtsp://example/stream', 'hls', None, None, {}, 'worker-1')
        process = SimpleNamespace(returncode=1, stderr=None, publishes_lifecycle_events=False)
        handle = ProcHandle(spec, process, 0)
        m._procs['ch1'] = handle
        m.stream_repo.get.return_value = {
            'assigned_worker_id': 'worker-1',
            'lease_expires_at': datetime.now(timezone.utc) + timedelta(seconds=60),
        }
        count = 0
        async def tick(_delay):
            nonlocal count
            count += 1
            if count == 2:
                # STOP completes while the failed stream is in restart backoff.
                handle.stopping = True
                m._procs.pop('ch1')
                m._stop_event.set()
        with patch('app.services.worker_stream.manager.asyncio.sleep', tick):
            await m._watch_processes_loop()
        m.runner.spawn.assert_not_awaited()
    asyncio.run(run())


def test_start_command_waits_for_assignment_and_starts():
    async def run():
        m = manager()
        m.stream_repo.get.side_effect = [None, {
            'assigned_worker_id': 'worker-1',
            'lease_expires_at': datetime.now(timezone.utc) + timedelta(seconds=60),
            'desired_state': 'running',
        }]
        m.start_stream = AsyncMock()
        async def commands():
            yield {'command': 'START', 'channel_id': 'ch1', 'params': {'source_rtsp': 'rtsp://example/stream'}}
        with patch('app.services.worker_stream.manager.asyncio.sleep', new=AsyncMock()):
            await m._consume_commands_loop(commands())
        m.start_stream.assert_awaited_once()
        assert m.start_stream.call_args.args[0].channel_id == 'ch1'
    asyncio.run(run())


def test_workers_use_independent_command_subscriptions():
    from contextlib import ExitStack
    from app.services.worker_stream.main import run

    async def check():
        groups = []
        for worker_id in ('worker-1', 'worker-2'):
            with ExitStack() as stack:
                stack.enter_context(patch.dict('os.environ', {'WORKER_ID': worker_id}))
                stack.enter_context(patch('app.core.observability.start_metrics_server'))
                factory = stack.enter_context(patch(
                    'app.infrastructure.messaging.kafka.consumer.KafkaConsumerBase',
                    return_value=AsyncMock(),
                ))
                stack.enter_context(patch(
                    'app.infrastructure.messaging.kafka.producer.KafkaProducerWrapper',
                    return_value=AsyncMock(),
                ))
                stack.enter_context(patch('app.infrastructure.persistence.stream_repository.DbStreamRepository'))
                stack.enter_context(patch('app.infrastructure.persistence.lease_db.DbLeaseStore'))
                stack.enter_context(patch('app.infrastructure.runners.gstreamer.GstreamerStreamRunner'))
                stack.enter_context(patch(
                    'app.services.worker_stream.manager.StreamProcessManager',
                    return_value=AsyncMock(),
                ))
                await run()
                groups.append(factory.call_args.kwargs['group_id'])
        assert groups[0] != groups[1]
    asyncio.run(check())
