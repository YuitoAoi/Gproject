import os
import shutil
from pathlib import Path

from src.services.interfaces.file_repository import FileRepository


class WindowsFileRepository(FileRepository):

    def __init__(self, working_dir: str = "."):
        self._working_dir = Path(working_dir).resolve()

    # ── 内部工具 ──────────────────────────────────────────────

    def _resolve(self, path: str) -> str:
        """将相对路径解析为以 working_dir 为基准的绝对路径。"""
        p = Path(path)
        if p.is_absolute():
            return str(p)
        return str(self._working_dir / p)

    def _ensure_parent(self, path: str) -> None:
        """确保目标文件的父目录存在。"""
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    # ── FileRepository 实现 ───────────────────────────────────

    def create(self, path: str) -> None:
        full = self._resolve(path)
        try:
            fd = os.open(full, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
        except FileNotFoundError:
            self._ensure_parent(full)
            fd = os.open(full, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)

    def copy(self, from_path: str, to_path: str) -> None:
        src = self._resolve(from_path)
        dst = self._resolve(to_path)
        self._ensure_parent(dst)
        shutil.copy2(src, dst)

    def move(self, from_path: str, to_path: str) -> None:
        src = self._resolve(from_path)
        dst = self._resolve(to_path)
        self._ensure_parent(dst)
        shutil.move(src, dst)

    def rename(self, from_path: str, to_path: str) -> None:
        self.move(from_path, to_path)

    def read(self, url: str) -> bytes:
        full = self._resolve(url)
        with open(full, "rb") as f:
            return f.read()

    def get_size(self, url: str) -> int:
        return os.path.getsize(self._resolve(url))

    def size(self, url: str) -> int:
        return self.get_size(url)

    def get_file_ext(self, url: str) -> str:
        return os.path.splitext(url)[1]

    def write(self, url: str, data: bytes) -> None:
        full = self._resolve(url)
        self._ensure_parent(full)
        try:
            fd = os.open(full, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_BINARY)
            with os.fdopen(fd, "wb") as f:
                f.write(data)
        except FileNotFoundError:
            self._ensure_parent(full)
            fd = os.open(full, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_BINARY)
            with os.fdopen(fd, "wb") as f:
                f.write(data)

    def over_write(self, url: str, data: bytes) -> None:
        full = self._resolve(url)
        self._ensure_parent(full)
        with open(full, "wb") as f:
            f.write(data)

    def exists(self, url: str) -> bool:
        return os.path.isfile(self._resolve(url))

    def delete(self, url: str) -> bool:
        full = self._resolve(url)
        try:
            os.remove(full)
            return True
        except FileNotFoundError:
            return False

    # ── 分片读写 ──────────────────────────────────────────────

    def read_chunk(self, url: str, offset: int, size: int) -> bytes:
        full = self._resolve(url)
        with open(full, "rb") as f:
            f.seek(offset)
            return f.read(size)

    def write_chunk(self, url: str, offset: int, data: bytes) -> None:
        full = self._resolve(url)
        self._ensure_parent(full)
        with open(full, "r+b") as f:
            f.seek(offset)
            f.write(data)

    # ── 目录操作 ──────────────────────────────────────────────

    def makedirs(self, path: str) -> None:
        full = self._resolve(path)
        os.makedirs(full, exist_ok=True)

    def is_dir(self, url: str) -> bool:
        return os.path.isdir(self._resolve(url))

    def list_dir(self, url: str) -> list[str]:
        full = self._resolve(url)
        if not os.path.isdir(full):
            raise NotADirectoryError(full)
        return os.listdir(full)

    def delete_dir(self, url: str) -> bool:
        full = self._resolve(url)
        try:
            shutil.rmtree(full)
            return True
        except FileNotFoundError:
            return False
