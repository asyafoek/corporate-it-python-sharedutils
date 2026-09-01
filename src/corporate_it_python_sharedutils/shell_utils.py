import subprocess
from typing import Optional


def execute_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """
    Execute a shell command.

    Args:
        command: Shell command.
        cwd: Working directory.
        timeout: Timeout in seconds.
        check: Raise exception on non-zero exit code.

    Returns:
        subprocess.CompletedProcess
    """
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        timeout=timeout,
        capture_output=True,
        text=True,
        check=check,
    )

    return result