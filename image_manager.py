import os
from pathlib import Path
from typing import List, Tuple
import chromadb
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import warnings
warnings.filterwarnings("ignore")

class ImageManager:
    def __init__(self, data_dir="./data/images"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(self.data_dir / "chroma_db"))
        self.collection = self.client.get_or_create_collection(
            name="images",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    def add_image(self, image_path: str):
        """添加图像到索引"""
        image_path = Path(image_path)
        if not image_path.exists():
            return f"错误: 图像不存在 {image_path}"
        
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                image_embedding = image_features.cpu().numpy()[0].tolist()
            
            self.collection.upsert(
                embeddings=[image_embedding],
                documents=[str(image_path)],
                metadatas=[{"path": str(image_path)}],
                ids=[str(image_path)]
            )
            
            return f"已添加图像: {image_path.name}"
        except Exception as e:
            return f"错误: {str(e)}"
    
    def index_images(self, image_dir: str):
        """批量索引图像文件夹"""
        image_dir = Path(image_dir)
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        
        results = []
        for ext in image_extensions:
            for img_path in image_dir.glob(f"*{ext}"):
                result = self.add_image(str(img_path))
                results.append(result)
        
        return results
    
    def search_images(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """通过文本描述搜索图像"""
        inputs = self.processor(text=[query], return_tensors="pt", padding=True).to(self.device)
        
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
            text_embedding = text_features.cpu().numpy()[0].tolist()
        
        results = self.collection.query(
            query_embeddings=[text_embedding],
            n_results=min(top_k, self.collection.count())
        )
        
        images = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if 'distances' in results else 0
                images.append((metadata['path'], 1 - distance))
        
        return images

