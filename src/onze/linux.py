import ctypes
import os
from pathlib import Path
from enum import IntFlag
import signal


libc = ctypes.CDLL(None, use_errno=True)


# Clone options (from linux/sched.h)
class Clone(IntFlag):
    NEWTIME = 0x00000080
    VM = 0x00000100  # Set if VM shared between processes
    FS = 0x00000200  # Set if fs info shared between processes
    FILES = 0x00000400  # Set if open files shared between processes
    SIGHAND = 0x00000800  # Set if signal handlers and blocked signals shared
    PIDFD = 0x00001000  # Set if a pidfd should be placed in parent
    PTRACE = 0x00002000  # Set if we want to let tracing continue on the child too
    VFORK = 0x00004000  # Set if the parent wants the child to wake it up on mm_release
    PARENT = 0x00008000  # Set if we want to have the same parent as the cloner
    THREAD = 0x00010000  # Same thread group?
    NEWNS = 0x00020000  # New mount namespace group
    SYSVSEM = 0x00040000  # Share system V SEM_UNDO semantics
    SETTLS = 0x00080000  # Create a new TLS for the child
    PARENT_SETTID = 0x00100000  # Set the TID in the parent
    CHILD_CLEARTID = 0x00200000  # Clear the TID in the child
    UNTRACED = (
        0x00800000  # Set if the tracing process can't force CLONE_PTRACE on this clone
    )
    CHILD_SETTID = 0x01000000  # Set the TID in the child
    NEWCGROUP = 0x02000000  # New cgroup namespace
    NEWUTS = 0x04000000  # New utsname namespace
    NEWIPC = 0x08000000  # New ipc namespace
    NEWUSER = 0x10000000  # New user namespace
    NEWPID = 0x20000000  # New pid namespace
    NEWNET = 0x40000000  # New network namespace
    IO = 0x80000000  # Clone io context
    CLEAR_SIGHAND = 0x100000000  # Clear any signal handler and reset to SIG_DFL
    INTO_CGROUP = (
        0x200000000  # Clone into a specific cgroup given the right permissions
    )


# Clone arguments (from linux/sched.h)
class CloneArgs(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_uint64),
        ("pidfd", ctypes.c_uint64),
        ("child_tid", ctypes.c_uint64),
        ("parent_tid", ctypes.c_uint64),
        ("exit_signal", ctypes.c_uint64),
        ("stack", ctypes.c_uint64),
        ("stack_size", ctypes.c_uint64),
        ("tls", ctypes.c_uint64),
        ("set_tid", ctypes.c_uint64),
        ("set_tid_size", ctypes.c_uint64),
        ("cgroup", ctypes.c_uint64),
    ]


# Mounting options (from linux/mount.h)
class Mount(IntFlag):
    RDONLY = 1  # Mount read-only
    NOSUID = 2  # Ignore suid and sgid bits
    NODEV = 4  # Disallow access to device special files
    NOEXEC = 8  # Disallow program execution
    SYNCHRONOUS = 16  # Writes are synced at once
    REMOUNT = 32  # Alter flags of a mounted FS
    MANDLOCK = 64  # Allow mandatory locks on an FS
    DIRSYNC = 128  # Directory modifications are synchronous
    NOSYMFOLLOW = 256  # Do not follow symlinks
    NOATIME = 1024  # Do not update access times
    NODIRATIME = 2048  # Do not update directory access times
    BIND = 4096
    MOVE = 8192
    REC = 16384
    SILENT = 32768
    POSIXACL = 1 << 16  # VFS does not apply the umask
    UNBINDABLE = 1 << 17  # Change to unbindable
    PRIVATE = 1 << 18  # Change to private
    SLAVE = 1 << 19  # Change to slave
    SHARED = 1 << 20  # Change to shared
    RELATIME = 1 << 21  # Update atime relative to mtime/ctime
    KERNMOUNT = 1 << 22  # This is a kern_mount call
    I_VERSION = 1 << 23  # Update inode I_version field
    STRICTATIME = 1 << 24  # Always perform atime updates
    LAZYTIME = 1 << 25  # Update the on-disk [acm]times lazily


# Unmounting options (from linux/fs.h)
class Umount(IntFlag):
    FORCE = 0x00000001  # Attempt to forcibily umount
    DETACH = 0x00000002  # Just detach from the tree
    EXPIRE = 0x00000004  # Mark for expiry
    NOFOLLOW = 0x00000008  # Don't follow symlink on umount


NR_pivot_root = 155
NR_clone3 = 435


def raise_errno(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if result == -1:
            errno = ctypes.get_errno()
            raise OSError(errno, os.strerror(errno))

        return result

    return wrapper


@raise_errno
def clone(flags: Clone, cgroup: int | None = None):
    if cgroup is not None:
        flags |= Clone.INTO_CGROUP
    else:
        cgroup = 0

    args = CloneArgs(flags=flags, exit_signal=signal.SIGCHLD, cgroup=cgroup)
    return libc.syscall(NR_clone3, ctypes.byref(args), ctypes.sizeof(args))


@raise_errno
def mount(
    source: Path, target: Path, type: str = "none", flags: Mount = Mount(0)
) -> None:
    return libc.mount(bytes(source), bytes(target), type.encode(), int(flags), None)


@raise_errno
def umount(target: Path, flags: Umount = Umount(0)) -> None:
    return libc.umount2(bytes(target), int(flags))


@raise_errno
def pivot_root(new_root: Path, put_old: Path) -> None:
    return libc.syscall(NR_pivot_root, bytes(new_root), bytes(put_old))
