"""
TikTok Streak Bot logic (adapted for Discord bot)
"""

import json
import time
import logging
import os
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions

from config import (
    TIKTOK_MESSAGES_URL,
    STREAK_MESSAGE,
    COOKIES_FILE,
    CONTACTS_FILE,
    LOGS_DIR,
    HEADLESS_MODE,
    PAGE_LOAD_WAIT,
    ELEMENT_WAIT,
    MESSAGE_SEND_DELAY,
)

logger = logging.getLogger("streak_bot")


class TikTokStreakBot:
    def __init__(self, headless=None, test_mode=False, custom_message=None, progress_callback=None):
        self.page = None
        self.headless = HEADLESS_MODE if headless is None else headless
        self.test_mode = test_mode
        self.custom_message = custom_message
        self.target_usernames = []
        self.contacts_found = []
        self.progress_callback = progress_callback  # async callback for Discord progress

    async def _notify(self, message: str):
        if self.progress_callback:
            try:
                await self.progress_callback(message)
            except Exception:
                pass

    def load_target_contacts(self):
        if not os.path.exists(CONTACTS_FILE):
            logger.error(f"Contacts file not found: {CONTACTS_FILE}")
            return False
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.target_usernames = data.get("contacts", [])
            if not self.target_usernames:
                logger.warning("No contacts found")
                return False
            logger.info(f"Loaded {len(self.target_usernames)} contacts")
            return True
        except Exception as e:
            logger.error(f"Error loading contacts: {e}")
            return False

    def create_browser(self):
        try:
            options = ChromiumOptions()
            options.set_argument("--disable-blink-features=AutomationControlled")
            options.set_argument("--disable-infobars")
            options.set_argument("--disable-dev-shm-usage")
            options.set_argument("--no-sandbox")
            if self.headless:
                options.set_argument("--headless=new")
            options.set_user_agent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            self.page = ChromiumPage(options)
            logger.info("Browser initialized")
            return self.page
        except Exception as e:
            logger.error(f"Error creating browser: {e}")
            raise

    def load_cookies(self):
        if not os.path.exists(COOKIES_FILE):
            logger.error(f"Cookies file not found: {COOKIES_FILE}")
            return False
        try:
            with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            self.page.get("https://www.tiktok.com")
            time.sleep(2)
            for cookie in cookies:
                try:
                    self.page.set.cookies(cookie)
                except Exception:
                    pass
            logger.info(f"Loaded {len(cookies)} cookies")
            return True
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return False

    def verify_login(self):
        try:
            self.page.get(TIKTOK_MESSAGES_URL)
            time.sleep(PAGE_LOAD_WAIT)
            current_url = self.page.url
            if "login" in current_url:
                logger.error("Not logged in")
                return False
            if "messages" in current_url:
                logger.info("Login verified")
                # dismiss passkey popup if any
                try:
                    time.sleep(2)
                    modal = self.page.ele('css:div[class*="TUXModal"]', timeout=2) or \
                            self.page.ele('css:div[role="dialog"]', timeout=2)
                    if modal:
                        maybe_later = self.page.ele('xpath://button[contains(., "Maybe later")]', timeout=2)
                        if maybe_later:
                            maybe_later.click()
                            time.sleep(1)
                except Exception:
                    pass
                return True
            return False
        except Exception as e:
            logger.error(f"Login verify error: {e}")
            return False

    def find_target_contacts(self):
        self.contacts_found = []
        try:
            time.sleep(ELEMENT_WAIT + 2)
            for target in self.target_usernames:
                found = False
                # try multiple strategies
                selectors = [
                    f'xpath://*[contains(text(), "{target}")]',
                    f'xpath://*[text()="{target}"]',
                ]
                for sel in selectors:
                    try:
                        elems = self.page.eles(sel)
                        for elem in elems:
                            if elem and target.lower() in (elem.text or "").lower():
                                # climb to conversation item
                                parent = elem
                                for _ in range(6):
                                    try:
                                        parent = parent.parent()
                                        if parent and ("Item" in (parent.attr("class") or "") or 
                                                       "item" in (parent.attr("class") or "") or
                                                       "Container" in (parent.attr("class") or "")):
                                            self.contacts_found.append({
                                                "element": parent,
                                                "username": target,
                                            })
                                            logger.info(f"Found: {target}")
                                            found = True
                                            break
                                    except Exception:
                                        break
                                if found:
                                    break
                                # fallback use element itself
                                self.contacts_found.append({
                                    "element": elem,
                                    "username": target,
                                })
                                logger.info(f"Found (direct): {target}")
                                found = True
                                break
                    except Exception:
                        continue
                if not found:
                    logger.warning(f"Could not find: {target}")
            logger.info(f"Found {len(self.contacts_found)}/{len(self.target_usernames)} contacts")
            return self.contacts_found
        except Exception as e:
            logger.error(f"Error finding contacts: {e}")
            return []

    def send_message(self, contact):
        try:
            username = contact.get("username", "unknown")
            element = contact.get("element")
            if not element:
                return False

            element.click()
            time.sleep(1.5)

            # find input
            input_field = None
            input_selectors = [
                'css:div[contenteditable="true"]',
                'css:textarea',
                'css:div[data-e2e="message-input"]',
                'css:div[class*="DraftEditor"]',
            ]
            for sel in input_selectors:
                try:
                    input_field = self.page.ele(sel, timeout=2)
                    if input_field:
                        break
                except Exception:
                    continue

            if not input_field:
                logger.error(f"No input field for {username}")
                return False

            input_field.click()
            time.sleep(0.4)
            message = self.custom_message or STREAK_MESSAGE
            input_field.input(message)
            time.sleep(0.5)

            # send
            sent = False
            try:
                send_btn = self.page.ele('css:button[data-e2e="send-button"]', timeout=1) or \
                           self.page.ele('css:button[class*="send"]', timeout=1)
                if send_btn:
                    send_btn.click()
                    sent = True
            except Exception:
                pass

            if not sent:
                # press Enter
                try:
                    input_field.input("\n")
                    sent = True
                except Exception:
                    pass

            time.sleep(MESSAGE_SEND_DELAY)
            if sent:
                logger.info(f"Sent to {username}")
            return sent
        except Exception as e:
            logger.error(f"Send error for {contact.get('username')}: {e}")
            return False

    def send_all_messages(self):
        if not self.contacts_found:
            return 0, []
        success = []
        failed = []
        for contact in self.contacts_found:
            username = contact.get("username")
            if self.test_mode:
                success.append(username)
                continue
            if self.send_message(contact):
                success.append(username)
            else:
                failed.append(username)
            time.sleep(1)
        return success, failed

    async def run(self):
        """Main execution. Returns dict with results."""
        result = {
            "success": False,
            "total_contacts": 0,
            "found": 0,
            "sent": [],
            "failed": [],
            "error": None,
        }

        try:
            await self._notify("🚀 **Bắt đầu chạy bot...**\n⏳ Đang khởi tạo browser...")

            if not self.load_target_contacts():
                result["error"] = "Không tìm thấy contacts.json hoặc danh sách trống"
                await self._notify(f"❌ {result['error']}")
                return result

            result["total_contacts"] = len(self.target_usernames)
            await self._notify(f"📋 Đã load **{result['total_contacts']}** contacts")

            self.create_browser()
            await self._notify("🌐 Browser đã sẵn sàng\n🍪 Đang load cookies...")

            if not self.load_cookies():
                result["error"] = "Không load được cookies (file không tồn tại hoặc lỗi)"
                await self._notify(f"❌ {result['error']}")
                return result

            await self._notify("🔐 Đang xác minh đăng nhập TikTok...")
            if not self.verify_login():
                result["error"] = "Cookies hết hạn hoặc không đăng nhập được. Hãy cập nhật cookies."
                await self._notify(f"❌ {result['error']}")
                return result

            await self._notify("✅ Đăng nhập thành công\n🔍 Đang tìm contacts trong danh sách chat...")
            self.find_target_contacts()
            result["found"] = len(self.contacts_found)

            if not self.contacts_found:
                result["error"] = "Không tìm thấy contact nào trong danh sách chat"
                await self._notify(f"⚠️ {result['error']}")
                return result

            await self._notify(f"📨 Tìm thấy **{result['found']}** contacts → bắt đầu gửi tin...")

            sent, failed = self.send_all_messages()
            result["sent"] = sent
            result["failed"] = failed
            result["success"] = True

            # final report
            report = (
                f"✅ **Hoàn thành!**\n\n"
                f"📊 **Kết quả:** {len(sent)}/{result['found']} thành công\n"
            )
            if sent:
                report += "\n**Đã gửi:**\n" + "\n".join([f"• `{u}`" for u in sent])
            if failed:
                report += "\n\n**Thất bại:**\n" + "\n".join([f"• `{u}`" for u in failed])

            await self._notify(report)
            return result

        except Exception as e:
            result["error"] = str(e)
            await self._notify(f"❌ Lỗi nghiêm trọng: `{e}`")
            logger.exception("Bot run failed")
            return result
        finally:
            try:
                if self.page:
                    self.page.quit()
            except Exception:
                pass
