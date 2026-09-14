import os.path

import mrcfile  # type: ignore[import-untyped]
import numpy as np

from dragonET._make_video import _make_video


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
