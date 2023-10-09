# IFUN 翻译项目

## 快速开始
安装依赖
```
poetry install
```
启动服务
```
poetry run python server.py
```
使用命令行翻译excel文件
```
poetry run python main.py /path/to/input.xlsx --languages en,ru --source-column 1
```
## 容器化部署
构建镜像
```
docker build -t ifuntrans .
```
启动测试环境服务
```
docker run --env-file .env -p 8188:8888 --name ifuntrans-test -d ifuntrans:latest
```
启动正式环境服务
```
docker run --env-file .env_formal 8189:8888 --name ifuntrans -d ifuntrans:pord
```

## 其他文档
- [接口文档](docs/机翻引擎对接文档.md)
