#!/usr/bin/env python3
import argparse
import sys
from paper_manager import PaperManager
from image_manager import ImageManager
import warnings
warnings.filterwarnings("ignore")

def main():
    parser = argparse.ArgumentParser(description="本地多模态AI智能助手")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 添加论文
    add_paper_parser = subparsers.add_parser("add_paper", help="添加并分类论文")
    add_paper_parser.add_argument("path", help="PDF文件路径")
    add_paper_parser.add_argument("--topics", required=True, help="主题列表，逗号分隔")
    
    # 批量整理论文
    organize_parser = subparsers.add_parser("organize_papers", help="批量整理论文")
    organize_parser.add_argument("source_dir", help="源文件夹路径")
    organize_parser.add_argument("--topics", required=True, help="主题列表，逗号分隔")
    
    # 搜索论文
    search_paper_parser = subparsers.add_parser("search_paper", help="语义搜索论文")
    search_paper_parser.add_argument("query", help="搜索查询")
    search_paper_parser.add_argument("--top_k", type=int, default=5, help="返回结果数量")
    
    # 同步数据库
    sync_parser = subparsers.add_parser("sync_papers", help="同步数据库，删除不存在的论文记录")
    
    # 添加图像
    add_image_parser = subparsers.add_parser("add_image", help="添加图像到索引")
    add_image_parser.add_argument("path", help="图像文件路径")
    
    # 批量索引图像
    index_images_parser = subparsers.add_parser("index_images", help="批量索引图像")
    index_images_parser.add_argument("image_dir", help="图像文件夹路径")
    
    # 搜索图像
    search_image_parser = subparsers.add_parser("search_image", help="以文搜图")
    search_image_parser.add_argument("query", help="图像描述")
    search_image_parser.add_argument("--top_k", type=int, default=5, help="返回结果数量")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 论文相关命令
    if args.command in ["add_paper", "organize_papers", "search_paper", "sync_papers"]:
        pm = PaperManager()
        
        if args.command == "add_paper":
            topics = [t.strip() for t in args.topics.split(",")]
            result = pm.add_paper(args.path, topics)
            print(result)
        
        elif args.command == "organize_papers":
            topics = [t.strip() for t in args.topics.split(",")]
            results = pm.batch_organize(args.source_dir, topics)
            for result in results:
                print(result)
        
        elif args.command == "search_paper":
            papers = pm.search_papers(args.query, args.top_k)
            if papers:
                print(f"找到 {len(papers)} 篇相关论文:")
                for i, (path, score) in enumerate(papers, 1):
                    print(f"{i}. {path} (相似度: {score:.3f})")
            else:
                print("未找到相关论文")
        
        elif args.command == "sync_papers":
            result = pm.sync_database()
            print(f"数据库同步完成:")
            print(f"  总记录数: {result['total']}")
            print(f"  保留记录: {result['kept']}")
            print(f"  删除记录: {result['deleted']}")
            if result['deleted'] > 0:
                print(f"\n已删除的文件记录:")
                for path in result['deleted_files']:
                    print(f"  - {path}")
    
    # 图像相关命令
    elif args.command in ["add_image", "index_images", "search_image"]:
        im = ImageManager()
        
        if args.command == "add_image":
            result = im.add_image(args.path)
            print(result)
        
        elif args.command == "index_images":
            results = im.index_images(args.image_dir)
            for result in results:
                print(result)
        
        elif args.command == "search_image":
            images = im.search_images(args.query, args.top_k)
            if images:
                print(f"找到 {len(images)} 张相关图像:")
                for i, (path, score) in enumerate(images, 1):
                    print(f"{i}. {path} (相似度: {score:.3f})")
            else:
                print("未找到相关图像")


if __name__ == "__main__":
    main()

