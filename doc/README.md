## 文档生成

### 安装MkDocs

安装文档生成工具[MkDocs](https://www.mkdocs.org/)
```shell
pip install mkdocs
```

### 安装插件

安装主题[mkdocs-material](https://squidfunk.github.io/mkdocs-material/)
```shell
pip install mkdocs-material
```

安装从markdown文件引用插件[mkdocs-include-markdown-plugin](https://github.com/mondeja/mkdocs-include-markdown-plugin)
```shell
pip install mkdocs-include-markdown-plugin
```

安装从API中提取文档插件[mkdocstrings](https://github.com/mkdocstrings/mkdocstrings)
```shell
pip install mkdocstrings
```

### 文档预览与生成

在线预览文档：在项目的`./doc`目录下执行
```shell
mkdocs serve
```

生成完整文档：在项目的`./doc`目录下执行
```shell
mkdocs build
```
生成后的文档在`./doc/site`目录下

## 参考
1. [从Python源码注释，自动生成API文档 - SegmentFault 思否](https://segmentfault.com/a/1190000040801843)
2. [Python技术文档最佳实践 - 知乎](https://zhuanlan.zhihu.com/p/333742823)
