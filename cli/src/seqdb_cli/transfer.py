from __future__ import annotations

import anyio
from pathlib import Path
from typing import Any

import httpx
from rich.progress import Progress

from seqdb_cli.utils import compute_md5


async def upload_files(
    base_url: str,
    token: str,
    files: list[Path],
    max_concurrent: int = 4,
    show_progress: bool = True,
) -> list[dict[str, Any]]:
    results = []
    sem = anyio.Semaphore(max_concurrent)
    headers = {"Authorization": f"Bearer {token}"}

    progress = Progress(disable=not show_progress)
    with progress:
        overall = progress.add_task("Uploading", total=len(files))

        async def _upload_one(file_path: Path) -> dict[str, Any]:
            async with sem:
                async with httpx.AsyncClient(timeout=300.0) as http:
                    resp = await http.post(
                        f"{base_url}/api/v1/staging/initiate",
                        headers=headers,
                        json={"filename": file_path.name, "file_size": file_path.stat().st_size},
                    )
                    resp.raise_for_status()
                    init = resp.json()

                    with open(file_path, "rb") as f:
                        put_resp = await http.put(init["presigned_url"], content=f.read())
                        put_resp.raise_for_status()

                    complete_resp = await http.post(
                        f"{base_url}/api/v1/staging/complete/{init['staged_file_id']}",
                        headers=headers,
                    )
                    complete_resp.raise_for_status()

                    progress.advance(overall)
                    return {
                        "staged_file_id": init["staged_file_id"],
                        "filename": file_path.name,
                        "md5": compute_md5(file_path),
                    }

        async with anyio.create_task_group() as tg:
            async def _run(fp: Path):
                result = await _upload_one(fp)
                results.append(result)

            for f in files:
                tg.start_soon(_run, f)

    return results


async def download_files(
    urls: list[tuple[str, str]],
    output_dir: Path,
    max_concurrent: int = 4,
    show_progress: bool = True,
) -> list[Path]:
    results = []
    sem = anyio.Semaphore(max_concurrent)
    output_dir.mkdir(parents=True, exist_ok=True)

    progress = Progress(disable=not show_progress)
    with progress:
        overall = progress.add_task("Downloading", total=len(urls))

        async def _download_one(url: str, filename: str) -> Path:
            async with sem:
                dest = output_dir / filename
                async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as http:
                    resp = await http.get(url)
                    resp.raise_for_status()
                    dest.write_bytes(resp.content)
                progress.advance(overall)
                return dest

        async with anyio.create_task_group() as tg:
            async def _run(u: str, fn: str):
                result = await _download_one(u, fn)
                results.append(result)

            for url, filename in urls:
                tg.start_soon(_run, url, filename)

    return results
