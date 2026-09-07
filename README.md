# TikTok Streak Discord Bot

Bot Discord giúp tự động gửi tin giữ streak TikTok, quản lý hoàn toàn qua Discord.

> ⚠️ **Cảnh báo**: Automation gửi tin nhắn TikTok vi phạm Terms of Service. Có rủi ro tài khoản bị khóa. Dùng với trách nhiệm của bạn.

## Tính năng

- Quản lý cookies TikTok qua Discord (DM hoặc slash command)
- Thêm / xóa / xem danh sách contacts
- Chạy gửi tin giữ streak + báo cáo tiến độ realtime
- Chế độ test (chỉ tìm contacts, không gửi thật)
- Đổi message mặc định dễ dàng

**Lưu ý**: Bot **không** kiểm tra số ngày streak hay chỉ gửi người đang có streak (vì logic gốc không hỗ trợ).

## Cài đặt

### 1. Clone / tải code

```bash
cd tiktok-streak-discord-bot
```

### 2. Cài dependencies

```bash
pip install -r requirements.txt
```

### 3. Tạo Discord Bot

1. Vào https://discord.com/developers/applications
2. New Application → Bot → Reset Token → copy token
3. Bật **Message Content Intent** và **Direct Messages**
4. OAuth2 → URL Generator → scopes: `bot`, `applications.commands`
5. Permissions: Send Messages, Embed Links, Attach Files, Use Slash Commands
6. Mời bot vào server

### 4. Cấu hình

```bash
cp .env.example .env
```

Sửa `.env`:

```
DISCORD_TOKEN=token_của_bạn
```

### 5. Chạy bot

```bash
python bot.py
```

## Cách dùng

### Bước 1: Lấy cookies TikTok

1. Login TikTok trên Chrome/Firefox
2. Cài extension **Cookie-Editor** hoặc **EditThisCookie**
3. Export cookies dạng JSON
4. Gửi file `cookies.json` vào **DM** với bot  
   **hoặc** dùng lệnh `/set_cookies` rồi paste JSON

### Bước 2: Thêm contacts

```
/add_contact username1
/add_contact username2
```

### Bước 3: Chạy

```
/run_streak
```

hoặc tùy chỉnh message:

```
/run_streak message:Hey giữ streak nha 🔥
```

Chế độ test:

```
/test_streak
```

## Các lệnh

| Lệnh | Mô tả |
|------|-------|
| `/help` | Hướng dẫn |
| `/status` | Xem trạng thái |
| `/add_contact` | Thêm người |
| `/remove_contact` | Xóa người |
| `/list_contacts` | Xem danh sách |
| `/clear_contacts` | Xóa hết |
| `/set_cookies` | Cập nhật cookies (JSON) |
| `/set_message` | Đổi message mặc định |
| `/run_streak` | Chạy gửi tin |
| `/test_streak` | Chạy thử |

## Cấu trúc thư mục

```
tiktok-streak-discord-bot/
├── bot.py              # Discord bot chính
├── streak_bot.py       # Logic gửi tin TikTok
├── config.py
├── requirements.txt
├── .env.example
├── data/
│   ├── cookies.json    # (tự tạo)
│   └── contacts.json   # (tự tạo)
└── logs/
```

## Lưu ý kỹ thuật

- Cần máy chủ có **Chrome/Chromium** (DrissionPage dùng Chromium)
- Cookies TikTok thường hết hạn sau vài ngày → phải cập nhật
- Nên chạy bot trên VPS có đủ RAM (browser tốn tài nguyên)
- Headless mode mặc định bật

## Credits

Logic gốc lấy cảm hứng từ [dewhush/TikTok-Streak-API](https://github.com/dewhush/TikTok-Streak-API) (đã archive).

## License
Giấy phép Giấy phép GNU GENERAL PUBLIC LICENSE v3.0
