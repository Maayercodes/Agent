import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Dict
import time
import random
from loguru import logger
from ..database.models import Daycare, Region

class DaycareScraper:
    def __init__(self, session, headless: bool = True):
        self.session = session
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        options.add_argument("--window-size=1920,1080")
        
        # Let undetected_chromedriver automatically find the matching version
        driver = uc.Chrome(options=options, use_subprocess=True)
        return driver

    def _random_delay(self, min_delay=1.0, max_delay=3.0):
        time.sleep(random.uniform(min_delay, max_delay))

    def scrape_google_maps(self, query: str, city: str, max_results: int = 20) -> List[Dict]:
        logger.info(f"Scraping Google Maps for {query} in {city}")
        results = []
        self.driver = self._init_driver()
        
        try:
            # Build search URL
            search_query = f"{query}+in+{city}".replace(' ', '+')
            url = f"https://www.google.com/maps/search/{search_query}"
            logger.info(f"Loading URL: {url}")
            
            self.driver.get(url)
            self._random_delay(3, 5)

            # Wait for results to load
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='article'], div.Nv2PK, div.section-result"))
                )
            except TimeoutException:
                logger.error("Initial results didn't load")
                self.driver.save_screenshot("google_maps_error.png")
                return results

            # Scroll and collect results
            scroll_attempts = 0
            while len(results) < max_results and scroll_attempts < 3:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self._random_delay(2, 3)
                
                items = self.driver.find_elements(By.CSS_SELECTOR, "div[role='article'], div.Nv2PK, div.section-result")
                for item in items:
                    if len(results) >= max_results:
                        break
                        
                    try:
                        name = item.find_element(By.CSS_SELECTOR, "div.fontHeadlineSmall, h3.section-result-title, div.qBF1Pd").text
                        address = item.find_element(By.CSS_SELECTOR, "div.fontBodyMedium > div:nth-child(1), div.section-result-location").text
                        
                        try:
                            phone = item.find_element(By.CSS_SELECTOR, "div.fontBodyMedium > div:nth-child(2) > span:nth-child(2), button.section-result-phone").text
                        except NoSuchElementException:
                            phone = "Not available"
                        
                        results.append({
                            'name': name,
                            'address': address,
                            'phone': phone
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error parsing listing: {str(e)}")
                        continue
                
                scroll_attempts += 1

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            self.driver.save_screenshot("google_maps_crash.png")
        finally:
            if self.driver:
                self.driver.quit()
                
        return results[:max_results]

    def save_to_db(self, daycares: List[Dict], region: str = 'USA'):
        try:
            count = 0
            for daycare_data in daycares:
                daycare = Daycare(
                    name=daycare_data['name'],
                    address=daycare_data['address'],
                    phone=daycare_data['phone'],
                    region=Region.USA if region.lower() == 'usa' else Region.FRANCE,
                    source='google_maps'
                )
                self.session.add(daycare)
                count += 1
            
            self.session.commit()
            logger.success(f"Successfully saved {count} daycares to database")
            return count
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving to database: {str(e)}")
            return 0