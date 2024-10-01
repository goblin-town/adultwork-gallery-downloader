import os
import logging
import pickle
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager
import enlighten

# Configure logging
logging.basicConfig(level=logging.INFO)

# Paths
DOWNLOAD_PATH = "downloads"
COOKIE_FILE = "cookies.pkl"

# Xpaths
PROFILE_NAME = "/html/body/table/tbody/tr/td/div[2]/center/table[1]/tbody/tr/td/table/tbody/tr[1]/td[1]/span"
LOGINOUT_SELECTOR = "/html/body/div[1]/div[3]/ul/li[2]/a"
ADULT_WARNING_SELECTOR = "/html/body/div[5]/div/div/div/center/table/tbody/tr[6]/td[1]/a"
PRIVATE_GALLERY_BUTTON = "/html/body/div[4]/div/ul/li[3]/a"
FIRST_IMAGE = "/html/body/table/tbody/tr/td/div/center/table/tbody/tr[2]/td/div/div/center/form/table/tbody/tr[2]/td[1]/table/tbody/tr[1]/td/table/tbody/tr/td/a/img"
FULL_SIZE = "/html/body/form/table[1]/tbody/tr/td[2]/nobr/input[1]"
PIC_TITLE = "/html/body/form/p[1]/b"
PIC_TOTAL = "/html/body/table/tbody/tr/td/div/center/table/tbody/tr[2]/td/div/div/center/form/table/tbody/tr[1]/td/table/tbody/tr/td[2]"
LARGE_PIC_TOTAL = "/html/body/table/tbody/tr/td/div[2]/center/table[2]/tbody/tr[2]/td/div[2]/center/form/div/center/table/tbody/tr[2]/td/div[1]/table/tbody/tr[1]/td"

def initialize_driver(headless=False):
    options = FirefoxOptions()
    if headless:
        options.add_argument("--headless")
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
    return driver

def load_cookies(driver, filepath):
    if os.path.exists(filepath):
        logging.info("Loading cookies from file")
        cookies = pickle.load(open(filepath, "rb"))
        driver.get("https://www.adultwork.com/Home.asp")
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.get("https://www.adultwork.com/Home.asp")
        return True
    return False

def save_cookies(driver, filepath):
    logging.info("Saving cookies")
    with open(filepath, "wb") as file:
        pickle.dump(driver.get_cookies(), file)

def login(driver):
    driver.get("https://www.adultwork.com/Login.asp")
    WebDriverWait(driver, 120).until(EC.element_to_be_clickable((By.XPATH, ADULT_WARNING_SELECTOR))).click()
    WebDriverWait(driver, 120).until(EC.text_to_be_present_in_element((By.XPATH, LOGINOUT_SELECTOR), "Logout"))
    logging.info("Login successful")

def download_images(driver, profile_name, num_pics):
    folder_path = os.path.join(DOWNLOAD_PATH, profile_name)
    os.makedirs(folder_path, exist_ok=True)
    manager = enlighten.get_manager()
    pbar = manager.counter(total=int(num_pics), desc='Progress', unit='pics')

    full_size = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, FULL_SIZE)))
    full_size.click()

    while True:
        file_name = "".join([c for c in driver.find_element(By.XPATH, PIC_TITLE).text if re.match(r'\w', c)])
        file_path = os.path.join(folder_path, f"{file_name}.png")

        if os.path.exists(file_path):
            logging.info(f'Already exists: {file_path}')
        else:
            with open(file_path, 'wb') as file:
                logging.info(f"Saving {file_path}")
                file.write(driver.find_element(By.NAME, 'TheImage').screenshot_as_png)

        pbar.update()  # Update progress bar after processing each image

        if len(driver.find_elements(By.NAME, 'btnNext')) == 0:
            pbar.update()
            break
        driver.find_element(By.NAME, 'btnNext').click()

def main():
    profile_number = input("AW Profile Number: ")
    profile_url = f"https://www.adultwork.com/ViewProfile.asp?UserID={profile_number}"
    private_gallery_url = f"https://www.adultwork.com/XXXGallery.asp?UserID={profile_number}"

    driver = initialize_driver()

    if not load_cookies(driver, COOKIE_FILE):
        logging.info("No valid cookies found. Please log in.")
        login(driver)
        save_cookies(driver, COOKIE_FILE)

    driver.quit()

    # Re-initialize driver for the main task
    driver = initialize_driver(headless=True)
    load_cookies(driver, COOKIE_FILE)
    driver.get(profile_url)

    # Extract profile name
    profile_name = driver.find_element(By.XPATH, PROFILE_NAME).text

    # Navigate to private gallery
    driver.get(private_gallery_url)
    num_pics = driver.find_element(By.XPATH, PIC_TOTAL).text.split(" pictures")[0]
    driver.find_element(By.XPATH, FIRST_IMAGE).click()

    # Handle pop-up window
    main_window = driver.current_window_handle
    for handle in driver.window_handles:
        if handle != main_window:
            popup = handle
            driver.switch_to.window(popup)

    download_images(driver, profile_name, num_pics)

    driver.quit()

if __name__ == "__main__":
    main()