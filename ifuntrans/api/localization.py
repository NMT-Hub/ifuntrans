from ifuntrans.api import IfunTransModel


def upload_file(task_id: str, bucket_name: str, object_name: str) -> IfunTransModel:
    pass


class ProgressModel(IfunTransModel):
    task_id: str
    progress: float


def progress(task_id) -> ProgressModel:
    pass


class DownloadFileModel(IfunTransModel):
    task_id: str
    url: str
    expire_time: str


def download_file(task_id) -> DownloadFileModel:
    pass
