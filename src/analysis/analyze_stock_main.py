import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.get_stock_info import extract_symbol_info
from db_utils.pg_services import save_support_output_to_db, upload_audio_directory
from analysis.analyze_stock import stock_agent, SupportDependencies, DataCrawl
import datetime
import re
from db_utils.pg_pool import init_db_pool

def create_audio_directory_and_save(symbol: str, text: str):
    """
    Tạo thư mục theo format {symbol_date_time} và lưu file audio
    
    Args:
        symbol: Mã cổ phiếu (VD: FPT, VNM)
        text: Nội dung phân tích để chuyển thành audio
    
    Returns:
        dict: Thông tin về thư mục và file đã tạo
    """
    # Tạo thư mục theo format symbol_date_time
    now = datetime.datetime.now()
    date_str = now.strftime('%Y%m%d')
    time_str = now.strftime('%H%M%S')
    audio_directory = f'output/audios/{symbol}_{date_str}_{time_str}'
    os.makedirs(audio_directory, exist_ok=True)
    
    # Tạo file audio
    audio_filename = f'{symbol}_analysis.mp3'
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
        'symbol': symbol,
        'date': date_str,
        'time': time_str,
        'full_timestamp': now.strftime('%Y%m%d_%H%M%S')
    }

async def main(symbol: str, secret_key: str = "your-secret-key-here", upload_to_server: bool = True):
    await init_db_pool()
    
    # 1. Lấy thông tin chứng khoán
    stock_data = await extract_symbol_info(symbol)
    print(f"Dữ liệu cổ phiếu {symbol}: {stock_data}")

    # 2. Phân tích dữ liệu (truyền data đã crawl)
    deps = SupportDependencies(stock_data=DataCrawl(stock_data))
    result = await stock_agent.run(f'Phân tích xu hướng cổ phiếu {symbol} bằng tiếng Việt', deps=deps)
    print(f"Kết quả phân tích: {result.output}")

    # 3. Lưu audio vào thư mục riêng theo format {symbol_date_time}
    audio_info = create_audio_directory_and_save(
        symbol=symbol,
        text=str(result.output.analysis_advice)
    )
    
    print(f"✅ Audio đã được lưu:")
    print(f"📂 Thư mục: {audio_info['directory']}")
    print(f"🎵 File: {audio_info['file_path']}")

    # 4. Lưu kết quả phân tích vào database
    await save_support_output_to_db(result.output)
    
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
    
    # 6. Return thông tin thư mục và file
    return {
        'audio_directory': audio_info['directory'],
        'audio_file': audio_info['file_path'],
        'audio_filename': audio_info['filename'],
        'symbol': symbol,
        'date': audio_info['date'],
        'time': audio_info['time'],
        'full_timestamp': audio_info['full_timestamp'],
        'analysis_result': result.output,
        'upload_result': upload_result
    }

if __name__ == "__main__":
    # Cấu hình
    SYMBOL = "FPT"
    SECRET_KEY = os.getenv("CLOUDINARY_SECRET_KEY")  # Kiểm tra env variable
    UPLOAD_TO_SERVER = True
    
    # Debug thông tin environment
    print(f"🔍 Debug info:")
    print(f"   └─ SECRET_KEY from env: {SECRET_KEY[:10] + '...' if SECRET_KEY else 'None'}")
    print(f"   └─ UPLOAD_TO_SERVER: {UPLOAD_TO_SERVER}")
    print(f"   └─ Current working directory: {os.getcwd()}")
    
    # Chạy phân tích và upload
    result = asyncio.run(main(
        symbol=SYMBOL, 
        secret_key=SECRET_KEY,
        upload_to_server=UPLOAD_TO_SERVER
    ))
    
    print(f"\n🎯 Kết quả cuối cùng:")
    print(f"📁 Thư mục audio: {result['audio_directory']}")
    print(f"🎵 File audio: {result['audio_file']}")
    print(f"📊 Symbol: {result['symbol']}")
    print(f"📅 Ngày: {result['date']}")
    print(f"⏰ Thời gian: {result['time']}")
    print(f"🕐 Timestamp đầy đủ: {result['full_timestamp']}")
    
    # Hiển thị kết quả upload với thông tin chi tiết
    if result['upload_result']:
        if result['upload_result']['success']:
            print(f"🌐 Upload: ✅ Thành công")
            print(f"📡 Title: {result['upload_result']['uploaded_file']['title']}")
            print(f"🏷️ Tags: {', '.join(result['upload_result']['uploaded_file']['tags'])}")
        else:
            print(f"🌐 Upload: ❌ Thất bại")
            print(f"   └─ Error: {result['upload_result'].get('error', 'Unknown error')}")
            print(f"   └─ Status code: {result['upload_result'].get('status_code', 'N/A')}")
            
            # Nếu có traceback, hiển thị thêm
            if 'traceback' in result['upload_result']:
                print(f"   └─ Full traceback:")
                print(f"      {result['upload_result']['traceback']}")
    else:
        print(f"🌐 Upload: ⏭️ Bỏ qua")
