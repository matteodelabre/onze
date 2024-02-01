from collections.abc import Sequence
from typing import Protocol
import asyncio
from asyncio.subprocess import PIPE
from .protocol import Command, write_command


class Seat(Protocol):
    def __str__(self) -> str:
        """Return a human-readable description of this seat’s configuration."""
        ...

    async def close(self) -> None:
        """Close all resources attached to this seat."""
        ...

    async def send(self, command: Command) -> None:
        """Send a command to this seat."""
        ...

    async def receive(self) -> str:
        """Wait for the next message from this seat."""
        ...


class TerminalSeat:
    """Interactive seat controlled by a human through the command line."""

    player: int

    def __str__(self):
        player = self.player
        return f"TerminalSeat({player=})"

    @classmethod
    async def create(cls, player: int):
        self = cls()
        self.player = player
        return self

    async def close(self) -> None:
        pass

    async def send(self, command: Command) -> None:
        print(f"[seat {self.player}] <- {write_command(command)}")

    async def receive(self) -> str:
        return input(f"[seat {self.player}] -> ")


class SubprocessSeat:
    """Unattended seat controlled by a separate process."""

    player: int
    args: Sequence[str]
    process: asyncio.subprocess.Process
    log_stderr_task: asyncio.Task

    def __str__(self) -> str:
        player = self.player
        args = self.args
        return f"SubprocessSeat({player=}, {args=})"

    @classmethod
    async def create(cls, player: int, args: Sequence[str]):
        self = cls()
        self.player = player
        self.args = args
        self.process = await asyncio.create_subprocess_exec(
            *args,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
        )
        self.log_stderr_task = asyncio.create_task(self._log_stderr())
        return self

    async def close(self) -> None:
        await self.process.wait()
        await self.log_stderr_task

    async def _log_stderr(self) -> None:
        assert self.process.stderr is not None

        while line := await self.process.stderr.readline():
            print(f"[seat {self.player}] {line.decode()}", end="")

    async def send(self, command: Command) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write((write_command(command) + "\n").encode())
        await self.process.stdin.drain()

    async def receive(self) -> str:
        assert self.process.stdout is not None
        return (await self.process.stdout.readline()).decode().removesuffix("\n")
