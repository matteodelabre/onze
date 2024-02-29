from uuid import uuid4
import os
import io
from pathlib import Path
import signal
import select
import asyncio
from typing import Self
from dataclasses import dataclass, field
from . import linux


@dataclass
class Mount:
    destination: Path
    source: Path | None = None
    options: list[str] = field(default_factory=list)
    type: str = "none"


@dataclass
class Box:
    # Root directory under which the subprocess is boxed
    root: Path = Path("")

    # Mounts setup before the subprocess is started
    mounts: list[Mount] = field(default_factory=list)

    # Maximum number of processes or threads (or -1 for no limit)
    tasks_limit: int = -1

    # Maximum RAM usage in bytes (or -1 for no limit)
    ram_limit: int = -1

    # Maximum swap usage in bytes (or -1 for no limit)
    swap_limit: int = -1


class BoxedProcess:
    """Run and communicate with a subprocess running in a contained environment."""

    args: list[str]
    box: Box
    pid: int | None
    returncode: int | None
    _cgroup: Path | None
    _pidfd: int | None
    stdin: io.BufferedWriter | None
    stdout: io.BufferedReader | None
    stderr: io.BufferedReader | None

    def __init__(
        self,
        args: list[str],
        box: Box = Box(),
        cwd: Path | str | None = None,
        stdin: int | io.FileIO | None = None,
        stdout: int | io.FileIO | None = None,
        stderr: int | io.FileIO | None = None,
    ):
        """
        Initialize a contained subprocess.

        :param args: List of arguments used to spawn the process
        :param box: Isolation settings
        :param stdin: File descriptor, stream or flag for handling standard input
        :param stdout: File descriptor, stream or flag for handling standard output
        :param stderr: File descriptor, stream or flag for handling standard error
        """
        self.args = args
        self.box = box

        # Open requested standard streams
        self.stdin = None
        self.stdout = None
        self.stderr = None

        stdin_read, stdin_write = -1, -1
        stdout_read, stdout_write = -1, -1
        stderr_read, stderr_write = -1, -1

        devnull = os.open(os.devnull, os.O_RDWR)

        match stdin:
            case None:
                pass

            case asyncio.subprocess.PIPE:
                stdin_read, stdin_write = os.pipe()

            case asyncio.subprocess.DEVNULL:
                stdin_read = devnull

            case int():
                stdin_read = stdin

            case _:
                stdin_read = stdin.fileno()

        match stdout:
            case None:
                pass

            case asyncio.subprocess.PIPE:
                stdout_read, stdout_write = os.pipe()

            case asyncio.subprocess.DEVNULL:
                stdout_write = devnull

            case int():
                stdout_write = stdout

            case _:
                stdout_write = stdout.fileno()

        match stderr:
            case None:
                pass

            case asyncio.subprocess.PIPE:
                stderr_read, stderr_write = os.pipe()

            case asyncio.subprocess.DEVNULL:
                stderr_write = devnull

            case int():
                stderr_write = stderr

            case _:
                stderr_write = stderr.fileno()

        # Replace current standard streams for child process
        old_stdin = -1
        old_stdout = -1
        old_stderr = -1

        if stdin_read != -1:
            old_stdin = os.dup(0)
            os.dup2(stdin_read, 0)

        if stdout_write != -1:
            old_stdout = os.dup(1)
            os.dup2(stdout_write, 1)

        if stderr_write != -1:
            old_stderr = os.dup(2)
            os.dup2(stderr_write, 2)

        try:
            cgroup = self._setup_cgroup()
            pid = linux.clone(
                flags=(
                    linux.Clone.NEWCGROUP
                    | linux.Clone.NEWIPC
                    | linux.Clone.NEWNET
                    | linux.Clone.NEWNS
                    | linux.Clone.NEWPID
                    | linux.Clone.NEWUSER
                    | linux.Clone.NEWUTS
                ),
                cgroup=cgroup,
            )
            os.close(cgroup)

            if pid == 0:
                self._exec_child(cwd)
            else:
                self.pid = pid
                self.returncode = None
                self._pidfd = os.pidfd_open(pid)

                # Initialize communication streams
                if stdin_write != -1:
                    self.stdin = open(stdin_write, "wb")

                if stdout_read != -1:
                    self.stdout = open(stdout_read, "rb")

                if stderr_read != -1:
                    self.stderr = open(stderr_read, "rb")
        finally:
            # Restore original streams and close unused pipe ends
            if old_stdin != -1:
                os.dup2(old_stdin, 0)

            if old_stdout != -1:
                os.dup2(old_stdout, 1)

            if old_stderr != -1:
                os.dup2(old_stderr, 2)

            if stdin_read != -1:
                os.close(stdin_read)

            if stdout_write != -1:
                os.close(stdout_write)

            if stderr_write != -1:
                os.close(stderr_write)

    def _exec_child(self, cwd: Path | str | None) -> None:
        # The new root needs to appear as a mount point for the
        # pivot_root call, so we start by bind-mounting it onto itself
        mounts = [
            Mount(
                source=Path(self.box.root),
                destination=Path("/"),
                type="none",
                options=["rbind", "ro"],
            ),
        ] + self.box.mounts

        for mount in mounts:
            source = mount.source if mount.source is not None else Path(mount.type)
            destination = self.box.root / mount.destination.relative_to("/")
            options = linux.Mount(0)

            for option in mount.options:
                match option:
                    case "bind":
                        options |= linux.Mount.BIND

                    case "rbind":
                        options |= linux.Mount.BIND
                        options |= linux.Mount.REC

                    case "ro":
                        options |= linux.Mount.RDONLY

                    case _:
                        raise ValueError(f"unknown mount option '{option}'")

            try:
                linux.mount(source, destination, mount.type, options)

                # A second syscall is needed to apply options to a bind mount
                if "ro" in mount.options and (
                    "bind" in mount.options or "rbind" in mount.options
                ):
                    options |= linux.Mount.REMOUNT
                    linux.mount(b"none", destination, "none", options)
            except OSError as err:
                raise RuntimeError(f"Failed to mount {mount}: {err.strerror}")

        # Change the root to the new root and unmount the old one
        linux.pivot_root(self.box.root, self.box.root)
        linux.umount(Path("/"), linux.Umount.DETACH)

        if cwd is not None:
            os.chdir(cwd)

        os.execvpe(self.args[0], self.args, {})

    def _setup_cgroup(self) -> int:
        cgroup_id = str(uuid4())
        user = os.getuid()

        # Create a cgroup under the user hierarchy
        cgroup_root = Path("/sys/fs/cgroup")
        user_root = (
            cgroup_root / "user.slice" / f"user-{user}.slice" / f"user@{user}.service"
        )
        box_root = user_root / f"box-{cgroup_id}"

        self._cgroup = box_root
        os.mkdir(box_root)

        # Configure cgroup limits
        if self.box.tasks_limit != -1:
            with open(box_root / "pids.max", "w") as file:
                print(self.box.tasks_limit, file=file)

        if self.box.ram_limit != -1:
            with open(box_root / "memory.max", "w") as file:
                print(self.box.ram_limit, file=file)

        if self.box.swap_limit != -1:
            with open(box_root / "memory.swap.max", "w") as file:
                print(self.box.swap_limit, file=file)

        return os.open(box_root, os.O_PATH)

    def poll(self) -> int | None:
        if self.returncode is not None:
            return self.returncode

        return self._check_exited()

    def wait(self, timeout: int | None = None) -> int | None:
        if self.returncode is not None:
            return self.returncode

        assert self._pidfd is not None
        waiter = select.poll()
        waiter.register(self._pidfd, select.POLLIN)
        waiter.poll(timeout)

        return self._check_exited()

    def _check_exited(self) -> int | None:
        assert self._pidfd is not None
        res = os.waitid(os.P_PIDFD, self._pidfd, os.WEXITED | os.WNOHANG)

        if res is not None:
            if res.si_code == os.CLD_EXITED:
                self.returncode = res.si_status
            else:
                self.returncode = -res.si_status

            self._cleanup()
            return self.returncode

        return None

    def _cleanup(self) -> None:
        if self._pidfd is not None:
            os.close(self._pidfd)
            self._pidfd = None

        if self._cgroup is not None:
            os.rmdir(self._cgroup)
            self._cgroup = None

    def communicate(self, input, timeout) -> tuple[str, str]:
        raise NotImplementedError()

    def send_signal(self, type: signal.Signals) -> None:
        if self._pidfd is not None:
            signal.pidfd_send_signal(self._pidfd, type)

    def terminate(self) -> None:
        self.send_signal(signal.SIGTERM)

    def kill(self) -> None:
        self.send_signal(signal.SIGKILL)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, value, traceback) -> None:
        if self.stdin is not None:
            self.stdin.close()
            self.stdin = None

        if self.stdout is not None:
            self.stdout.close()
            self.stdout = None

        if self.stderr is not None:
            self.stderr.close()
            self.stderr = None

        self.wait()


class BoxedSubprocessTransport(asyncio.base_subprocess.BaseSubprocessTransport):  # type: ignore
    def _start(self, args, shell, stdin, stdout, stderr, bufsize, box, cwd, **kwargs):
        self._proc = BoxedProcess(args, box, cwd, stdin, stdout, stderr)
        return self

    def _process_exited(self, returncode):
        super()._process_exited(returncode)
        self._proc._cleanup()


async def create_boxed_subprocess_exec(
    program: str,
    *args: str,
    box: Box,
    stdin: int | io.FileIO | None = None,
    stdout: int | io.FileIO | None = None,
    stderr: int | io.FileIO | None = None,
    limit: int = asyncio.streams._DEFAULT_LIMIT,  # type: ignore
    **kwargs,
):
    loop = asyncio.get_running_loop()
    protocol = asyncio.subprocess.SubprocessStreamProtocol(limit=limit, loop=loop)
    watcher = asyncio.get_child_watcher()

    with watcher:
        waiter = loop.create_future()
        transport = BoxedSubprocessTransport(
            loop=loop,
            protocol=protocol,
            args=(program,) + args,
            shell=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            bufsize=0,
            waiter=waiter,
            box=box,
            **kwargs,
        )
        watcher.add_child_handler(
            transport.get_pid(),
            lambda pid, returncode: loop.call_soon_threadsafe(
                loop.call_soon,
                transport._process_exited,
                returncode,
            ),
        )
        await waiter

    return asyncio.subprocess.Process(transport, protocol, loop)
