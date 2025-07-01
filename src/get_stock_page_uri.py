import asyncio
from playwright.async_api import async_playwright

async def get_stock_page_uri(stock_code):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  
        page = await browser.new_page()
        
        # Truy cập trang CafeF
        await page.goto("https://s.cafef.vn/")  
        
        await page.fill('#CafeF_SearchKeyword_Company', stock_code)
        
        # Click nút tìm kiếm
        await page.click('a.bt_search')
        print("✅ Đã click nút tìm kiếm")

        # Chờ kết quả hiện ra (hoặc URL thay đổi)
        try:
            await page.wait_for_load_state('load', timeout=5000)
            print("✅ Trang đã load lại hoặc cập nhật nội dung")
        except:
            print("⚠️ Không thấy trang load lại sau khi click")

        # Có thể in URL hiện tại để kiểm tra
        print("📍 URL hiện tại:", page.url)
        await browser.close()
        return str(page.url)

