from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    return webdriver.Chrome(options=options)

def wait_for_content_load(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'please wait')]"))
        )
    except:
        pass
    time.sleep(3)

def extract_project_details_from_current_page(driver):
    try:
        wait_for_content_load(driver)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        def clean_text(text):
            if not text:
                return 'Not Found'
            text = re.sub(r'please wait\.\.\.', '', text, flags=re.IGNORECASE)
            text = re.sub(r'No\s+\w+\s+Available', '', text, flags=re.IGNORECASE)
            text = ' '.join(text.split())
            return text.strip() if text.strip() else 'Not Found'

        def find_in_table_structure(label):
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        if label.lower() in cell_text.lower() and len(cell_text) < 50:
                            if i + 1 < len(cells):
                                value = cells[i + 1].get_text(strip=True)
                                if value and not any(skip in value.lower() for skip in ['please wait', 'loading', 'facility of']):
                                    return clean_text(value)
            return 'Not Found'

        def find_in_form_structure(label):
            label_element = soup.find(string=lambda text: text and label.lower() in text.lower() and len(text) < 50)
            if label_element:
                parent = label_element.parent
                input_field = parent.find_next('input')
                if input_field and input_field.get('value'):
                    return clean_text(input_field.get('value'))
                for sibling in parent.find_next_siblings():
                    text = sibling.get_text(strip=True)
                    if text and not any(skip in text.lower() for skip in ['please wait', 'loading', 'facility of']):
                        return clean_text(text)
            return 'Not Found'

        def get_field_value(label):
            value = find_in_table_structure(label)
            if value != 'Not Found':
                return value
            value = find_in_form_structure(label)
            if value != 'Not Found':
                return value
            return 'Not Found'

        rera_regd_no = get_field_value('Rera Regd. No')
        project_name = get_field_value('Project Name')

        try:
            promoter_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Promoter') or contains(@href, 'promoter')]")
            driver.execute_script("arguments[0].click();", promoter_tab)
            wait_for_content_load(driver)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
        except Exception as e:
            pass

        promoter_name = get_field_value('Company Name')
        if promoter_name == 'Not Found':
            promoter_name = get_field_value('Promoter Name')

        promoter_address = get_field_value('Registered Office Address')
        if promoter_address == 'Not Found':
            promoter_address = get_field_value('Office Address')

        gst_no = get_field_value('GST No')
        if gst_no == 'Not Found':
            gst_no = get_field_value('GSTIN')

        return {
            'Rera Regd. No': rera_regd_no,
            'Project Name': project_name,
            'Promoter Name': promoter_name,
            'Address of the Promoter': promoter_address,
            'GST No.': gst_no
        }

    except Exception as e:
        return None

def scrape_ongoing_projects():
    driver = setup_driver()
    try:
        driver.get('https://rera.odisha.gov.in/projects/project-list')
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'View Details')]"))
        )
        project_details = []
        for i in range(6):
            try:
                view_details_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'View Details')]")
                if i >= len(view_details_buttons):
                    break
                button = view_details_buttons[i]
                driver.execute_script("arguments[0].click();", button)
                time.sleep(5)
                details = extract_project_details_from_current_page(driver)
                if details:
                    project_details.append(details)
                driver.back()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'View Details')]"))
                )
                time.sleep(2)
            except Exception as e:
                try:
                    driver.get('https://rera.odisha.gov.in/projects/project-list')
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'View Details')]"))
                    )
                except:
                    pass
                continue
        return project_details
    except Exception as e:
        return None
    finally:
        driver.quit()
