#!/bin/bash

FOLDER=$1
# 遍历指定目录下的所有文件
for file in $1/*.xlsx; do
    # 检查文件是否为文件而不是目录
    if [ -f "$file" ]; then
        # 获取文件名和扩展名
        filename=$(basename "$file")
        extension="${filename##*.}"
        filename="${filename%.*}"
        
        # 添加 '_translate' 并重命名文件
        new_filename="${filename}_translate.${extension}"
        new_file="$1/$new_filename"
        echo "Translating $file to $new_file"
        python main.py $file  --output $file -k  -i "I'm translating for mydevelopment game. Please use localized language when translating."
    fi
done

