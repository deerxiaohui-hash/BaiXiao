from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path

from app.models.schemas import UploadResponse
from app.services.document_processor import document_processor
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    print(f"[DEBUG] 收到上传请求: {file.filename}")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    file_content = await file.read()
    file_size = len(file_content)
    print(f"[DEBUG] 文件大小: {file_size} bytes")
    
    is_valid, message = document_processor.validate_file(file.filename, file_size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    try:
        print(f"[DEBUG] 开始保存文件")
        file_path = document_processor.save_uploaded_file(file_content, file.filename)
        print(f"[DEBUG] 文件已保存: {file_path}")
        
        print(f"[DEBUG] 开始处理文档")
        document_id, chunks = document_processor.process_document(file_path, file.filename)
        print(f"[DEBUG] 文档处理完成, ID: {document_id}, 分块数: {len(chunks)}")
        
        print(f"[DEBUG] 开始向量化存储")
        vector_store.add_documents(chunks, document_id, file.filename, file_size, stored_file=file_path.name)
        print(f"[DEBUG] 向量化存储完成")
        
        return UploadResponse(
            success=True,
            document_id=document_id,
            filename=file.filename,
            chunks_count=len(chunks),
            message="文档上传成功"
        )
        
    except ValueError as e:
        print(f"[ERROR] ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理文档时出错: {str(e)}")
