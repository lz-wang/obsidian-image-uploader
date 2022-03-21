## 关于

利用对象云存储接口，纯Python实现的一个Obsidian图床软件。

## 已完成功能
1. 支持将Obsidian笔记中的本地图片上传到图床服务器，并生成转换为通用Markdown链接的Markdown文件
2. 支持对Obsidian本地附件文件夹与远程图床文件夹的图片同步状态检查
3. 支持在检查同步状态时开启文件的MD5值校验（如果MD5校验不通过，那么同步到图床时本地的文件将覆盖远程文件）
4. 支持对Obsidian附件文件夹的所有附件批量同步到服务器

## 待开发功能
- [ ] 图片上传前压缩
- [ ] 图片上传前加水印

注意：
1. Obsidian附件的目录层级必须为1级，即附件文件夹下没有子文件夹，否则子文件夹内容将被忽略
2. 当前图床仅支持腾讯云COS（开通腾讯云COS存储服务参考[腾讯云COS](https://console.cloud.tencent.com/cos5)）

## 截图

### 主页面

![main-page](./doc/img/main-page.png)

### 图床服务器设置界面

![setting-page](./doc/img/setting-page.png)


## 快速开始

### 项目依赖

注意: `PySide6`使用缓存可能出现问题，所以此处加参数`--no-cache-dir`
```shell
pip install -r requirements.txt --no-cache-dir
```

### 开始开发

运行或调试根目录下的`main.py`即可。

### 使用Pyinstaller打包App为Windows`.exe`软件包
在项目根目录，首先删除之前的构建残存目录：
```shell
rm ./build
rm ./dist 
```
然后重新生成打包的文件:
```shell
pyinstaller main.py --clean --onedir --noconsole --icon "./assets/windows.ico" --name ObsidianImageUploader
```
此时，在项目根目录下的`dist`目录中，有以及打包完毕的软件，可以使用[Inno Setup](https://jrsoftware.org/)等Windows下打包软件打包为安装包即可。

### 使用Pyinstaller打包App为macOS`.app`软件包

在项目根目录，首先删除之前的构建残存目录：
```shell
sudo rm -rf ./build ./dist 
```

然后重新生成打包的文件:
```shell
sudo pyinstaller main.py --clean --onedir --noconsole --icon "./assets/macos.icns" --name ObsidianImageUploader
```

然后，在软件根目录的dist目录中：

- `./dist/main.app`: macOS专用软件包（无控制台），双击即可运行
- `./dist/main/main`: 可执行的二进制文件（有控制台）

### 使用Nuitka打包App为二进制文件

在项目根目录，首先删除之前的构建残存目录：
```shell
rm -rf main.build main.dist 
```

然后重新生成打包的文件:
```shell
python -m nuitka --follow-imports --enable-plugin=pyside6 --standalone main.py
```

尝试直接运行App二进制文件:
```shell
./main.dist/main
```

如果启动时有如下报错:
```shell
Traceback (most recent call last):
  File "/Users/lzwang/MyProjects/Python/obsidian-img-uploader/./main.dist/main.py", line 3, in <module>
ImportError: dlopen(/Users/lzwang/MyProjects/Python/obsidian-img-uploader/./main.dist/PySide6/QtWidgets.so, 2): Library not loaded: @rpath/QtQml.framework/Versions/A/QtQml
  Referenced from: /Users/lzwang/MyProjects/Python/obsidian-img-uploader/main.dist/libpyside6.abi3.6.2.dylib
  Reason: image not found
```

需要将Python环境中`PySide6`下的整个`Qt`目录拷贝至项目的`./main.dist/PySide6/`目录下即可(此处使用的是conda创建的`obsidian-img-uploader`环境):

```shell
cp -rf /Users/lzwang/.conda/envs/obsidian-img-uploader/lib/python3.9/site-packages/PySide6/Qt ~/MyProjects/Python/obsidian-img-uploader/main.dist/PySide6/
```

再次尝试运行App二进制文件即可:
```shell
./main.dist/main
```

## 参考资料

1. [Use Nuitka to compile a macOS executable from a Python Pyside6 app](https://www.loekvandenouweland.com/content/pyside6-nuitka-python.html)
2. [python 3.x - Pyinstaller error: 'SystemError: codesign failure!' on macOS - Stack Overflow](https://stackoverflow.com/questions/68884906/pyinstaller-error-systemerror-codesign-failure-on-macos)
3. [PNG转ICO图标格式 - 在线，免费，快速](https://png2icojs.com/zh/)
