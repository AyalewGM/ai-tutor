"""Thread-safe ephemeral test relay; production always uses Redis Pub/Sub."""
import asyncio
from contextlib import asynccontextmanager
from queue import Empty, Full, Queue
from threading import Lock


class TestLiveRelay:
    __test__ = False

    def __init__(self):
        self.lock = Lock()
        self.rooms = {}

    @asynccontextmanager
    async def open(self, board_id):
        inbox = Queue(maxsize=64)
        with self.lock:
            self.rooms.setdefault(board_id, []).append(inbox)
        relay = self

        class Channel:
            async def publish(self, event):
                with relay.lock:
                    subscribers = list(relay.rooms.get(board_id, []))
                for subscriber in subscribers:
                    try:
                        subscriber.put_nowait(event)
                    except Full:
                        try:
                            subscriber.get_nowait()
                            subscriber.put_nowait(event)
                        except (Empty, Full):
                            pass

            async def receive(self):
                try:
                    return inbox.get_nowait()
                except Empty:
                    await asyncio.sleep(0.01)
                    return None

        try:
            yield Channel()
        finally:
            with self.lock:
                self.rooms[board_id].remove(inbox)
                if not self.rooms[board_id]:
                    del self.rooms[board_id]
