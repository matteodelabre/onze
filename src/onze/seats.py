from collections.abc import Sequence
from typing import Protocol
from subprocess import Popen, PIPE
from .protocol import Command, write_command


class Seat(Protocol):
    def __str__(self) -> str:
        """Return a human-readable of this seat’s configuration."""
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

    def send(self, command: Command) -> None:
        print(f"[seat {self.player}] <- {command}")

    def receive(self) -> str:
        return input(f"[seat {self.player}] -> ")


class SubprocessSeat:
    """Unattended seat controlled by a separate process."""

    def __init__(self, player: int, args: Sequence[str]):
        self.player = player
        self.process = Popen(args, stdin=PIPE, stdout=PIPE, encoding="utf8")

    def __str__(self) -> str:
        player = self.player
        args = self.process.args
        return f"SubprocessSeat({player=}, {args=})"

    def send(self, command: Command) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(write_command(command) + "\n")
        self.process.stdin.flush()

    def receive(self) -> str:
        assert self.process.stdout is not None
        return self.process.stdout.readline().removesuffix("\n")
