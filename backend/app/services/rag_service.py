from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from app.config import settings
from app.services.vector_store import vector_store
from app.models.schemas import SourceReference


class RAGService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.LONGCAT_API_KEY,
            base_url=settings.LONGCAT_BASE_URL,
            model=settings.LONGCAT_MODEL,
            temperature=0.3
        )

        self.prompt_template = PromptTemplate(
            template="""你是"百晓"，一个企业内部知识库助手。请根据以下企业制度文档内容回答问题。

要求：
1. 只使用提供的文档内容回答问题，不要编造信息
2. 如果文档中没有相关信息，请明确告知用户
3. 回答要准确、简洁、专业
4. 如果涉及具体数字或规定，请准确引用

文档内容：
{context}

问题：{question}

请给出答案：""",
            input_variables=["context", "question"]
        )

    def _build_context(self, documents: List[Document]) -> str:
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("filename", "未知来源")
            section = doc.metadata.get("section")
            location = f"（{section}）" if section else ""
            context_parts.append(f"[文档{i}] 来源: {source}{location}\n{doc.page_content}")
        return "\n\n".join(context_parts)

    def _format_sources(self, results: List[tuple]) -> List[SourceReference]:
        sources = []
        for doc, similarity in results:
            # search() 已返回相似度（0~1，越大越相关），不再做距离换算
            source = SourceReference(
                content=doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                source=doc.metadata.get("filename", "未知来源"),
                page=doc.metadata.get("page"),
                chunk_index=doc.metadata.get("chunk_index"),
                section=doc.metadata.get("section"),
                relevance_score=round(similarity, 3),
            )
            sources.append(source)
        return sources

    def answer_question(self, question: str) -> Dict[str, Any]:
        results = vector_store.search(question, k=settings.RETRIEVAL_TOP_K)

        if not results:
            return {
                "answer": "抱歉，知识库中没有找到与问题相关的内容。请尝试换个问法，或确认相关制度文档已上传。",
                "sources": []
            }

        context = self._build_context([doc for doc, _ in results])
        prompt = self.prompt_template.format(context=context, question=question)

        try:
            response = self.llm.invoke(prompt)
            answer = response.content
        except Exception as e:
            answer = f"生成答案时出现错误: {str(e)}"

        return {
            "answer": answer,
            "sources": self._format_sources(results)
        }


rag_service = RAGService()
