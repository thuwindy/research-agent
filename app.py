import streamlit as st
import json
import os
import requests
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
    /* 侧边栏加宽 */
    [data-testid="stSidebar"] {
        min-width: 320px !important;
        max-width: 320px !important;
    }
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
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    /* 调研计划格式化显示 */
    .plan-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 0.8rem;
        border-left: 4px solid #1E3A5F;
    }
    .plan-section h4 {
        margin-top: 0;
        color: #1E3A5F;
    }
    .plan-tag {
        display: inline-block;
        background: #1E3A5F;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        margin: 2px;
    }
    /* 执行摘要样式 */
    .exec-summary {
        background: linear-gradient(135deg, #f0f7ff 0%, #e6f0ff 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #b8d4fe;
        margin-bottom: 1rem;
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

# ==================== Tavily搜索 ====================

def tavily_search(query: str, search_depth: str = "advanced", max_results: int = 10) -> dict:
    """
    Tavily搜索API - 专为AI应用设计的搜索服务
    免费1000次/月，注册: https://tavily.com
    """
    api_key = st.secrets.get("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY", ""))

    if not api_key:
        st.warning("⚠️ Tavily API Key 未配置，跳过搜索")
        return {"results": [], "error": "未配置Tavily API Key"}

    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": search_depth,
        "include_answer": True,
        "include_raw_content": False,
        "max_results": max_results,
        "include_domains": [],
        "exclude_domains": []
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            st.error(f"❌ Tavily API 返回状态码: {response.status_code}")
            st.error(f"响应内容: {response.text[:500]}")
            return {"results": [], "error": f"API返回状态码: {response.status_code}"}
    except Exception as e:
        st.error(f"❌ Tavily 搜索失败: {str(e)}")
        return {"results": [], "error": str(e)}


def classify_source(url: str) -> str:
    """根据URL判断来源类型"""
    academic_domains = ["scholar.google", "arxiv.org", "researchgate.net", "academia.edu", "jstor.org", "springer.com", "sciencedirect.com", "wiley.com", "cnki.net", "wanfangdata.com.cn"]
    official_domains = [".gov", ".gov.cn", ".org.cn", "un.org", "worldbank.org", "imf.org"]
    thinktank_domains = ["brookings.edu", "rand.org", "cfr.org", "chathamhouse.org", "csis.org", "carnegieendowment.org", "rii", "cass"]

    url_lower = url.lower()

    for domain in academic_domains:
        if domain in url_lower:
            return "学术文献"

    for domain in official_domains:
        if domain in url_lower:
            return "官方文件"

    for domain in thinktank_domains:
        if domain in url_lower:
            return "智库报告"

    return "网络来源"


def assess_credibility(url: str, title: str) -> str:
    """评估来源可信度"""
    high_domains = [".gov", ".gov.cn", ".edu", ".ac.cn", "brookings", "rand.org", "cfr.org", "un.org", "worldbank"]
    medium_domains = ["reuters.com", "apnews.com", "bbc.com", "nytimes.com", "theguardian.com", "xinhuanet.com", "people.com.cn"]

    url_lower = url.lower()

    for domain in high_domains:
        if domain in url_lower:
            return "高"

    for domain in medium_domains:
        if domain in url_lower:
            return "中"

    return "待验证"


def multi_source_search(topic: str, search_queries: dict, search_depth: str = "standard") -> dict:
    """执行多源信息检索（使用Tavily）"""

    # 映射搜索深度
    depth = "advanced" if search_depth == "深度" else "basic"

    all_results = {
        "academic": [],
        "news": [],
        "official": [],
        "general": []
    }

    # 1. 学术文献检索
    st.markdown("📚 **检索学术文献...**")
    academic_queries = search_queries.get("academic", [topic])
    for query in academic_queries[:2]:
        result = tavily_search(
            query=f"{query} 学术研究 论文",
            search_depth=depth,
            max_results=5
        )
        for item in result.get("results", []):
            all_results["academic"].append({
                "type": "学术文献",
                "title": item.get("title", ""),
                "content": item.get("content", "")[:500],
                "url": item.get("url", ""),
                "score": item.get("score", 0),
                "credibility": assess_credibility(item.get("url", ""), item.get("title", ""))
            })

    # 2. 新闻报道检索
    st.markdown("📰 **检索新闻报道...**")
    news_queries = search_queries.get("news", [topic])
    for query in news_queries[:2]:
        result = tavily_search(
            query=f"{query} 新闻 最新报道",
            search_depth="basic",
            max_results=5
        )
        for item in result.get("results", []):
            all_results["news"].append({
                "type": "新闻报道",
                "title": item.get("title", ""),
                "content": item.get("content", "")[:500],
                "url": item.get("url", ""),
                "score": item.get("score", 0),
                "credibility": assess_credibility(item.get("url", ""), item.get("title", ""))
            })

    # 3. 官方文件/智库报告检索
    st.markdown("🏛️ **检索官方文件与智库报告...**")
    official_queries = search_queries.get("official", [topic]) + search_queries.get("thinktank", [])
    for query in official_queries[:2]:
        result = tavily_search(
            query=f"{query} 官方文件 政策 智库报告",
            search_depth=depth,
            max_results=5
        )
        for item in result.get("results", []):
            source_type = classify_source(item.get("url", ""))
            all_results["official"].append({
                "type": source_type,
                "title": item.get("title", ""),
                "content": item.get("content", "")[:500],
                "url": item.get("url", ""),
                "score": item.get("score", 0),
                "credibility": assess_credibility(item.get("url", ""), item.get("title", ""))
            })

    # 4. 综合检索
    st.markdown("🔍 **检索综合信息...**")
    result = tavily_search(
        query=f"{topic} 社会政治 分析 治理",
        search_depth=depth,
        max_results=8
    )
    for item in result.get("results", []):
        source_type = classify_source(item.get("url", ""))
        all_results["general"].append({
            "type": source_type,
            "title": item.get("title", ""),
            "content": item.get("content", "")[:500],
            "url": item.get("url", ""),
            "score": item.get("score", 0),
            "credibility": assess_credibility(item.get("url", ""), item.get("title", ""))
        })

    # 去重
    for key in all_results:
        seen_titles = set()
        unique_results = []
        for r in all_results[key]:
            title = r.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_results.append(r)
        all_results[key] = unique_results

    return all_results


def format_search_results(results: dict) -> str:
    """格式化搜索结果为文本"""
    output = []

    # 学术文献
    if results.get("academic"):
        output.append("## 📚 学术文献\n")
        for i, item in enumerate(results["academic"][:10], 1):
            output.append(f"{i}. **{item['title']}**")
            output.append(f"   - 类型: {item.get('type', '学术文献')}")
            if item.get('content'):
                output.append(f"   - 摘要: {item['content'][:200]}...")
            output.append(f"   - 来源: {item.get('url', '')}")
            output.append(f"   - 可信度: {item.get('credibility', '待评估')}")
            output.append("")

    # 新闻报道
    if results.get("news"):
        output.append("## 📰 新闻报道\n")
        for i, item in enumerate(results["news"][:10], 1):
            output.append(f"{i}. **{item['title']}**")
            output.append(f"   - 类型: {item.get('type', '新闻报道')}")
            if item.get('content'):
                output.append(f"   - 摘要: {item['content'][:200]}...")
            output.append(f"   - 来源: {item.get('url', '')}")
            output.append(f"   - 可信度: {item.get('credibility', '待评估')}")
            output.append("")

    # 官方文件/智库报告
    if results.get("official"):
        output.append("## 🏛️ 官方文件与智库报告\n")
        for i, item in enumerate(results["official"][:10], 1):
            output.append(f"{i}. **{item['title']}**")
            output.append(f"   - 类型: {item.get('type', '官方文件')}")
            if item.get('content'):
                output.append(f"   - 摘要: {item['content'][:200]}...")
            output.append(f"   - 来源: {item.get('url', '')}")
            output.append(f"   - 可信度: {item.get('credibility', '待评估')}")
            output.append("")

    # 综合来源
    if results.get("general"):
        output.append("## 🔍 综合信息\n")
        for i, item in enumerate(results["general"][:8], 1):
            output.append(f"{i}. **{item['title']}**")
            output.append(f"   - 类型: {item.get('type', '网络来源')}")
            if item.get('content'):
                output.append(f"   - 摘要: {item['content'][:200]}...")
            output.append(f"   - 来源: {item.get('url', '')}")
            output.append(f"   - 可信度: {item.get('credibility', '待评估')}")
            output.append("")

    return "\n".join(output)


# ==================== 提示词定义 ====================

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
  "search_queries": {
    "academic": ["学术搜索词1", "学术搜索词2"],
    "news": ["新闻搜索词1", "新闻搜索词2"],
    "official": ["官方文件搜索词1"],
    "thinktank": ["智库搜索词1"]
  },
  "analysis_focus": {
    "political": "政治维度关注点",
    "economic": "经济维度关注点",
    "social": "社会维度关注点",
    "historical": "历史维度关注点"
  }
}

只输出JSON，不要有其他内容。"""

VERIFIER_PROMPT = """你是一位严谨的社会政治信息分析师。请对收集到的多源信息进行整合与验证。

## 任务

### 1. 信息去重与分类
识别重复信息，保留最权威来源，按类型分类

### 2. 可信度评估
- 学术文献：期刊声誉、引用次数、研究方法
- 新闻报道：媒体信誉、是否多方印证
- 官方文件：发布机构权威性
- 智库报告：机构声誉、研究方法

### 3. 交叉验证
标注哪些信息有多源支持（至少2个独立来源）

### 4. 社会政治数据特别注意
- 注意不同社会阶层、族群、地域的数据代表性
- 避免精英偏差
- 标注社会期望偏差可能导致的数据失真

## 输出要求
请输出结构化的验证结果，包含：
1. 已验证的事实（按可信度排序）
2. 关键行动者及其角色
3. 数据缺口与局限性
4. 潜在偏差警告
5. 关键事件时间线"""

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

3. **社会维度**
   - 社会流动与阶层固化
   - 社会动员与集体行动
   - 意识形态治理与社会控制

4. **历史维度**
   - 社会政治变迁的长时段脉络
   - 政策周期与关键节点

### 分析方法
- **对比分析**：纵向时间对比、横向群体/地区对比
- **因果推理**：政策如何重塑社会结构
- **机制分析**：政策传导机制、社会政治反馈回路

## 伦理要求
- 客观中立，严格区分事实与研究者的分析判断
- 避免精英偏差，关注多元社会群体的声音
- 注明数据局限性"""

WRITER_PROMPT = """你是一位学术报告撰写专家。请将分析结果转化为结构化的调研报告。

## 报告撰写原则
- **学术规范**：严谨、客观、有据可查
- **社会政治本位**：突出社会政治逻辑，弱化国际关系叙事
- **循证呈现**：所有论点必须有数据或事实支撑
- **清晰结构**：层次分明，逻辑清晰

## 报告结构

> **执行摘要**（放在报告最顶部，用 > 引用块突出显示）
>
> **核心发现：** [1-2句话概括最重要的发现]
> **主要结论：** [2-3条要点，每条以 • 开头]
> **政策启示：** [1-2条启示]

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
#### 5.1 核心发现（3-5条，每条带编号，必须有来源支撑）
#### 5.2 理论贡献
#### 5.3 实践启示

---

### 六、研究局限与展望
#### 6.1 数据局限
#### 6.2 方法局限
#### 6.3 未来研究方向

---

### 附录
#### A. 主要信息来源（按类型分类，标注可信度）
#### B. 可视化建议
#### C. 术语表

## 格式要求
- 使用Markdown格式
- 执行摘要放在报告最顶部，使用 > 引用块格式，简明扼要（不超过300字）
- 标注所有引用来源
- 区分事实陈述与分析判断
- 保持学术客观性"""


def call_llm(system_prompt: str, user_prompt: str, stream: bool = True) -> str:
    """调用DeepSeek API"""
    api_key = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
    if not api_key:
        st.error("❌ DeepSeek API Key 未配置")
        return ""

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
        timeout=180.0
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000,
            stream=stream
        )

        if stream:
            full_response = ""
            placeholder = st.empty()
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            return full_response
        else:
            return response.choices[0].message.content

    except Exception as e:
        st.error(f"❌ API调用失败: {str(e)}")
        return ""


def run_research(topic: str, search_depth: str = "标准", analysis_type: str = "完整分析"):
    """执行完整调研流程"""

    # 步骤1：调研规划
    st.markdown("### 📋 步骤1：制定调研计划")
    plan = call_llm(PLANNER_PROMPT, f"调研主题：{topic}")

    if not plan:
        st.error("❌ 调研规划失败，请检查API配置")
        return

    # 解析调研计划
    try:
        json_str = plan
        if "```json" in plan:
            json_str = plan.split("```json")[1].split("```")[0]
        elif "```" in plan:
            json_str = plan.split("```")[1].split("```")[0]
        plan_data = json.loads(json_str.strip())
        search_queries = plan_data.get("search_queries", {})

        # 格式化显示调研计划
        with st.expander("📋 查看完整调研计划", expanded=True):
            st.markdown(f"""
            <div class="plan-section">
                <h4>📌 调研主题</h4>
                <p style="font-size:1.1rem;font-weight:bold;">{plan_data.get('research_topic', topic)}</p>
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
                <div class="plan-section">
                    <h4>⏰ 时间范围</h4>
                    <p>{plan_data.get('time_range', '未指定')}</p>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""
                <div class="plan-section">
                    <h4>🌍 地理范围</h4>
                    <p>{plan_data.get('geographic_scope', '未指定')}</p>
                </div>
                """, unsafe_allow_html=True)

            subs = plan_data.get('subtopics', [])
            if subs:
                st.markdown("**📑 子主题：**")
                tags_html = " ".join([f'<span class="plan-tag">{s}</span>' for s in subs])
                st.markdown(tags_html, unsafe_allow_html=True)

            questions = plan_data.get('research_questions', [])
            if questions:
                st.markdown("**❓ 核心研究问题：**")
                for q in questions:
                    st.markdown(f"- {q}")

            af = plan_data.get('analysis_focus', {})
            if af:
                st.markdown("**🔬 分析焦点：**")
                cols = st.columns(4)
                dims = [
                    ("政治维度", af.get('political', '')),
                    ("经济维度", af.get('economic', '')),
                    ("社会维度", af.get('social', '')),
                    ("历史维度", af.get('historical', ''))
                ]
                for i, (label, content) in enumerate(dims):
                    if content:
                        with cols[i]:
                            st.markdown(f"""
                            <div class="plan-section" style="text-align:center;">
                                <strong>{label}</strong>
                                <p style="font-size:0.9rem;margin-top:0.3rem;">{content[:80]}...</p>
                            </div>
                            """, unsafe_allow_html=True)

            sq = plan_data.get('search_queries', {})
            if sq:
                st.markdown("**🔍 搜索策略：**")
                scols = st.columns(4)
                sq_map = [
                    ("学术", "🎓", sq.get('academic', [])),
                    ("新闻", "📰", sq.get('news', [])),
                    ("官方", "🏛️", sq.get('official', [])),
                    ("智库", "🧠", sq.get('thinktank', []))
                ]
                for i, (label, icon, queries) in enumerate(sq_map):
                    if queries:
                        with scols[i]:
                            for q in queries[:3]:
                                st.caption(f"{icon} {q[:60]}")

    except Exception as e:
        st.warning(f"⚠️ 无法解析调研计划JSON，使用默认搜索词: {str(e)}")
        search_queries = {
            "academic": [topic],
            "news": [topic],
            "official": [topic],
            "thinktank": [topic]
        }

    st.markdown("---")

    # 步骤2：多源信息检索
    st.markdown("### 🔍 步骤2：多源信息检索")
    search_results = multi_source_search(topic, search_queries, search_depth)

    # 统计结果
    total_results = sum(len(v) for v in search_results.values())
    st.success(f"✅ 检索完成：共获取 {total_results} 条信息")

    # 显示检索统计
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("学术文献", len(search_results.get("academic", [])))
    with col2:
        st.metric("新闻报道", len(search_results.get("news", [])))
    with col3:
        st.metric("官方/智库", len(search_results.get("official", [])))
    with col4:
        st.metric("综合来源", len(search_results.get("general", [])))

    # 格式化搜索结果
    formatted_results = format_search_results(search_results)

    st.markdown("---")

    # 步骤3：信息整合与验证
    st.markdown("### ✅ 步骤3：信息整合与验证")
    verification = call_llm(
        VERIFIER_PROMPT,
        f"调研主题：{topic}\n\n调研计划：{plan}\n\n检索到的信息：\n{formatted_results}",
        stream=False
    )

    if not verification:
        st.warning("⚠️ 信息验证步骤失败，将使用原始搜索结果继续")
        verification = formatted_results

    st.markdown("---")

    # 步骤4：深度分析
    st.markdown("### 📊 步骤4：社会政治深度分析")

    # 根据分析类型调整提示词
    analyst_extra = ""
    if analysis_type == "快速概览":
        analyst_extra = "\n请做快速概览分析，控制在1000字以内，聚焦核心发现。"
    elif analysis_type == "专题分析":
        analyst_extra = "\n请做专题深度分析，选择2-3个最关键的子主题深入挖掘，每个子主题不少于500字的分析。"

    analysis = call_llm(
        ANALYST_PROMPT + analyst_extra,
        f"调研主题：{topic}\n\n调研计划：{plan}\n\n验证后的信息：{verification}"
    )

    if not analysis:
        st.error("❌ 深度分析失败")
        return

    st.markdown("---")

    # 步骤5：生成报告
    st.markdown("### 📝 步骤5：生成调研报告")

    # 根据分析类型调整报告
    writer_extra = ""
    if analysis_type == "快速概览":
        writer_extra = "\n请生成2000字以内的精简报告，聚焦执行摘要和核心发现。"
    elif analysis_type == "专题分析":
        writer_extra = "\n请生成详细的专题研究报告，每个分析维度的专题子项不少于800字分析。"

    report = call_llm(
        WRITER_PROMPT + writer_extra,
        f"调研主题：{topic}\n\n调研计划：{plan}\n\n验证后的信息：{verification}\n\n深度分析：{analysis}"
    )

    if not report:
        st.error("❌ 报告生成失败")
        return

    st.markdown("---")

    # 下载按钮
    st.markdown("### 📥 下载报告")
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="下载 Markdown 报告",
            data=report,
            file_name=f"调研报告_{topic[:20]}.md",
            mime="text/markdown"
        )

    with col2:
        plain_text = report.replace("#", "").replace("*", "").replace("-", "•")
        st.download_button(
            label="下载 TXT 报告",
            data=plain_text,
            file_name=f"调研报告_{topic[:20]}.txt",
            mime="text/plain"
        )

    # 显示信息来源摘要
    st.markdown("---")
    with st.expander("📚 查看所有检索到的信息来源"):
        st.markdown(formatted_results)


def main():
    # 侧边栏
    with st.sidebar:
        st.markdown("## 📖 使用说明")

        st.markdown("""
        ### 操作步骤

        1. 输入调研主题
        2. 点击"开始调研"
        3. 等待2-5分钟
        4. 下载调研报告

        ### 调研流程

        - 📋 制定调研计划
        - 🔍 多源信息检索
        - ✅ 信息整合验证
        - 📊 社会政治分析
        - 📝 生成调研报告
        """)

        st.markdown("---")

        st.markdown("## 💡 示例主题")
        st.markdown("""
        - 金正恩的国内政策决策与社会控制
        - 朝鲜的社会福利政策演变
        - 政治参与渠道与社会动员
        - 意识形态治理与社会稳定
        """)

        st.markdown("---")

        st.markdown("## 🔧 技术说明")
        st.markdown("""
        - AI模型：DeepSeek V4 Pro
        - 搜索引擎：Tavily
        - 分析框架：社会政治分析
        """)

        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #999; font-size: 0.8rem;'>
            社会政治调研助手 v2.0<br>
            专注于国内社会政治结构与过程分析
        </div>
        """, unsafe_allow_html=True)

    # 主页面
    st.markdown('<p class="main-header">📊 社会政治调研助手</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">基于社会政治分析框架的学术调研智能体 | 集成多源信息检索与验证</p>', unsafe_allow_html=True)

    # 功能介绍
    st.markdown("""
    <div style='background-color: #f0f7ff; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
        <strong>核心功能：</strong>
        多源信息检索 → 交叉验证 → 社会政治深度分析 → 结构化报告生成
    </div>
    """, unsafe_allow_html=True)

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
            search_depth = st.selectbox("搜索深度", ["标准", "深度"], index=0,
                                       help="深度搜索会获取更多结果，但耗时更长")
        with col2:
            analysis_type = st.selectbox("分析类型", ["完整分析", "快速概览", "专题分析"], index=0)

    # 开始调研按钮
    if st.button("🚀 开始调研", type="primary", use_container_width=True):
        if not topic:
            st.warning("⚠️ 请输入调研主题")
            return

        # API Key检查
        deepseek_key = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
        tavily_key = st.secrets.get("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY", ""))

        if not deepseek_key:
            st.error("❌ DeepSeek API Key 未配置，请联系管理员")
            return

        if not tavily_key:
            st.error("❌ Tavily API Key 未配置，请联系管理员")
            return

        st.markdown("---")
        st.markdown(f"## 📚 调研主题：{topic}")
        st.markdown("---")

        run_research(topic, search_depth, analysis_type)

    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p><strong>社会政治调研助手 v2.0</strong></p>
        <p>集成 Semantic Scholar · News · 政府文件 · 智库报告 多源检索</p>
        <p>专注于国内社会政治结构与过程分析</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
