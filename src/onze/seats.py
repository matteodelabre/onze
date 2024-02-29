from collections.abc import Sequence
from typing import Protocol
from asyncio import gather, create_task, create_subprocess_exec, Task
from asyncio.subprocess import Process, PIPE
from pathlib import Path
from .box import create_boxed_subprocess_exec, Box
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

    async def communicate(self, command: Command) -> str:
        """Send a command to this seat and wait for a response."""
        _, response = await gather(self.send(command), self.receive())
        return response


class TerminalSeat(Seat):
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


class SubprocessSeat(Seat):
    """Unattended seat controlled by a separate process."""

    player: int
    args: Sequence[str]
    box: Box | None
    process: Process
    log_stderr_task: Task

    def __str__(self) -> str:
        player = self.player
        args = self.args
        box = str(self.box.root) if self.box is not None else None
        return f"{self.__class__.__name__}({player=}, {args=}, {box=})"

    @classmethod
    async def create(
        cls,
        player: int,
        *args: str,
        cwd: Path | str | None = None,
        box: Box | None = None,
    ):
        self = cls()
        self.player = player
        self.args = args
        self.box = box

        if box is None:
            self.process = await create_subprocess_exec(
                *args,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
                cwd=cwd,
            )
        else:
            self.process = await create_boxed_subprocess_exec(
                *args,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
                box=box,
                cwd=cwd,
            )

        self.log_stderr_task = create_task(self._log_stderr())
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


class Table:
    def __init__(self, seats: dict[int, Seat]):
        self.seats = seats

    async def broadcast(self, command: Command) -> None:
        await gather(*(seat.send(command) for seat in self.seats.values()))

    async def close(self) -> None:
        await gather(*(seat.close() for seat in self.seats.values()))

    async def send(self, player: int, command: Command) -> None:
        await self.seats[player].send(command)

    async def receive(self, player: int) -> str:
        return await self.seats[player].receive()

    async def communicate(self, player: int, command: Command) -> str:
        return await self.seats[player].communicate(command)
