import argparse
import json
import random
import re
import time
from pathlib import Path
from typing import Optional
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

START_URL = "https://qd.fang.lianjia.com/loupan/"
DISTRICTS = ["shinan", "shibei", "licang", "laoshan", "huangdao", "chengyang", "jimoqu", "jiaozhou", "pingdu", "laixi"]
OUTPUT_FILE = "lianjia_houses.json"


def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) ""AppleWebKit/537.36 (KHTML, like Gecko) ""Chrome/142.0.0.0 Safari/537.36")
    options.add_argument("--start-maximized")
    options.add_argument("--lang=zh-CN,zh")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN','zh']});
        """
    })

    time.sleep(0.6)
    return driver


def is_captcha_page(driver) -> bool:
    cur = driver.current_url.lower()
    if "captcha" in cur or "hip.lianjia.com" in cur:
        return True

    body = driver.find_element(By.TAG_NAME, "body").text
    if body and ("极验" in body or "请点击重试" in body or "拖动" in body or "人机验证" in body):
        return True
    return False


def wait_for_captcha_pass(driver, timeout: int = 300, poll: int = 3) -> bool:
    start = time.time()
    print(f"检测到验证码/风控页面：等待手动通过，最长 {timeout} 秒（每 {poll}s 检测一次）")
    while time.time() - start < timeout:
        time.sleep(poll)

        if not is_captcha_page(driver):
            if driver.find_elements(By.CSS_SELECTOR, "div.no-result-wrapper.hide"):
                print("验证已通过，检测到楼盘列表元素，可继续下一步")
                return True
        print(f"    等待中... {int(time.time() - start)}s elapsed", end="\r")

    print("\n等待验证码超时")
    return False


def is_logged_in(driver) -> bool:
    try:
        driver.find_element(By.CSS_SELECTOR, "a.user")
        return True
    except NoSuchElementException:
        return False


def extract_one_page(driver):
    time.sleep(random.uniform(1.2, 2.4))
    items = []

    elems = driver.find_elements(By.CSS_SELECTOR, "li.resblock-list")

    for e in elems:
        def get_text_safe(css):
            try:
                el = e.find_element(By.CSS_SELECTOR, css)
                return el.text.strip()
            except Exception:
                return ""

        name = get_text_safe("a.name ")
        stype = get_text_safe("span.resblock-type")
        status = get_text_safe("span.sale-status")
        avg_price = get_text_safe("span.number")

        if avg_price != "价格待定":
            total_price = re.findall(r"\d+\.?\d*", get_text_safe("div.second"))
            if len(total_price) == 2:
                min_total_price = total_price[0]
                max_total_price = total_price[1]
            elif len(total_price) == 1:
                min_total_price = total_price[0]
                max_total_price = total_price[0]
            else:
                min_total_price = ''
                max_total_price = ''
        else:
            avg_price = ''
            min_total_price = ''
            max_total_price = ''

        address = get_text_safe("div.resblock-location").split('/')
        district = address[0].strip()
        neighborhood = address[1].strip()
        detailed_address = address[2].strip()

        room = "".join(get_text_safe("a.resblock-room").split()).split('/')
        if len(room) == 0:
            room = ""
        else:
            room = ",".join(room)

        area = re.findall(r"\d+", get_text_safe("div.resblock-area"))
        if len(area) == 2:
            min_area = area[0]
            max_area = area[1]
        elif len(area) == 1:
            min_area = area[0]
            max_area = area[0]
        else:
            min_area = ''
            max_area = ''

        tags_div = e.find_element(By.CSS_SELECTOR, "div.resblock-tag")
        tag_spans = tags_div.find_elements(By.TAG_NAME, "span")
        tags = [tag_span.text for tag_span in tag_spans]
        tag = ",".join(tags)
        items.append({
            "name": name,
            "type": stype,
            "status": status,
            "avg_price": avg_price,
            "min_total_price": min_total_price,
            "max_total_price": max_total_price,
            "district": district,
            "neighborhood": neighborhood,
            "detailed_address": detailed_address,
            "room": room,
            "min_area": min_area,
            "max_area": max_area,
            "tag": tag,
            "url": driver.current_url
        })
    return items


def have_next_page(driver) -> bool:
    btn = driver.find_elements(By.CSS_SELECTOR, "a.next")
    if len(btn) > 0:
        return True
    else:
        return False


def go_next_page(driver) -> bool:
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "a.next")
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(random.uniform(1.0, 2.0))
        return True
    except NoSuchElementException:
        return False


def main():
    # 处理命令行参数
    parser = argparse.ArgumentParser()
    # 添加命令行参数
    parser.add_argument("--wait-after-login", type=int, default=60, help="登录时等待秒数")
    parser.add_argument("--captcha-timeout", type=int, default=300, help="遇到验证码时最长等待秒数")
    parser.add_argument("--output", default=OUTPUT_FILE, help="输出 JSON 文件名")
    # 解析命令行参数
    args = parser.parse_args()

    # 创建浏览器驱动
    driver = create_driver()
    try:
        print("打开目标页：", START_URL)
        # 使用浏览器驱动访问目标 URL
        driver.get(START_URL)
        # 随机等待 2~4 秒，模拟正常用户行为，避免被检测为机器人
        time.sleep(random.uniform(2.0, 4.0))

        # 若遇验证码页面，则等待验证通过
        if is_captcha_page(driver):
            ok = wait_for_captcha_pass(driver, timeout=args.captcha_timeout)
            if not ok:
                print("验证未通过，退出")
                return

        # 检测登录状态
        logged = is_logged_in(driver)
        print(f"初始登录状态：{logged}")
        if not logged:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "a.btn-login")
                if btn:
                    print("已尝试点击登录按钮，请在弹出的登录框中完成登录（如需验证码请完成）。")
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(0.3)
                    driver.execute_script("arguments[0].click();", btn)
            except NoSuchElementException:
                print("未能找到并点击登录按钮（将继续，但如果需要登录可能无法抓取全部数据）。")

            # 进入登录等待循环：每秒检测一次是否已登录
            max_wait = args.wait_after_login
            waited = 0
            logged_success = False
            while waited < max_wait:
                time.sleep(1)
                waited += 1

                # 若已检测到登录成功，提前跳出循环
                if is_logged_in(driver):
                    logged_success = True
                    print(f"\n检测到已登录（{waited}s）")
                    break

                # 登录过程中如果出现验证码页面，则等待手动通过验证
                if is_captcha_page(driver):
                    print("\n登录过程中出现验证码，等待手动通过...")
                    ok = wait_for_captcha_pass(driver, timeout=args.captcha_timeout)
                    if not ok:
                        print("登录过程中验证码未通过，继续等待或退出")

                # 每 5 秒输出一次等待提示
                if waited % 5 == 0:
                    print(f" 等待登录中...{waited}s elapsed", end="\r")

            if not logged_success:
                print("\n登录等待结束但未检测到登录成功（继续抓取但部分功能可能受限）")
        else:
            print("页面显示已登录，跳过登录点击")

        # 主抓取循环（页）
        all_results = []

        for district in DISTRICTS:
            driver.get(f"{START_URL}{district}/#{district}")

            if is_captcha_page(driver):
                ok = wait_for_captcha_pass(driver, timeout=args.captcha_timeout)
                if not ok:
                    print("验证未通过，停止抓取")
                    break

            try:
                max_page = int(driver.find_element(By.XPATH, "(//a[@data-page])[last()]").text)
                print(max_page)
            except NoSuchElementException:
                max_page = 1

            time.sleep(random.uniform(1.0, 2.5))
            for page in range(1, max_page + 1):
                print(f"\n=== 开始抓取第 {page} 页，当前 URL：{driver.current_url} ===")

                if is_captcha_page(driver):
                    ok = wait_for_captcha_pass(driver, timeout=args.captcha_timeout)
                    if not ok:
                        print("验证未通过，停止抓取")
                        break

                # 抓取当前页的所有数据
                page_items = extract_one_page(driver)
                print(f"抓取到 {len(page_items)} 条记录")

                # 将当前页数据追加到总结果中
                all_results.extend(page_items)

                # 尝试进入下一页，不成功则提前结束抓取
                success = go_next_page(driver)
                if not success:
                    print("未找到下一页或已到最后一页，停止")
                    break

                time.sleep(random.uniform(1.0, 2.5))

        output = Path(args.output)
        output.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n抓取完成，共 {len(all_results)} 条记录，已保存到 {args.output}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()