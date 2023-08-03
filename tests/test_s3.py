def test_s3():
    local_file_path = "./books/"
    save_file_path = "./books_translated/"
    end_suffix_list = ["pdf", "xlsx", "txt", "srt", "epub", "docx"]
    s3_obj = S3()
    s3 = s3_obj.conn_s3()
    bucket_name = "ifun-bi-ai-share"
    target_key = "ai-translate/target/"  # 到时候要写入的key
    keys = s3_obj.list_bucket_keys(s3, bucket_name)
    end_suffix_list = ["pdf", "xlsx", "txt", "srt", "epub", "docx"]
    end_suffix_list = set(end_suffix_list)
    for key in keys:
        book_name = str(key.split("/")[-1])
        suffix = str(book_name.split(".")[-1])
        if suffix not in end_suffix_list:
            continue
    s3_obj.download_file(s3, bucket_name=bucket_name, file_name=key, local_file=local_file_path, file=book_name)
    s3_obj.upload_file(s3, file_name=save_file_path + book_name, bucket=bucket_name, object_name=target_key + book_name)
