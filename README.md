# 社会政治调研助手

基于DeepSeek V4 Pro的学术调研智能体，专注于社会政治分析框架。

## 快速部署

### 方案一：Streamlit Cloud（推荐）

1. **上传到GitHub**
   ```bash
   cd research-agent
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/research-agent.git
   git push -u origin main
   ```

2. **部署到Streamlit Cloud**
   - 访问 https://share.streamlit.io
   - 用GitHub账号登录
   - 点击 "New app"
   - 选择你的仓库和 `app.py` 文件
   - 点击 "Deploy"

3. **配置Secrets**
   - 在Streamlit Cloud界面点击 "Advanced settings"
   - 在Secrets中添加：
   ```
   DEEPSEEK_API_KEY = "sk-your-api-key-here"
   ```

4. **获取链接**
   - 部署完成后会得到一个链接：`https://yourapp.streamlit.app`
   - 将此链接发给客户即可

---

### 方案二：本地运行

1. **安装依赖**
   ```bash
   cd research-agent
   pip install -r requirements.txt
   ```

2. **配置API Key**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # 编辑 secrets.toml，填入你的API Key
   ```

3. **运行应用**
   ```bash
   streamlit run app.py
   ```

4. **访问应用**
   - 打开浏览器访问：`http://localhost:8501`

---

### 方案三：Docker部署

1. **创建Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt

   EXPOSE 8501

   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **构建并运行**
   ```bash
   docker build -t research-agent .
   docker run -p 8501:8501 -e DEEPSEEK_API_KEY="your-key" research-agent
   ```

---

## 交付给客户

### 最简方案（推荐）

1. 用你自己的账号部署到Streamlit Cloud
2. 在Secrets中配置你的DeepSeek API Key
3. 把链接发给客户：`https://yourapp.streamlit.app`

**优点**：
- 客户无需任何配置
- 点开链接即用
- 你控制API Key和使用量

### 客户自己部署

如果客户需要私有化部署：

1. 提供整个 `research-agent` 文件夹
2. 让客户申请自己的DeepSeek API Key
3. 按照上述方案一或方案三部署

---

## 使用说明（可发给客户）

```
社会政治调研助手 - 使用指南

1. 访问链接：[你的应用链接]

2. 输入调研主题，例如：
   - "金正恩的国内政策决策与社会控制"
   - "朝鲜的社会福利政策演变"
   - "政治参与渠道与社会动员"

3. 点击"开始调研"按钮

4. 等待分析完成（约1-3分钟）

5. 下载调研报告（Markdown或TXT格式）

如有问题，请联系：[你的联系方式]
```

---

## 功能特性

- ✅ 基于DeepSeek V4 Pro大模型
- ✅ 社会政治分析框架
- ✅ 多维度分析（政治、经济、社会、历史）
- ✅ 流式输出，实时显示
- ✅ 支持下载Markdown和TXT格式
- ✅ 简洁易用的界面

---

## 技术栈

- **前端**：Streamlit
- **后端**：Python
- **AI模型**：DeepSeek V4 Pro
- **部署**：Streamlit Cloud / Docker

---

## 费用说明

- **Streamlit Cloud**：免费
- **DeepSeek API**：按使用量付费
  - 输入：¥1/百万tokens
  - 输出：¥2/百万tokens
  - 单次调研约消耗5000-10000 tokens，成本约¥0.01-0.02

---

## 常见问题

### Q: 客户需要自己申请API Key吗？
A: 不需要。如果你部署到Streamlit Cloud并配置好Secrets，客户只需要打开链接。

### Q: 如何控制使用量？
A: 可以在DeepSeek控制台设置用量限制。

### Q: 数据安全吗？
A: 数据通过DeepSeek API处理，不会被存储。如果需要更高的数据安全，可以私有化部署。

### Q: 可以自定义界面吗？
A: 可以修改 `app.py` 中的CSS样式和布局。

---

## 文件结构

```
research-agent/
├── app.py                      # 主应用
├── requirements.txt            # 依赖文件
├── README.md                   # 说明文档
└── .streamlit/
    ├── config.toml             # Streamlit配置
    └── secrets.toml.example    # API Key模板
```
