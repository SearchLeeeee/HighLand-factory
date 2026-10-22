# code/

代码根目录。这是一个占位文件：接入真实项目后，用项目自己的 `README.md`
替换本文件，并删除 `code/.gitkeep`。

约定：

- 可执行内容只放在 `code/`；长期文档只放在 `wiki/`。
- 子项目结构、构建与运行命令登记在 `.factory/factory.yaml` 的 `commands`，
  由 `factory upgrade` 渲染进 `wiki/governance/workflow-profile.md`。
- 每个 owner 的责任路径在 `factory.yaml` 的 `owners[].paths` 中声明，不要只在
  这里用文字描述。
- 代码与契约变更必须同步 `wiki/` 对应权威文档；只有代码没有文档，视为未完成。
