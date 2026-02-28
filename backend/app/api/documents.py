from fastapi import APIRouter, HTTPException

from app.models.schemas import DocumentsResponse, DocumentInfo, DeleteResponse
from app.services.vector_store_simple import vector_store

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents", response_model=DocumentsResponse)
async def get_documents():
    documents = vector_store.get_all_documents()
    
    document_infos = [
        DocumentInfo(
            id=doc["id"],
            filename=doc["filename"],
            upload_time=doc["upload_time"],
            chunks_count=doc["chunks_count"],
            file_size=doc["file_size"]
        )
        for doc in documents
    ]
    
    return DocumentsResponse(documents=document_infos)


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(document_id: str):
    success = vector_store.delete_document(document_id)
    
    if success:
        return DeleteResponse(
            success=True,
            message="文档删除成功"
        )
    else:
        raise HTTPException(status_code=404, detail="文档不存在")
