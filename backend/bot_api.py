import os
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from twocaptcha import TwoCaptcha  # This import will work with 2captcha-python
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class VoterInfoBot:
    def __init__(self):
        self.driver = None
        self.wait = None
        # Use the correct package name
        self.solver = TwoCaptcha(os.getenv('TWO_CAPTCHA_API_KEY', '6a618c70ab1c170d5ee4706d077cfbda'))
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver for Railway deployment"""
        try:
            logger.info("🛠️ Setting up Chrome driver for Railway...")
            
            chrome_options = Options()
            
            # Railway-specific Chrome options
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Additional options for stability
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-software-rasterizer")
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Use webdriver-manager for automatic driver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 25)
            
            logger.info("✅ Chrome driver setup successful")
            
        except Exception as e:
            logger.error(f"❌ Chrome driver setup failed: {e}")
            raise

    # [Keep all the other methods the same as before]
    def run_bot(self, id_number):
        """Main function to run the bot and extract voter information"""
        try:
            logger.info(f"🚀 Starting Voter Information Bot for ID: {id_number}")
            
            steps = [
                ("🌐 Navigating to IEC website", self.navigate_to_site),
                ("🔢 Entering ID number", lambda: self.enter_id_number(id_number)),
                ("🔍 Finding reCAPTCHA", self.find_recaptcha_elements),
                ("🔄 Solving reCAPTCHA", self.solve_recaptcha_v2),
                ("📤 Submitting form", self.submit_form),
                ("⏳ Waiting for results", self.wait_for_results_page),
                ("📊 Extracting information", self.extract_voter_information)
            ]
            
            for step_name, step_func in steps:
                logger.info(step_name)
                result = step_func()
                if not result:
                    logger.error(f"❌ Failed at: {step_name}")
                    return None
                time.sleep(2)  # Brief pause between steps
            
            voter_data = self.extract_voter_information()
            return voter_data
            
        except Exception as e:
            logger.error(f"❌ Bot execution failed: {e}")
            return None
    
    def navigate_to_site(self):
        try:
            self.driver.get("https://www.elections.org.za/pw/Voter/Voter-Information")
            time.sleep(5)
            
            if "Voter Information" in self.driver.title or "Voter Information" in self.driver.page_source:
                logger.info("✅ IEC website loaded successfully")
                return True
            else:
                logger.warning("⚠️ IEC website may not have loaded correctly")
                return True
                
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return False
    
    def enter_id_number(self, id_number):
        try:
            logger.info("Looking for ID input field...")
            time.sleep(2)
            
            id_selectors = [
                "#MainContent_uxIDNumberTextBox",
                "input[name='ctl00$MainContent$uxIDNumberTextBox']",
                "input[type='tel']",
                "input[placeholder*='ID number']",
                "input[maxlength='13']"
            ]
            
            id_input = None
            for selector in id_selectors:
                try:
                    id_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"✅ Found ID input using: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not id_input:
                logger.error("❌ Could not find ID input field")
                return False
            
            logger.info(f"Entering ID number: {id_number}")
            id_input.clear()
            id_input.send_keys(id_number)
            
            entered_value = id_input.get_attribute('value')
            if entered_value == id_number:
                logger.info("✅ ID number entered successfully")
                return True
            else:
                logger.error(f"❌ ID number entry failed. Expected: {id_number}, Got: {entered_value}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error entering ID: {e}")
            return False
    
    def find_recaptcha_elements(self):
        try:
            logger.info("Looking for reCAPTCHA...")
            
            recaptcha_selectors = [
                "iframe[src*='google.com/recaptcha']",
                "iframe[src*='recaptcha']",
                ".g-recaptcha",
                "#g-recaptcha",
                "div[class*='recaptcha']",
                "iframe[title*='recaptcha']"
            ]
            
            for selector in recaptcha_selectors:
                try:
                    recaptcha_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"✅ Found reCAPTCHA element using: {selector}")
                    return recaptcha_element
                except NoSuchElementException:
                    continue
            
            logger.error("❌ Could not find reCAPTCHA elements")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error finding reCAPTCHA: {e}")
            return None
    
    def get_recaptcha_site_key(self):
        try:
            logger.info("Extracting reCAPTCHA site key...")
            
            # Method 1: Look for site key in iframe src
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute('src') or ''
                if 'recaptcha' in src:
                    if 'k=' in src:
                        import urllib.parse as urlparse
                        parsed = urlparse.urlparse(src)
                        params = urlparse.parse_qs(parsed.query)
                        if 'k' in params:
                            site_key = params['k'][0]
                            logger.info(f"✅ Found reCAPTCHA site key: {site_key}")
                            return site_key
            
            # Method 2: Look for data-sitekey attribute
            sitekey_selectors = [
                "div[data-sitekey]",
                ".g-recaptcha[data-sitekey]",
                "*[data-sitekey]"
            ]
            
            for selector in sitekey_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        site_key = element.get_attribute('data-sitekey')
                        if site_key and len(site_key) > 10:
                            logger.info(f"✅ Found reCAPTCHA site key: {site_key}")
                            return site_key
                except NoSuchElementException:
                    continue
            
            # Method 3: Search in page source
            page_source = self.driver.page_source
            import re
            sitekey_patterns = [
                r'data-sitekey="([^"]+)"',
                r'sitekey[\'"]?\s*[:=]\s*[\'"]([^\'"]+)[\'"]',
                r'recaptcha.*?[\'"]([a-zA-Z0-9_-]{40})[\'"]'
            ]
            
            for pattern in sitekey_patterns:
                matches = re.search(pattern, page_source)
                if matches:
                    site_key = matches.group(1)
                    logger.info(f"✅ Found reCAPTCHA site key: {site_key}")
                    return site_key
            
            logger.error("❌ Could not find reCAPTCHA site key")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting site key: {e}")
            return None
    
    def solve_recaptcha_v2(self):
        try:
            logger.info("Starting reCAPTCHA v2 solving...")
            
            site_key = self.get_recaptcha_site_key()
            if not site_key:
                logger.error("No reCAPTCHA site key found")
                return False
            
            page_url = self.driver.current_url
            
            logger.info(f"Solving reCAPTCHA v2 - Site Key: {site_key}, URL: {page_url}")
            
            try:
                logger.info("Sending to 2Captcha service (this may take 10-30 seconds)...")
                result = self.solver.recaptcha(
                    sitekey=site_key,
                    url=page_url,
                    version='v2'
                )
                
                recaptcha_token = result['code']
                logger.info("✅ reCAPTCHA solved successfully")
                
                script = """
                var selectors = [
                    '#g-recaptcha-response',
                    '[name="g-recaptcha-response"]',
                    'textarea[name="g-recaptcha-response"]',
                    '.g-recaptcha-response'
                ];
                
                for (var i = 0; i < selectors.length; i++) {
                    var element = document.querySelector(selectors[i]);
                    if (element) {
                        element.style.display = '';
                        element.innerHTML = arguments[0];
                        element.value = arguments[0];
                        
                        var event = new Event('change', { bubbles: true });
                        element.dispatchEvent(event);
                    }
                }
                return true;
                """
                
                success = self.driver.execute_script(script, recaptcha_token)
                if success:
                    logger.info("✅ reCAPTCHA token injected successfully")
                    time.sleep(2)
                    return True
                else:
                    logger.error("❌ Failed to inject reCAPTCHA token")
                    return False
                
            except Exception as e:
                logger.error(f"2Captcha reCAPTCHA solving error: {e}")
                return False
            
        except Exception as e:
            logger.error(f"reCAPTCHA solving failed: {e}")
            return False
    
    def submit_form(self):
        try:
            logger.info("Looking for submit button...")
            
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "input[value*='Submit']",
                "input[value*='submit']",
                "input[value*='Search']",
                "input[value*='search']",
                "button[onclick*='submit']",
                "#MainContent_uxSubmitButton",
                "#MainContent_btnSubmit",
                "input[id*='Submit']",
                "button[id*='Submit']",
                "button[class*='btn-primary']",
                "input[class*='btn-primary']",
                "input[onclick*='submit']"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"✅ Found submit button using: {selector}")
                    
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
                    time.sleep(1)
                    
                    try:
                        submit_button.click()
                        logger.info("✅ Form submitted using regular click")
                    except:
                        self.driver.execute_script("arguments[0].click();", submit_button)
                        logger.info("✅ Form submitted using JavaScript click")
                    
                    time.sleep(3)
                    return True
                except NoSuchElementException:
                    continue
            
            logger.error("❌ Could not find submit button")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error submitting form: {e}")
            return False
    
    def wait_for_results_page(self):
        try:
            logger.info("Waiting for results page to load...")
            time.sleep(5)
            
            results_indicators = [
                (By.ID, "MainContent_uxIDNumberDataField"),
                (By.ID, "MainContent_uxWardDataField"), 
                (By.ID, "MainContent_uxVDDataField"),
                (By.XPATH, "//div[contains(@class, 'form-row')]"),
                (By.XPATH, "//label[contains(@id, 'DataField')]")
            ]
            
            for by, selector in results_indicators:
                try:
                    element = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    logger.info(f"✅ Results page indicator found: {selector}")
                    return True
                except TimeoutException:
                    continue
            
            current_url = self.driver.current_url
            if "My-ID-Information-Details" in current_url:
                logger.info("✅ On results page (URL confirmed)")
                return True
            else:
                logger.warning(f"Current URL: {current_url}")
                
            logger.error("❌ Results page not detected")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error waiting for results page: {e}")
            return False
    
    def extract_voter_information(self):
        try:
            logger.info("Extracting voter information...")
            
            voter_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'identity_number': 'Not found',
                'full_name': 'Not found',
                'ward': 'Not found', 
                'voting_district': 'Not found',
                'ward_number': 'Not found',
                'municipality': 'Not found',
                'province': 'Not found'
            }
            
            # Extract Identity Number
            try:
                id_element = self.driver.find_element(By.ID, "MainContent_uxIDNumberDataField")
                voter_data['identity_number'] = id_element.text.strip()
                logger.info(f"✅ Identity Number: {voter_data['identity_number']}")
            except NoSuchElementException:
                logger.warning("Identity Number field not found")
            
            # Extract Ward Information
            try:
                ward_element = self.driver.find_element(By.ID, "MainContent_uxWardDataField")
                ward_text = ward_element.text.strip()
                voter_data['ward'] = ward_text
                logger.info(f"✅ Ward: {voter_data['ward']}")
                
                # Parse ward details
                if ',' in ward_text:
                    parts = [part.strip() for part in ward_text.split(',')]
                    if len(parts) >= 1:
                        voter_data['ward_number'] = parts[0]
                    if len(parts) >= 2:
                        voter_data['municipality'] = parts[1]
                    if len(parts) >= 3:
                        voter_data['province'] = parts[2]
                        
            except NoSuchElementException:
                logger.warning("Ward field not found")
            
            # Extract Voting District
            try:
                vd_element = self.driver.find_element(By.ID, "MainContent_uxVDDataField")
                voter_data['voting_district'] = vd_element.text.strip()
                logger.info(f"✅ Voting District: {voter_data['voting_district']}")
            except NoSuchElementException:
                logger.warning("Voting District field not found")
            
            return voter_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting voter information: {e}")
            return {}
    
    def close(self):
        """Close the browser"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("🔒 Browser closed.")
        except Exception as e:
            logger.warning(f"⚠️ Error closing browser: {e}")

@app.route('/verify-voter', methods=['POST'])
def verify_voter():
    """API endpoint to verify voter information"""
    start_time = time.time()
    bot = None
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        id_number = data.get('id_number')
        
        if not id_number:
            return jsonify({'error': 'ID number is required'}), 400
        
        if len(id_number) != 13 or not id_number.isdigit():
            return jsonify({'error': 'Invalid ID number format. Must be 13 digits.'}), 400
        
        # Create and run bot
        bot = VoterInfoBot()
        
        # Run the bot
        results = bot.run_bot(id_number)
        end_time = time.time()
        processing_time = f"{end_time - start_time:.2f} seconds"
        
        if results:
            results['processing_time'] = processing_time
            results['status'] = 'success'
            logger.info(f"✅ Verification completed in {processing_time}")
            return jsonify(results)
        else:
            return jsonify({
                'status': 'error',
                'error': 'Failed to extract voter information from IEC website'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ API error: {e}")
        return jsonify({
            'status': 'error',
            'error': f'Internal server error: {str(e)}'
        }), 500
        
    finally:
        if bot:
            bot.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'service': 'Voter Verification API',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API information"""
    return jsonify({
        'message': 'ConnectVote IEC Verification API',
        'version': '1.0.0',
        'endpoints': {
            'POST /verify-voter': 'Verify voter information with IEC',
            'GET /health': 'Health check'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting Voter Verification API on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
