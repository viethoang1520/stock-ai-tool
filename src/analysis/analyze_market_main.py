import os
import sys
# Ensure parent directory is in sys.path for module resolution
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import json
from typing import List, Dict
import asyncio
import re
import datetime
from crawlers.crawl_cafebiz_news import extract_cafebiz_news
from analysis.analyze_market import market_agent, MarketAnalysisOutput
from db_utils.pg_services import save_market_analysis_to_db, upload_audio_directory
from db_utils.pg_pool import init_db_pool

def create_market_audio_directory_and_save(url: str, text: str):
    """
    Tạo thư mục theo format market_analysis_{source}_{date_time} và lưu file audio
    
    Args:
        url: URL nguồn tin (để tạo tên file)
        text: Nội dung phân tích để chuyển thành audio
    
    Returns:
        dict: Thông tin về thư mục và file đã tạo
    """
    # Tạo thư mục theo format market_analysis_source_date_time
    now = datetime.datetime.now()
    date_str = now.strftime('%Y%m%d')
    time_str = now.strftime('%H%M%S')
    
    # Tạo tên source từ URL
    source_name = os.path.basename(url).replace('.', '_').replace('-', '_')[:20]  # Giới hạn độ dài
    if not source_name:
        source_name = "unknown"
    
    audio_directory = f'output/audios/market_analysis_{source_name}_{date_str}_{time_str}'
    os.makedirs(audio_directory, exist_ok=True)
    
    # Tạo file audio
    audio_filename = f'market_analysis_{source_name}.mp3'
    audio_path = os.path.join(audio_directory, audio_filename)
    
    # Làm sạch text và tạo audio
    clean_text = re.sub(r'[\*\/_#\-]+', ' ', text)
    
    from gtts import gTTS
    tts = gTTS(clean_text, lang='vi')
    tts.save(audio_path)
    
    return {
        'directory': audio_directory,
        'file_path': audio_path,
        'filename': audio_filename,
        'source': source_name,
        'url': url,
        'date': date_str,
        'time': time_str,
        'full_timestamp': now.strftime('%Y%m%d_%H%M%S')
    }

async def main(secret_key: str = "your-secret-key-here", upload_to_server: bool = True):
    await init_db_pool()
    
    # 1. Crawl dữ liệu
    print("🔍 Đang crawl dữ liệu tin tức...")
    crawl_results = await extract_cafebiz_news()
    
    analysis_results = []
    
    for item in crawl_results:
        url = item.get('url')
        if not item.get('success'):
            print(f"❌ Failed to crawl {url}: {item.get('error_message')}")
            continue
            
        print(f"\n📰 Đang phân tích tin tức từ: {url}")
        
        news = item.get('news', [])
        titles = '\n'.join([n.get('title', '') for n in news if n.get('title')])
        prompt = f"Các tiêu đề tin tức từ {url} về thị trường chứng khoán:\n{titles}\n\nHãy phân tích toàn thị trường như một chuyên gia."
        
        # 2. Gọi agent
        result = await market_agent.run(prompt)
        print(f"✅ Phân tích hoàn thành cho {url}")
        print(f"📊 Analysis:\n{result.output.analysis}\n{'-'*40}")
        
        # 3. Lưu audio vào thư mục riêng theo format market_analysis_{source}_{date_time}
        audio_info = create_market_audio_directory_and_save(
            url=url,
            text=result.output.analysis
        )
        
        print(f"✅ Audio đã được lưu:")
        print(f"📂 Thư mục: {audio_info['directory']}")
        print(f"🎵 File: {audio_info['file_path']}")

        # 4. Lưu thông tin vào database
        await save_market_analysis_to_db(result.output)
        print(f"💾 Đã lưu vào database")
        
        # 5. Upload podcast lên server (nếu được yêu cầu)
        upload_result = None
        if upload_to_server:
            print(f"\n🚀 Đang upload podcast lên server...")
            
            # Kiểm tra secret key trước
            if not secret_key or secret_key == "your-secret-key-here":
                print(f"❌ Secret key không hợp lệ: {secret_key}")
                upload_result = {
                    'success': False,
                    'error': 'Secret key is missing or invalid'
                }
            else:
                print(f"🔑 Secret key: {secret_key[:10]}...")  # Chỉ hiển thị 10 ký tự đầu
                print(f"📁 Directory path: {audio_info['directory']}")
                print(f"📄 File exists: {os.path.exists(audio_info['file_path'])}")
                
                try:
                    upload_result = await upload_audio_directory(
                        directory_path=audio_info['directory'],
                        secret_key=secret_key
                    )
                    
                    print(f"📊 Upload result: {upload_result}")  # Log toàn bộ response
                    
                    if upload_result['success']:
                        print(f"✅ Upload podcast thành công!")
                        print(f"📡 Server response: {upload_result['uploaded_file']['title']}")
                    else:
                        print(f"❌ Upload podcast thất bại:")
                        print(f"   └─ Error: {upload_result.get('error', 'Unknown error')}")
                        print(f"   └─ Status code: {upload_result.get('status_code', 'N/A')}")
                        
                        # Nếu có thêm thông tin chi tiết
                        if 'uploaded_file' in upload_result and upload_result['uploaded_file'] is None:
                            print(f"   └─ File upload failed: No file was uploaded")
                        
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"❌ Exception khi upload podcast:")
                    print(f"   └─ Error: {str(e)}")
                    print(f"   └─ Traceback: {error_details}")
                    
                    upload_result = {
                        'success': False,
                        'error': str(e),
                        'traceback': error_details
                    }
        
        # 6. Lưu kết quả từng analysis
        analysis_results.append({
            'url': url,
            'source': audio_info['source'],
            'audio_directory': audio_info['directory'],
            'audio_file': audio_info['file_path'],
            'audio_filename': audio_info['filename'],
            'date': audio_info['date'],
            'time': audio_info['time'],
            'full_timestamp': audio_info['full_timestamp'],
            'analysis_result': result.output,
            'upload_result': upload_result
        })
        
        print(f"{'='*60}")
    
    return analysis_results

if __name__ == "__main__":
    # Cấu hình
    SECRET_KEY = os.getenv("CLOUDINARY_SECRET_KEY")  # Kiểm tra env variable
    UPLOAD_TO_SERVER = True
    
    # Debug thông tin environment
    print(f"🔍 Debug info:")
    print(f"   └─ SECRET_KEY from env: {SECRET_KEY[:10] + '...' if SECRET_KEY else 'None'}")
    print(f"   └─ UPLOAD_TO_SERVER: {UPLOAD_TO_SERVER}")
    print(f"   └─ Current working directory: {os.getcwd()}")
    
    # Chạy phân tích và upload
    results = asyncio.run(main(
        secret_key=SECRET_KEY,
        upload_to_server=UPLOAD_TO_SERVER
    ))
    
    print(f"\n🎯 Tổng kết phân tích thị trường:")
    print(f"📊 Tổng số phân tích: {len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"\n📈 Phân tích #{i}:")
        print(f"   └─ Nguồn: {result['url']}")
        print(f"   └─ Thư mục audio: {result['audio_directory']}")
        print(f"   └─ File audio: {result['audio_filename']}")
        print(f"   └─ Timestamp: {result['full_timestamp']}")
        
        # Hiển thị kết quả upload
        if result['upload_result']:
            if result['upload_result']['success']:
                print(f"   └─ Upload: ✅ Thành công")
                print(f"   └─ Title: {result['upload_result']['uploaded_file']['title']}")
                print(f"   └─ Tags: {', '.join(result['upload_result']['uploaded_file']['tags'])}")
            else:
                print(f"   └─ Upload: ❌ Thất bại")
                print(f"      └─ Error: {result['upload_result'].get('error', 'Unknown error')}")
                print(f"      └─ Status code: {result['upload_result'].get('status_code', 'N/A')}")
        else:
            print(f"   └─ Upload: ⏭️ Bỏ qua")
    
    # Thống kê upload
    successful_uploads = sum(1 for r in results if r['upload_result'] and r['upload_result']['success'])
    failed_uploads = sum(1 for r in results if r['upload_result'] and not r['upload_result']['success'])
    skipped_uploads = sum(1 for r in results if not r['upload_result'])
    
    print(f"\n📊 Thống kê upload:")
    print(f"   └─ ✅ Thành công: {successful_uploads}")
    print(f"   └─ ❌ Thất bại: {failed_uploads}")
    print(f"   └─ ⏭️ Bỏ qua: {skipped_uploads}")
