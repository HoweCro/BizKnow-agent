from datetime import date, timedelta

from langchain.agents import create_agent
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama

from app.config import EMBEDDING_MODEL_NAME, VECTORSTORE_DIR


def format_docs(docs) -> str:
    """将检索到的文档格式化为带来源和页码的上下文。"""
    if not docs:
        return "知识库中没有找到相关内容。"

    lines = []
    for index, doc in enumerate(docs, 1):
        if isinstance(doc, Document):
            source = doc.metadata.get("source", "未知文件")
            page = doc.metadata.get("page")
            page_label = f"，第 {page + 1} 页" if isinstance(page, int) else ""
            content = doc.page_content
        else:
            source = "未知文件"
            page_label = ""
            content = str(doc)
        lines.append(f"[{index}] {content}（来源：{source}{page_label}）")
    return "\n\n".join(lines)


def load_rag_chain():
    """创建可按需调用知识检索和工作日计算工具的本地 Agent。"""
    if not VECTORSTORE_DIR.exists():
        raise RuntimeError("Vectorstore not found. Please run ingest.py first.")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vectorstore = FAISS.load_local(
        folder_path=str(VECTORSTORE_DIR),
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    @tool
    def search_company_policies(query: str) -> str:
        """检索公司制度、流程、产品手册和员工常见问题。需要基于公司资料回答时调用此工具。"""
        return format_docs(retriever.invoke(query))

    @tool
    def calculate_workdays(start_date: str, end_date: str) -> str:
        """计算两个日期之间（含起止日期）的工作日数量；周六和周日不计入，法定节假日不扣除。日期格式必须为 YYYY-MM-DD。"""
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        except ValueError:
            return "日期格式无效，请使用 YYYY-MM-DD。"
        if end < start:
            return "结束日期不能早于开始日期。"
        if (end - start).days > 3660:
            return "日期区间不能超过 10 年。"

        workdays = 0
        current = start
        while current <= end:
            if current.weekday() < 5:
                workdays += 1
            current += timedelta(days=1)
        return f"{start.isoformat()} 至 {end.isoformat()}（含起止日期）共有 {workdays} 个工作日；此计算未扣除法定节假日。"

    model = ChatOllama(
        model="qwen2.5:0.5b",
        temperature=0,
        num_ctx=4096,
        num_predict=384,
        client_kwargs={"timeout": 90.0},
    )

    return create_agent(
        model=model,
        tools=[search_company_policies, calculate_workdays],
        system_prompt=(
            "你是公司内部知识助手。需要回答公司制度、流程或产品资料时，必须先调用 search_company_policies，"
            "并且只根据检索结果回答；没有找到依据时，明确说明知识库中没有相关信息。"
            "涉及日期区间的工作日数量时，调用 calculate_workdays，并说明该结果未扣除法定节假日。"
            "必要时可以调用多个工具。回答简洁、礼貌，并在制度类回答中注明检索结果给出的文件名和页码。"
        ),
    )
