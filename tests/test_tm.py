import tempfile
from ifuntrans.tm import init_tm_indexing


def test_tm(mocker):

    with tempfile.TemporaryDirectory() as temp:
        mocker.patch("ifuntrans.tm.get_index_path", return_value=temp)
        init_tm_indexing(force_reload=True)
