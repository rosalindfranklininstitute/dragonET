from dragonET.command_line._make_video import _make_video
import numpy as np
import mrcfile  # type: ignore[import-untyped]
import os.path


def test_make_video(tmpdir):

    def write_mrc_file():
        data = np.ones((10, 100, 100), dtype="float32")
        handle = mrcfile.new(os.path.join(tmpdir, "data.mrc"))
        handle.set_data(data)

    write_mrc_file()

    _make_video(
        os.path.join(tmpdir, "data.mrc"), os.path.join(tmpdir, "movie.mp4"), factor=1
    )

    assert os.path.exists(os.path.join(tmpdir, "movie.mp4"))
