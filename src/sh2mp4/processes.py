"""Subprocess cleanup shared by recording components."""

import asyncio
from contextlib import suppress


async def terminate_process(process, timeout=5):
    """Terminate and reap a child, including one that exited concurrently."""
    if process is None:
        return
    if process.returncode is None:
        with suppress(ProcessLookupError):
            process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout)
    except asyncio.TimeoutError:
        with suppress(ProcessLookupError):
            process.kill()
        await process.wait()
    except BaseException:
        with suppress(ProcessLookupError):
            process.kill()
        await asyncio.shield(process.wait())
        raise
