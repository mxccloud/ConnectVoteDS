from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from twocaptcha import TwoCaptcha

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class VoterInfoBot:
    def __init__(self):
        self.setup_driver()
        self.wait = WebDriverWait(self.driver, 20)
        self.solver = TwoCaptcha("6a618c70ab1c170d5ee4706d077cfbda")
        
    def setup_driver(self):
        try:
            print("🛠️ Setting up Chrome driver...")
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Chrome driver setup successful")
            
        except WebDriverException as e:
            print(f"❌ Chrome driver setup failed: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error during driver setup: {e}")
            raise
    
    def run_bot(self, id_number):
        """Main function to run the bot and extract voter information"""
        try:
            print("🚀 Starting Voter Information Bot...")
            print(f"🔢 Processing ID: {id_number}")
            
            # Step 1: Navigate
            if not self.navigate_to_site():
                return None
                
            # Step 2: Enter ID
            if not self.enter_id_number(id_number):
                return None
                
            # Step 3: Solve reCAPTCHA
            recaptcha_element = self.find_recaptcha_elements()
            if not recaptcha_element:
                return None
            
            if not self.solve_recaptcha_v2():
                return None
                
            # Step 4: Submit form
            if not self.submit_form():
                return None
            
            # Step 5: Wait for results
            if not self.wait_for_results_page():
                return None
                
            # Step 6: Extract data
            voter_data = self.extract_voter_information()
            
            return voter_data
            
        except Exception as e:
            print(f"❌ Bot error: {e}")
            return None
    
    def navigate_to_site(self):
        try:
            print("🌐 Navigating to the website...")
            self.driver.get("https://www.elections.org.za/pw/Voter/Voter-Information")
            time.sleep(5)
            
            if "Voter Information" in self.driver.title or "Voter Information" in self.driver.page_source:
                print("✅ Page loaded successfully")
                return True
            else:
                print("⚠️ Page may not have loaded correctly")
                return True
                
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def enter_id_number(self, id_number):
        try:
            print(f"🔢 Looking for ID input field...")
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
                    print(f"✅ Found ID input using: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not id_input:
                print("❌ Could not find ID input field with any selector")
                return False
            
            print(f"📝 Entering ID number: {id_number}")
            id_input.clear()
            id_input.send_keys(id_number)
            
            entered_value = id_input.get_attribute('value')
            if entered_value == id_number:
                print("✅ ID number entered successfully")
                return True
            else:
                print(f"❌ ID number entry failed. Expected: {id_number}, Got: {entered_value}")
                return False
                
        except Exception as e:
            print(f"❌ Error entering ID: {e}")
            return False
    
    def find_recaptcha_elements(self):
        """Find reCAPTCHA v2 elements"""
        try:
            print("🔍 Looking for reCAPTCHA...")
            
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
                    print(f"✅ Found reCAPTCHA element using: {selector}")
                    return recaptcha_element
                except NoSuchElementException:
                    continue
            
            print("❌ Could not find reCAPTCHA elements")
            return None
            
        except Exception as e:
            print(f"❌ Error finding reCAPTCHA: {e}")
            return None
    
    def get_recaptcha_site_key(self):
        """Extract reCAPTCHA site key from the page"""
        try:
            print("🔑 Extracting reCAPTCHA site key...")
            
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
                            print(f"✅ Found reCAPTCHA site key: {site_key}")
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
                            print(f"✅ Found reCAPTCHA site key: {site_key}")
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
                    print(f"✅ Found reCAPTCHA site key: {site_key}")
                    return site_key
            
            print("❌ Could not find reCAPTCHA site key")
            return None
            
        except Exception as e:
            print(f"❌ Error getting site key: {e}")
            return None
    
    def solve_recaptcha_v2(self):
        """Solve reCAPTCHA v2 using 2Captcha"""
        try:
            print("🔄 Starting reCAPTCHA v2 solving...")
            
            site_key = self.get_recaptcha_site_key()
            if not site_key:
                print("❌ No reCAPTCHA site key found")
                return False
            
            page_url = self.driver.current_url
            
            print(f"📡 Solving reCAPTCHA v2...")
            print(f"   Site Key: {site_key}")
            print(f"   Page URL: {page_url}")
            
            try:
                print("⏳ Sending to 2Captcha service (this may take 10-30 seconds)...")
                result = self.solver.recaptcha(
                    sitekey=site_key,
                    url=page_url,
                    version='v2'
                )
                
                recaptcha_token = result['code']
                print("✅ reCAPTCHA solved successfully")
                
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
                    print("✅ reCAPTCHA token injected successfully")
                    time.sleep(2)
                    return True
                else:
                    print("❌ Failed to inject reCAPTCHA token")
                    return False
                
            except Exception as e:
                print(f"❌ 2Captcha reCAPTCHA solving error: {e}")
                return False
            
        except Exception as e:
            print(f"❌ reCAPTCHA solving failed: {e}")
            return False
    
    def submit_form(self):
        """Submit the form after reCAPTCHA is solved"""
        try:
            print("🔍 Looking for submit button...")
            
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
                    print(f"✅ Found submit button using: {selector}")
                    
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
                    time.sleep(1)
                    
                    try:
                        submit_button.click()
                        print("✅ Form submitted using regular click")
                    except:
                        self.driver.execute_script("arguments[0].click();", submit_button)
                        print("✅ Form submitted using JavaScript click")
                    
                    time.sleep(3)
                    return True
                except NoSuchElementException:
                    continue
            
            print("❌ Could not find submit button with any selector")
            return False
            
        except Exception as e:
            print(f"❌ Error submitting form: {e}")
            return False
    
    def wait_for_results_page(self):
        """Wait for the results page to load"""
        try:
            print("⏳ Waiting for results page to load...")
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
                    element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    print(f"✅ Results page indicator found: {selector}")
                    return True
                except TimeoutException:
                    continue
            
            current_url = self.driver.current_url
            if "My-ID-Information-Details" in current_url:
                print("✅ On results page (URL confirmed)")
                return True
            else:
                print(f"⚠️ Current URL: {current_url}")
                
            print("❌ Results page not detected within timeout")
            return False
            
        except Exception as e:
            print(f"❌ Error waiting for results page: {e}")
            return False
    
    def extract_voter_information(self):
        """Extract specific voter information from the results page"""
        try:
            print("📊 Extracting voter information...")
            
            voter_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'identity_number': 'Not found',
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
                print(f"✅ Identity Number: {voter_data['identity_number']}")
            except NoSuchElementException:
                print("❌ Identity Number field not found")
            
            # Extract Ward Information
            try:
                ward_element = self.driver.find_element(By.ID, "MainContent_uxWardDataField")
                ward_text = ward_element.text.strip()
                voter_data['ward'] = ward_text
                print(f"✅ Ward: {voter_data['ward']}")
                
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
                print("❌ Ward field not found")
            
            # Extract Voting District
            try:
                vd_element = self.driver.find_element(By.ID, "MainContent_uxVDDataField")
                voter_data['voting_district'] = vd_element.text.strip()
                print(f"✅ Voting District: {voter_data['voting_district']}")
            except NoSuchElementException:
                print("❌ Voting District field not found")
            
            return voter_data
            
        except Exception as e:
            print(f"❌ Error extracting voter information: {e}")
            return {}
    
    def close(self):
        """Close the browser"""
        try:
            self.driver.quit()
            print("🔒 Browser closed.")
        except:
            print("⚠️ Browser already closed or error closing")

@app.route('/verify-voter', methods=['POST'])
def verify_voter():
    """API endpoint to verify voter information"""
    try:
        data = request.get_json()
        id_number = data.get('id_number')
        
        if not id_number:
            return jsonify({'error': 'ID number is required'}), 400
        
        if len(id_number) != 13 or not id_number.isdigit():
            return jsonify({'error': 'Invalid ID number format'}), 400
        
        # Create and run bot
        bot = VoterInfoBot()
        
        try:
            # Run the bot
            start_time = time.time()
            results = bot.run_bot(id_number)
            end_time = time.time()
            
            if results:
                results['processing_time'] = f"{end_time - start_time:.2f} seconds"
                results['status'] = 'success'
                print(f"✅ Verification completed in {end_time - start_time:.2f} seconds")
                return jsonify(results)
            else:
                return jsonify({
                    'status': 'error',
                    'error': 'Failed to extract voter information'
                }), 500
                
        finally:
            bot.close()
            
    except Exception as e:
        print(f"❌ API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Voter Verification API'})

if __name__ == '__main__':
    print("🚀 Starting Voter Verification API...")
    app.run(host='0.0.0.0', port=5000, debug=True)
