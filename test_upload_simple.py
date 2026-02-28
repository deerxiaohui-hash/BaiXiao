#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'backend')

from pathlib import Path
from app.services.document_processor import document_processor

# 测试文档处理
test_file = Path("企业员工管理制度.docx")

if not test_file.exists():
    print(f"❌ 文件不存在: {test_file}")
    sys.exit(1)

print(f"✅ 文件存在: {test_file}")
print(f"文件大小: {test_file.stat().st_size / 1024:.2f} KB")

# 读取文件内容
with open(test_file, 'rb') as f:
    content = f.read()

# 验证文件
is_valid, message = document_processor.validate_file(test_file.name, len(content))
print(f"文件验证: {message}")

if not is_valid:
    print("❌ 文件验证失败")
    sys.exit(1)

# 保存文件
try:
    saved_path = document_processor.save_uploaded_file(content, test_file.name)
    print(f"✅ 文件保存成功: {saved_path}")
except Exception as e:
    print(f"❌ 文件保存失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 处理文档
try:
    print("开始处理文档...")
    document_id, chunks = document_processor.process_document(saved_path, test_file.name)
    print(f"✅ 文档处理成功!")
    print(f"  - 文档ID: {document_id}")
    print(f"  - 分块数量: {len(chunks)}")
    print(f"  - 第一块内容预览: {chunks[0].page_content[:100]}...")
except Exception as e:
    print(f"❌ 文档处理失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试向量存储
print("开始向量化存储...")
from app.services.vector_store import vector_store
try:
    print(f"向量存储对象: {vector_store}")
    print(f"Collection: {vector_store.collection}")
    vector_store.add_documents(chunks, document_id, test_file.name, len(content))
    print(f"✅ 向量化存储成功!")
except Exception as e:
    print(f"❌ 向量化存储失败: {e}")
    print(f"错误类型: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n🎉 所有测试通过!")
