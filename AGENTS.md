# AGENTS.md

## 沟通方式

- 默认中文回复；代码、命令、变量名、文件路径保持英文
- 结论先行，简洁直接
- 不制造未经确认的数据

## 前后端联动原则

- 后端 API、Response、Schema 或字段发生变化时，必须检查前端是否受到影响。
- 如果前端需要修改：必须同步修改相关前端代码，并进行前后端联调。
- 如果当前阶段不需要修改前端：不得无关修改前端。
- 任何 API Breaking Change：必须同时评估前端影响。

## Git

- 不自动 `git commit` 或 `git push`，除非明确要求
- 提交前先展示将要提交的变更摘要
- commit message 使用简洁英文

## 红线操作

以下操作必须先询问用户：

- 删除文件、目录或 git 历史
- 修改密钥、token、证书、CI/CD 配置
- `git push`、`git rebase`、`git reset --hard`、强制推送
- 公开发布（生产部署等）

## 开发阶段规则

项目开发必须遵循：[docs/development/roadmap.md](docs/development/roadmap.md)（阶段任务表，决定开发顺序与完成标准）。

模块依赖必须遵循：[docs/development/dependency-tree.md](docs/development/dependency-tree.md)（模块依赖关系，决定前置条件）。

禁止跳过依赖模块开发。

具体规则：

1. 必须严格按照 roadmap.md 中的 Phase 顺序开发。
2. 当前 Phase 没有完成之前，不允许开始下一阶段。
3. 每完成一个 Phase，需要：
   - 总结完成内容
   - 列出修改文件
   - 运行测试
   - 检查 Bug
   - 等待用户确认
4. 不允许一次生成整个项目代码。
5. 不允许为了完成需求提前创建未来阶段代码。
6. 如果当前阶段依赖其他模块，先说明依赖关系。
