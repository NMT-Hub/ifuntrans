import pytest
import pandas


@pytest.mark.skip(reason="tm.xlsx is not available")
def test_tm():
    init_tm_indexing()
    # search
    tm_path = get_tm_path()
    tm_df = pandas.read_excel(tm_path)
    tm_df = tm_df.iloc[1:]

    # random choose some rows
    rows = tm_df.sample(10).iterrows()

    for _, row in rows:
        source_lang = row.index[1]
        for target_lang in tm_df.columns[2:]:
            string = str(row[source_lang])
            source, _ = search_tm(string, source_lang, target_lang)
            assert source in string
