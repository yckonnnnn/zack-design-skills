# Figma MCP 连接与排错

## 注册 MCP 服务器

### Codex (`~/.codex/config.toml`)

```toml
[features]
rmcp_client = true          # 老版本用 experimental_use_rmcp_client = true

[mcp_servers.figma]
url = "https://mcp.figma.com/mcp"
bearer_token_env_var = "FIGMA_OAUTH_TOKEN"
http_headers = { "X-Figma-Region" = "us-east-1" }
# 可选
# startup_timeout_sec = 10
# tool_timeout_sec = 60
```

Token 必须存在于**启动 Codex 的那个 shell 环境**里：

```bash
export FIGMA_OAUTH_TOKEN="<token>"      # 当前 shell
echo 'export FIGMA_OAUTH_TOKEN="<token>"' >> ~/.zshrc   # 持久化
echo $FIGMA_OAUTH_TOKEN                 # 验证非空
```

改完配置和 env 后**重启**客户端。

### Claude Code / 其他兼容 MCP 的客户端

用 streamable HTTP 类型指向 `https://mcp.figma.com/mcp`，鉴权走 Bearer token（同一个环境变量）。
具体字段名按客户端文档填写；关键是：**URL、Bearer 鉴权、区域头三样都要对**。

### Cursor

`~/.cursor/mcp.json` 里的 `mcpServers.figma`，同样用 URL + Bearer 结构。
桌面端 Dev Mode 的本地服务器是另一种接法（走 localhost），此时不需要 token。

---

## 区域

`X-Figma-Region` 必须与你的 Figma 组织区域一致（默认 `us-east-1`）。
区域写错的表现是**鉴权通过但请求 403/404**，很容易误判成 token 失效。

---

## 排错表

| 现象 | 原因 | 处理 |
|---|---|---|
| 工具列表里没有 figma | 配置没被读到 / 没重启 | 重启客户端；确认配置文件路径正确 |
| 401 / 认证失败 | token 没进环境、含引号、已过期 | `echo $FIGMA_OAUTH_TOKEN` 检查；去掉引号；重新签发 |
| OAuth 报错 | `rmcp_client` 未启用 | 打开 `[features].rmcp_client` |
| 403 / 404，但 token 看起来没问题 | 区域头不对 | 改 `X-Figma-Region` 与组织区域一致 |
| 超时 | 节点太大 / 网络 | 调大 `tool_timeout_sec`；先用 `get_metadata` 缩小范围 |
| 返回内容被截断 | 一次取了整个页面 | 用 `get_metadata` 定位子节点，逐个 `get_design_context` |
| 链接取不到节点 | 链接指向的是页面而不是 frame/layer | 重新复制具体 frame 或 layer 的链接 |
| 拿不到变量 | 该文件没用变量，用的是样式 | 用 `get_design_context` 里的样式值，手工建映射表 |

---

## 快速验证

1. 让客户端列出可用的 figma 工具 —— 能列出说明服务器已连上。
2. 用一个小图层的链接跑一次 `get_design_context` —— 能返回结构化数据说明鉴权与区域都对。
3. 跑一次 `get_screenshot` —— 能拿到图说明资源链路通。

三步都过，再开始正式还原。
