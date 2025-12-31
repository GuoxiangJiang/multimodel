import os
import shutil
from pathlib import Path
from typing import List, Tuple
import chromadb
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
import warnings
warnings.filterwarnings("ignore")

class PaperManager:
    def __init__(self, data_dir="./data/papers"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(self.data_dir / "chroma_db"))
        self.collection = self.client.get_or_create_collection(
            name="papers",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF提取文本"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages[:5]:  # 只读前5页用于分类
                text += page.extract_text()
            return text[:50000]  # 限制长度
        except:
            return ""
    
    def classify_paper(self, text: str, topics: List[str]) -> str:
        """根据文本内容分类论文"""
        if not text:
            return topics[0] if topics else "未分类"
        
        text_embedding = self.model.encode(text)
        topic_embeddings = self.model.encode(topics)
        
        similarities = []
        for topic_emb in topic_embeddings:
            sim = (text_embedding @ topic_emb) / (
                (text_embedding @ text_embedding) ** 0.5 * (topic_emb @ topic_emb) ** 0.5
            )
            similarities.append(sim)
        
        max_idx = similarities.index(max(similarities))
        return topics[max_idx]
    
    def add_paper(self, pdf_path: str, topics: List[str]) -> str:
        """添加并分类单个论文"""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return f"错误: 文件不存在 {pdf_path}"
        
        text = self.extract_text_from_pdf(str(pdf_path))
        category = self.classify_paper(text, topics)
        
        target_dir = self.data_dir / category
        target_dir.mkdir(exist_ok=True)
        target_path = target_dir / pdf_path.name
        
        shutil.copy2(pdf_path, target_path)
        
        embedding = self.model.encode(text).tolist()
        self.collection.upsert(
            embeddings=[embedding],
            documents=[text],
            metadatas=[{"path": str(target_path), "category": category}],
            ids=[str(target_path)]
        )
        
        return f"已添加: {pdf_path.name} -> {category}"
    
    def batch_organize(self, source_dir: str, topics: List[str]):
        """批量整理论文"""
        source_dir = Path(source_dir)
        pdf_files = list(source_dir.glob("*.pdf"))
        
        results = []
        for pdf_file in pdf_files:
            result = self.add_paper(str(pdf_file), topics)
            results.append(result)
        
        return results
    
    def search_papers(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """语义搜索论文"""
        query_embedding = self.model.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count())
        )
        
        papers = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if 'distances' in results else 0
                papers.append((metadata['path'], 1 - distance))
        
        return papers
    
    def sync_database(self) -> dict:
        """同步数据库，删除文件系统中不存在的论文记录"""
        all_data = self.collection.get()
        
        if not all_data['ids']:
            return {"total": 0, "deleted": 0, "kept": 0}
        
        deleted_ids = []
        deleted_paths = []
        
        for i, doc_id in enumerate(all_data['ids']):
            metadata = all_data['metadatas'][i]
            file_path = Path(metadata['path'])
            
            if not file_path.exists():
                deleted_ids.append(doc_id)
                deleted_paths.append(str(file_path))
        
        if deleted_ids:
            self.collection.delete(ids=deleted_ids)
        
        return {
            "total": len(all_data['ids']),
            "deleted": len(deleted_ids),
            "kept": len(all_data['ids']) - len(deleted_ids),
            "deleted_files": deleted_paths
        }

