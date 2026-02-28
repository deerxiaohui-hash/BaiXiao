from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from app.config import settings
from app.services.vector_store_simple import vector_store
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
            template="""你是一个企业内部知识库助手。请根据以下企业制度文档内容回答问题。

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
            content = doc.page_content
            context_parts.append(f"[文档{i}] 来源: {source}\n{content}")
        return "\n\n".join(context_parts)
    
    def _format_sources(self, documents: List[tuple]) -> List[SourceReference]:
        sources = []
        for doc, distance in documents:
            # distance 已经是距离值（越小越相似），需要转换为相似度（越大越相似）
            # similarity = 1 - distance，然后转换为百分比
            similarity = max(0.0, 1.0 - distance)  # 确保不为负数
            relevance_score = round(similarity, 3)
            
            source = SourceReference(
                content=doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                source=doc.metadata.get("filename", "未知来源"),
                page=doc.metadata.get("page"),
                chunk_index=doc.metadata.get("chunk_index"),  # 添加片段序号
                relevance_score=relevance_score
            )
            sources.append(source)
        return sources
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        documents_with_scores = vector_store.similarity_search_with_score(question, k=5)
        
        if not documents_with_scores:
            return {
                "answer": "抱歉，知识库中暂时没有相关文档。请先上传企业制度文档后再进行提问。",
                "sources": []
            }
        
        documents = [doc for doc, _ in documents_with_scores]
        context = self._build_context(documents)
        
        prompt = self.prompt_template.format(context=context, question=question)
        
        try:
            response = self.llm.invoke(prompt)
            answer = response.content
        except Exception as e:
            answer = f"生成答案时出现错误: {str(e)}"
        
        sources = self._format_sources(documents_with_scores)
        
        return {
            "answer": answer,
            "sources": sources
        }


rag_service = RAGService()
