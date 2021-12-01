## 关于

利用对象存储接口实现的一个Obsidian图床软件。

## 特点

1. 使用100%的Python实现，支持macOS和Linux平台
2. 支持将Obsidian笔记中的本地图片链接转变为通用Markdown链接
3. 支持将Obsidian的附件全部同步到图床服务器上

注意：

- 当前图床仅支持腾讯云COS（开通腾讯云COS存储服务参考[腾讯云COS](https://console.cloud.tencent.com/cos5)）

## 截图

### 主页面

![main-page](./doc/img/main-page.png)

### 图床服务器设置界面

![setting-page](./doc/img/setting-page.png)


## 快速开始

### 项目依赖：
```shell
pip install cos-python-sdk-v5
pip install pyqt5
```

### 开始开发

运行或调试根目录下的`main.py`即可。
