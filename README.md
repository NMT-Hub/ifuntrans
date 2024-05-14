# IFUN 翻译项目

## 快速开始
启动redis（用于请求缓存，以及限制请求频率）
```
docker run --network="host" --name ifuntrans-redis -d redis:6.2.14
```
安装依赖（需要安装
```
poetry install
```
准备环境变量
```
source .env
```
启动服务
```
poetry run python server.py
```
使用命令行翻译excel文件
```
poetry run python main.py /path/to/input.xlsx
```
其他参数使用`python main.py --help`查看，具体使用案例见[使用案例](./docs/使用案例.md)

使用命令行翻译word文件（RTF，doc，pdf格式请用wps超级会员转换成docx格式）
```
poetry run python translate_docx.py /path/to/docx
```
其他参数使用`python translate_docx.py --help`查看，具体使用案例见[使用案例](./docs/使用案例.md)

## 容器化部署
构建镜像
```
docker build -t ifuntrans .
```
启动测试环境服务（其中REDIS\_HOST改成redis的访问地址）
```
docker run --env-file .env -e REDIS_HOST=172.26.0.3 -p 8188:8888 --name ifuntrans-test -d ifuntrans:latest
```
启动正式环境服务（其中REDIS\_HOST改成redis的访问地址）
```
docker run --env-file .env_formal -e REDIS_HOST=172.26.0.3 -p 8189:8888 --name ifuntrans -d ifuntrans:prod
```

## 其他文档
- [接口文档](docs/机翻引擎对接文档.md)
