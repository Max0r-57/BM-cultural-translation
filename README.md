This is a personal translation project made by a college student who studies translation

# 大英博物馆展厅页面 · 中文本地化

本项目将大英博物馆官网的三个页面译为中文，并保留原网站的版式与风格：

| 页面 | 原文链接 | 译文文件 |
| --- | --- | --- |
| 展厅（首页） | https://www.britishmuseum.org/collection/galleries | `index.html` |
| 第1展厅 · 启蒙运动 | https://www.britishmuseum.org/collection/galleries/enlightenment | `enlightenment.html` |
| 第25展厅 · 非洲 | https://www.britishmuseum.org/collection/galleries/africa | `africa.html` |

在线浏览：https://max0r-57.github.io/BM-cultural-translation/

## 翻译原则

- 只替换文本（正文、标题、导航、按钮文字、图片替代文字、图片说明、灯箱说明等），HTML 结构、样式和脚本保持原样。
- “第1展厅”“第25展厅”（以及指向这两个展厅的其他入口）链接到本站的译文页面，其余按钮和链接一律保留官网原链接。
- 页面中已保存的图片存放在 `galleries_files/`、`enlightenment_files/`、`africa_files/` 文件夹中。

## 目录说明

- `source/`：用浏览器“网页，全部”方式保存的英文原始网页（压缩包）。
- `tools/trans.py`：英中对照译文表（全部译文都在这里，便于查阅和修改）。
- `tools/build.py`：把译文替换进原始网页的脚本。修改译文后，将 `source/` 中的压缩包解压到某个目录，然后运行
  `cd tools && python3 build.py <解压目录> ..` 即可重新生成页面。

内容版权归大英博物馆理事会所有（© The Trustees of the British Museum），本项目仅用于翻译课程学习。
