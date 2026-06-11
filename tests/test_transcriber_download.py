import io
import threading
from unittest.mock import patch

import pytest

import transcriber


def test_repo_id_maps_known_model():
    assert transcriber._repo_id("small") == "Systran/faster-whisper-small"


def test_repo_id_passthrough_for_unknown():
    assert transcriber._repo_id("some/custom-repo") == "some/custom-repo"


def test_is_model_downloaded_true_when_cached():
    with patch("transcriber.snapshot_download", return_value="/fake/path"):
        assert transcriber.is_model_downloaded("small") is True


def test_is_model_downloaded_false_when_missing():
    with patch("transcriber.snapshot_download", side_effect=FileNotFoundError):
        assert transcriber.is_model_downloaded("small") is False


def test_download_model_skips_when_already_downloaded():
    calls = []

    def fake_snapshot(repo, **kwargs):
        calls.append(kwargs)
        if kwargs.get("local_files_only"):
            return "/fake/path"  # already present
        raise AssertionError("should not perform a full download")

    with patch("transcriber.snapshot_download", side_effect=fake_snapshot):
        transcriber.download_model("small")
    # only the local_files_only existence check happened
    assert calls and all(k.get("local_files_only") for k in calls)


def test_download_model_reports_progress():
    progress = []

    def fake_snapshot(repo, **kwargs):
        if kwargs.get("local_files_only"):
            raise FileNotFoundError  # not yet downloaded
        tqdm_class = kwargs["tqdm_class"]
        bar = tqdm_class(total=100, file=io.StringIO())
        bar.update(40)
        bar.update(60)
        return "/fake/path"

    with patch("transcriber.snapshot_download", side_effect=fake_snapshot):
        transcriber.download_model("small", progress_cb=lambda d, t: progress.append((d, t)))

    assert progress[-1] == (100, 100)


def test_download_model_cancellation():
    cancel = threading.Event()
    cancel.set()  # cancel immediately

    def fake_snapshot(repo, **kwargs):
        if kwargs.get("local_files_only"):
            raise FileNotFoundError
        tqdm_class = kwargs["tqdm_class"]
        bar = tqdm_class(total=100, file=io.StringIO())
        bar.update(10)  # must raise before doing real work
        return "/fake/path"

    with patch("transcriber.snapshot_download", side_effect=fake_snapshot):
        with pytest.raises(transcriber.DownloadCancelled):
            transcriber.download_model("small", cancel_event=cancel)
