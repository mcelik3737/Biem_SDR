"""One bounded map renderer: newest viewport wins, never touches Tk or SDR."""

from threading import Condition, Thread


class MapWorker:
    def __init__(self, renderer):
        self.renderer = renderer
        self.condition = Condition()
        self.revision = 0
        self.pending = None
        self.result = None
        self.closed = False
        self.thread = Thread(target=self.run, name="offline-map", daemon=True)
        self.thread.start()

    def submit(self, view):
        with self.condition:
            self.revision += 1
            self.pending = view
            self.result = None
            self.condition.notify()

    def take_result(self):
        with self.condition:
            result, self.result = self.result, None
            return result

    def close(self):
        with self.condition:
            self.closed = True
            self.pending = self.result = None
            self.condition.notify()

    def cancelled(self, revision):
        with self.condition:
            return self.closed or revision != self.revision

    def run(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.closed or self.pending is not None)
                if self.closed:
                    return
                view, self.pending = self.pending, None
                revision = self.revision
            try:
                rendered = self.renderer.render(
                    view, lambda revision=revision: self.cancelled(revision)
                )
                outcome = (view, rendered, None)
            except Exception as exc:
                outcome = (view, None, str(exc))
            with self.condition:
                if not self.closed and revision == self.revision:
                    self.result = outcome
