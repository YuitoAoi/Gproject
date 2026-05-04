
import abc
from typing import Optional


class FileRepository(abc.ABC):
    """文件存储抽象接口。"""

    @abc.abstractmethod
    def create(self, path: str) -> None:
        """创建一个空文件（类似 touch），若已存在则抛出 FileExistsError。"""

    @abc.abstractmethod
    def copy(self, from_path: str, to_path: str) -> None:
        """复制文件，保留元数据。若目标已存在则覆盖。"""

    @abc.abstractmethod
    def move(self, from_path: str, to_path: str) -> None:
        """移动/重命名文件。若目标已存在则覆盖。"""

    @abc.abstractmethod
    def read(self, url: str) -> bytes:
        """以字节形式读取文件全部内容。"""

    @abc.abstractmethod
    def get_size(self, url: str) -> int:
        """返回文件大小（字节）。"""

    @abc.abstractmethod
    def get_file_ext(self, url: str) -> str:
        """返回文件扩展名（含点号，如 '.txt'）。"""

    @abc.abstractmethod
    def write(self, url: str, data: bytes) -> None:
        """写入新文件，若文件已存在则抛出 FileExistsError。"""

    @abc.abstractmethod
    def over_write(self, url: str, data: bytes) -> None:
        """写入数据，若文件已存在则覆盖。"""

    @abc.abstractmethod
    def exists(self, url: str) -> bool:
        """检查文件是否存在。"""

    @abc.abstractmethod
    def delete(self, url: str) -> bool:
        """删除文件，成功返回 True，文件不存在返回 False。"""

    @abc.abstractmethod
    def read_chunk(self, url: str, offset: int, size: int) -> bytes:
        """读取文件指定偏移量的指定大小字节块，用于分片上传。"""

    @abc.abstractmethod
    def write_chunk(self, url: str, offset: int, data: bytes) -> None:
        """在指定偏移量写入数据块，用于分片写入。"""

    @abc.abstractmethod
    def size(self, url: str) -> int:
        """get_size 的别名，返回文件大小（字节）。"""

    @abc.abstractmethod
    def makedirs(self, path: str) -> None:
        """递归创建目录。"""

    @abc.abstractmethod
    def is_dir(self, url: str) -> bool:
        """检查路径是否为目录。"""

    @abc.abstractmethod
    def list_dir(self, url: str) -> list[str]:
        """列出目录下所有条目的名称。"""

    @abc.abstractmethod
    def delete_dir(self, url: str) -> bool:
        """递归删除目录。"""

    @abc.abstractmethod
    def rename(self, from_path: str, to_path: str) -> None:
        """重命名/移动，与 move 相同但语义更明确。"""
    
# class AsyncFileRepository(abc.ABC):
    
#     @abc.abstractmethod
#     async def create_async(self, path: Path) -> None:
#         pass

#     @abc.abstractmethod
#     async def copy_async(self, from_path: Path, to_path: Path):
#         pass

#     @abc.abstractmethod
#     async def move_async(self, from_path: Path, to_path: Path):
#         pass

#     @abc.abstractmethod
#     async def read_async(self, url: Path) -> bytes:
#         pass

#     @abc.abstractmethod
#     async def write_async(self, url: Path, data: bytes) -> None:
#         pass

#     @abc.abstractmethod
#     async def over_write_async(self, url: Path,data: bytes) -> None:
#         pass

#     @abc.abstractmethod
#     def exists(self, url: Path):
#         pass

#     @abc.abstractmethod
#     async def delete_async(self, url: Path):
#         pass