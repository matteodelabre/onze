from collections.abc import Sequence
from typing import Protocol
from subprocess import Popen, PIPE
from threading import Thread
from .protocol import Command, write_command


class Seat(Protocol):
    def __str__(self) -> str:
        """Return a human-readable description of this seat’s configuration."""
        ...

    def close(self) -> None:
        """Close all resources attached to this seat."""
        ...

    def send(self, command: Command) -> None:
        """Send a command to this seat."""
        ...

    def receive(self) -> str:
        """Wait for the next message from this seat."""
        ...


class TerminalSeat:
    """Interactive seat controlled by a human through the command line."""

    def __init__(self, player: int):
        self.player = player

    def __str__(self):
        player = self.player
        return f"TerminalSeat({player=})"

    def close(self) -> None:
        pass

    def send(self, command: Command) -> None:
        print(f"[seat {self.player}] <- {write_command(command)}")

    def receive(self) -> str:
        return input(f"[seat {self.player}] -> ")


class SubprocessSeat:
    """Unattended seat controlled by a separate process."""

    def __init__(self, player: int, args: Sequence[str]):
        self.player = player
        self.process = Popen(
            args, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=1, encoding="utf8"
        )
        self.log_thread = Thread(target=self._log_stderr)
        self.log_thread.start()

    def _log_stderr(self) -> None:
        assert self.process.stderr is not None

        for line in self.process.stderr:
            print(f"[seat {self.player}] {line}", end="")

    def __str__(self) -> str:
        player = self.player
        args = self.process.args
        return f"SubprocessSeat({player=}, {args=})"

    def close(self) -> None:
        self.process.kill()
        self.log_thread.join()

    def send(self, command: Command) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(write_command(command) + "\n")
        self.process.stdin.flush()

    def receive(self) -> str:
        assert self.process.stdout is not None
        return self.process.stdout.readline().removesuffix("\n")
