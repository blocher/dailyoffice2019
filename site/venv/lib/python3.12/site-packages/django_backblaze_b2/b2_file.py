from io import BytesIO
from logging import getLogger
from typing import IO, Any, Callable, Dict, Optional, Union

from b2sdk.v2 import Bucket
from django.core.files.base import File

logger = getLogger("django-backblaze-b2")


class B2File(File):
    """Read/Write as lazy as possible"""

    def __init__(
        self,
        name: str,
        bucket: Bucket,
        size_provider: Callable[[str], int],
        file_metadata: Dict[str, Any],
        mode: str,
    ):
        self.name: str = name
        self._bucket: Bucket = bucket
        self._size_provider = size_provider
        self._file_metadata = file_metadata
        self._mode: str = mode
        self._has_unwritted_data: bool = False
        self._contents: Optional[IO] = None

    @property
    def file(self) -> Union[IO[Any], None]:
        if self._contents is None:
            self._contents = self._read_file_contents()
        return self._contents

    @file.setter
    def file(self, value: IO[Any]) -> None:
        self._contents = value

    def _read_file_contents(self) -> BytesIO:
        currently_downloading_file = self._bucket.download_file_by_name(file_name=self.name)
        bytes_io = BytesIO()
        currently_downloading_file.save(bytes_io)
        contents = BytesIO(bytes_io.getvalue())
        bytes_io.close()
        return contents

    @property
    def size(self) -> int:
        if not hasattr(self, "_size"):
            self._size = self._size_provider(self.name)
        return self._size

    def read(self, num_bytes: Optional[int] = None) -> bytes:
        return self.file.read(num_bytes if isinstance(num_bytes, int) else -1) if self.file else bytes()

    def write(self, content) -> int:
        if "w" not in self._mode:
            raise AttributeError("File was not opened for write access.")
        self.file = BytesIO(content)

        self._has_unwritted_data = True
        return len(content)

    def close(self) -> None:
        if self.file:
            if self._has_unwritted_data:
                self.save_and_retrieve_file(self.file)
            self.file.close()

    def save_and_retrieve_file(self, content: IO[Any]) -> str:
        """
        Save and retrieve the filename.
        If the file exists it will make another version of that file.
        """
        logger.debug(f"Saving {self.name} to b2 bucket ({self._bucket.get_id()})")
        self._bucket.upload_bytes(
            data_bytes=content.read(),
            file_name=self.name,
            file_info=self._file_metadata,
        )
        self._has_unwritted_data = False
        return self.name
