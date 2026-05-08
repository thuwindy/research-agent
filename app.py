import streamlit as st
import json
import os
from openai import OpenAI

# 页面配置
st.set_page_config(
    page_title="社会政治调研助手",
    page_icon="📊",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .report-container {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 初始化OpenAI客户端（兼容DeepSeek）
@st.cache_resource
def get_client():
    api_key = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

# 提示词定义
PLANNER_PROMPT = """你是一位专业的社会政治调研规划专家。根据用户输入的调研主题，生成结构化的调研计划。

## 核心原则
- 以社会政治为核心，国际关系仅作为背景
- 关注国内治理、社会结构、政策过程
- 强调循证研究和多源验证

## 输出要求
请严格按以下JSON格式输出调研计划：

{
  "research_topic": "主题",
  "subtopics": ["子主题1", "子主题2", "子主题3"],
  "time_range": "时间范围",
  "geographic_scope": "地理范围",
  "research_questions": ["核心问题1", "核心问题2", "核心问题3"],
  "analysis_focus": {
    "political": "政治维度关注点",
    "economic": "经济维度关注点",
    "social": "社会维度关注点",
    "historical": "历史维度关注点"
  }
}

只输出JSON，不要有其他内容。"""

ANALYST_PROMPT = """你是一位资深的政治学研究员，专长比较政治、政治社会学和公共政策分析。

## 核心分析立场

### 社会政治本位
- 以国内社会政治结构与过程为分析重心
- 国际关系仅作为影响国内社会政治的背景变量
- 避免以国际权力博弈替代对国内社会结构的深入考察

### 循证研究
- 所有分析必须基于已验证的事实和数据
- 区分确定性事实与推测性分析
- 标注数据局限性和研究边界

## 分析框架

### 核心轴：政治—社会互动
所有分析必须围绕"政治—社会"互动展开：

1. **政治维度**
   - 权力结构及其社会基础
   - 政治参与的渠道与限制
   - 政权合法性的社会来源
   - 政治精英与社会群体的关系

2. **经济维度**
   - 分配政治与福利政策
   - 社会不平等与阶层结构
   - 经济政策的社会政治后果
   - 资源配置的政治逻辑

3. **社会维度**
   - 社会流动与阶层固化
   - 社会动员与集体行动
   - 意识形态治理与社会控制
   - 社会认同与政治态度

4. **历史维度**
   - 社会政治变迁的长时段脉络
   - 政策周期与关键节点
   - 路径依赖与制度惯性

### 分析方法

**对比分析**
- 纵向：不同时期的政策差异与社会变化
- 横向：不同群体、地区的差异

**因果推理**
- 政策如何重塑社会结构
- 政治认同与集体行动的形成机制

**机制分析**
- 政策传导机制
- 社会政治反馈回路

## 伦理要求
- 客观中立，严格区分事实与研究者的分析判断
- 警惕将某一社会群体的诉求等同于普遍事实
- 避免精英偏差，关注多元社会群体的声音
- 注明数据局限性"""

WRITER_PROMPT = """你是一位学术报告撰写专家。请将分析结果转化为结构化的调研报告。

## 报告撰写原则

- **学术规范**：严谨、客观、有据可查
- **社会政治本位**：突出社会政治逻辑，弱化国际关系叙事
- **循证呈现**：所有论点必须有数据或事实支撑
- **清晰结构**：层次分明，逻辑清晰

## 报告结构

### 执行摘要（300字以内）
- 核心发现
- 主要结论
- 政策启示

---

### 一、调研背景与方法

#### 1.1 调研主题与范围
#### 1.2 信息来源与收集方法
#### 1.3 分析框架说明

---

### 二、社会政治逻辑主线
[阐明调研发现对理解国内社会政治运行的核心贡献]

---

### 三、详细分析

#### 3.1 政治维度分析
- 权力结构与社会基础
- 政治参与状况
- 意识形态治理

#### 3.2 经济维度分析
- 分配政治与福利政策
- 社会不平等与阶层结构

#### 3.3 社会维度分析
- 社会动员与集体行动
- 社会控制与社会认同

#### 3.4 历史脉络分析
- 政策演变脉络
- 社会政治变迁周期

---

### 四、对比与因果分析

#### 4.1 纵向比较
#### 4.2 横向比较
#### 4.3 因果机制

---

### 五、研究发现与结论

#### 5.1 核心发现
[3-5条，每条单独列出]

#### 5.2 理论贡献

#### 5.3 实践启示

---

### 六、研究局限与展望

#### 6.1 数据局限
#### 6.2 方法局限
#### 6.3 未来研究方向

---

### 附录

#### A. 主要信息来源
[按类型分类列出，标注可信度]

#### B. 可视化建议
- 社会网络图
- 政策偏好分布图
- 时间线
- 代际/阶层态度变迁图

## 格式要求
- 使用Markdown格式
- 标注所有引用来源
- 区分事实陈述与分析判断
- 在适当位置插入[数据待验证]标签
- 保持学术客观性，避免价值判断"""


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """调用DeepSeek API"""
    client = get_client()
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=8000,
            stream=True
        )

        # 流式输出
        full_response = ""
        placeholder = st.empty()
        for chunk in response:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)
        return full_response

    except Exception as e:
        st.error(f"API调用失败: {str(e)}")
        return ""


def run_research(topic: str):
    """执行调研流程"""

    # 步骤1：调研规划
    st.markdown("### 📋 步骤1：制定调研计划")
    with st.spinner("正在分析调研主题..."):
        plan = call_llm(PLANNER_PROMPT, f"调研主题：{topic}")

    if not plan:
        return

    st.markdown("---")

    # 步骤2：深度分析
    st.markdown("### 🔍 步骤2：社会政治深度分析")
    with st.spinner("正在进行深度分析..."):
        analysis = call_llm(ANALYST_PROMPT, f"调研主题：{topic}\n\n调研计划：{plan}")

    if not analysis:
        return

    st.markdown("---")

    # 步骤3：生成报告
    st.markdown("### 📝 步骤3：生成调研报告")
    with st.spinner("正在撰写报告..."):
        report = call_llm(WRITER_PROMPT, f"调研主题：{topic}\n\n调研计划：{plan}\n\n深度分析：{analysis}")

    if not report:
        return

    st.markdown("---")

    # 下载按钮
    st.markdown("### 📥 下载报告")
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="下载 Markdown 报告",
            data=report,
            file_name=f"调研报告_{topic}.md",
            mime="text/markdown"
        )

    with col2:
        # 转换为纯文本
        plain_text = report.replace("#", "").replace("*", "").replace("-", "•")
        st.download_button(
            label="下载 TXT 报告",
            data=plain_text,
            file_name=f"调研报告_{topic}.txt",
            mime="text/plain"
        )


def main():
    # 侧边栏
    with st.sidebar:
        st.markdown("## ⚙️ 设置")

        # API Key输入
        api_key = st.text_input(
            "DeepSeek API Key",
            type="password",
            help="请输入你的DeepSeek API Key"
        )
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key
            st.success("✅ API Key 已设置")

        st.markdown("---")

        # 使用说明
        st.markdown("""
        ## 📖 使用说明

        1. 输入DeepSeek API Key
        2. 输入调研主题
        3. 点击"开始调研"
        4. 等待分析完成
        5. 下载调研报告

        ## 💡 示例主题

        - 金正恩的国内政策决策与社会控制
        - 朝鲜的社会福利政策演变
        - 政治参与渠道与社会动员
        - 意识形态治理与社会稳定
        """)

        st.markdown("---")
        st.markdown("## ℹ️ 关于")
        st.markdown("""
        **社会政治调研助手**

        基于DeepSeek V4 Pro的学术调研智能体，
        专注于社会政治分析框架。
        """)

    # 主页面
    st.markdown('<p class="main-header">📊 社会政治调研助手</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">基于社会政治分析框架的学术调研智能体</p>', unsafe_allow_html=True)

    # 调研主题输入
    topic = st.text_area(
        "请输入调研主题",
        placeholder="例如：金正恩的国内政策决策与社会控制",
        height=100
    )

    # 高级选项
    with st.expander("🔧 高级选项"):
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("分析深度", ["标准分析", "深度分析", "快速概览"], index=0)
        with col2:
            st.selectbox("输出格式", ["完整报告", "执行摘要", "详细分析"], index=0)

    # 开始调研按钮
    if st.button("🚀 开始调研", type="primary", use_container_width=True):
        if not topic:
            st.warning("⚠️ 请输入调研主题")
            return

        if not os.getenv("DEEPSEEK_API_KEY"):
            st.warning("⚠️ 请先在左侧设置中输入DeepSeek API Key")
            return

        st.markdown("---")
        st.markdown(f"## 📚 调研主题：{topic}")
        st.markdown("---")

        # 执行调研
        run_research(topic)

    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>社会政治调研助手 v1.0 | 基于 DeepSeek V4 Pro</p>
        <p>专注于国内社会政治结构与过程分析</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
