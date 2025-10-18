// Initialize Supabase with your new credentials
const SUPABASE_URL = 'https://gujmsxxkwzhpvfdawyeu.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd1am1zeHhrd3pocHZmZGF3eWV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2Mzk4NTYsImV4cCI6MjA3NjIxNTg1Nn0.-eJki5EWV7RU4NoS4i6En6Pa6kIvgny9-gdYQFa9zmI';

// Initialize Supabase client
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// API endpoint for voter verification
const BOT_API_URL = 'http://localhost:5000/verify-voter';

// Current step tracking
let currentStep = 1;
const totalSteps = 9;
let currentUser = null;

// DOM Elements
const loginScreen = document.getElementById('loginScreen');
const appContainer = document.getElementById('appContainer');
const progressBar = document.getElementById('progressBar');
const stepElements = document.querySelectorAll('.step');
const stepContents = document.querySelectorAll('.step-content');
const currentUserName = document.getElementById('currentUserName');
const supabaseStatus = document.getElementById('supabaseStatus');
const supabaseStatusText = document.getElementById('supabaseStatusText');

// Initialize the app
function initApp() {
    // Check if user is already logged in (from localStorage)
    const savedUser = localStorage.getItem('supabaseUser');
    if (savedUser) {
        try {
            currentUser = JSON.parse(savedUser);
            showApp();
            checkSupabaseConnection();
        } catch (e) {
            console.error("Error parsing saved user data", e);
            localStorage.removeItem('supabaseUser');
        }
    }
    
    setupEventListeners();
}

// Show the main application
function showApp() {
    loginScreen.style.display = 'none';
    appContainer.style.display = 'block';
    currentUserName.textContent = currentUser.email;
    updateProgress();
}

// Show notification
function showNotification(message) {
    const notification = document.getElementById('notification');
    const notificationText = document.getElementById('notificationText');
    
    notificationText.textContent = message;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// Show Supabase status
function showSupabaseStatus(message, isSuccess = true) {
    supabaseStatusText.textContent = message;
    supabaseStatus.style.background = isSuccess ? '#3ecf8e' : '#e74c3c';
    supabaseStatus.style.display = 'block';
    
    setTimeout(() => {
        supabaseStatus.style.display = 'none';
    }, 5000);
}

// Check Supabase connection
async function checkSupabaseConnection() {
    try {
        const { data, error } = await supabase.from('voter_profiles').select('count').limit(1);
        
        if (error) {
            showSupabaseStatus("Supabase connection failed", false);
            console.error('Supabase error:', error);
        } else {
            showSupabaseStatus("Connected to Supabase successfully", true);
        }
    } catch (error) {
        showSupabaseStatus("Supabase connection error", false);
        console.error('Connection error:', error);
    }
}

// Update progress bar and step indicators
function updateProgress() {
    // Update progress bar width
    const progressPercentage = (currentStep / totalSteps) * 100;
    progressBar.style.width = `${progressPercentage}%`;
    
    // Update step indicators
    stepElements.forEach((step, index) => {
        if (index + 1 === currentStep) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });
    
    // Show current step content
    stepContents.forEach((content, index) => {
        if (index + 1 === currentStep) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
    
    window.scrollTo(0, 0);
}

// Navigate to a specific step
function goToStep(stepNumber) {
    if (stepNumber >= 1 && stepNumber <= totalSteps + 2) {
        currentStep = stepNumber;
        updateProgress();
    }
}

// Handle login with Supabase
async function handleLogin(email, password) {
    if (!email || !password) {
        showNotification('Please enter both email and password');
        return false;
    }
    
    try {
        const { data, error } = await supabase.auth.signInWithPassword({
            email: email,
            password: password,
        });
        
        if (error) {
            showNotification('Login error: ' + error.message);
            return false;
        }
        
        currentUser = data.user;
        localStorage.setItem('supabaseUser', JSON.stringify(currentUser));
        
        showApp();
        showNotification(`Welcome back, ${currentUser.email}!`);
        checkSupabaseConnection();
        return true;
    } catch (error) {
        showNotification('Login failed: ' + error.message);
        return false;
    }
}

// Handle logout
async function handleLogout() {
    try {
        await supabase.auth.signOut();
        currentUser = null;
        localStorage.removeItem('supabaseUser');
        appContainer.style.display = 'none';
        loginScreen.style.display = 'flex';
        
        // Clear form fields
        document.getElementById('email').value = '';
        document.getElementById('password').value = '';
        
        showNotification('Logged out successfully');
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Verify voter with IEC using Python bot
async function verifyWithIEC(idNumber) {
    try {
        showNotification('🔍 Verifying with IEC... This may take 20-30 seconds');
        
        const response = await fetch(BOT_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id_number: idNumber })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showNotification('✅ Voter verification successful!');
            return result;
        } else {
            showNotification('❌ Verification failed: ' + (result.error || 'Unknown error'));
            return null;
        }
    } catch (error) {
        console.error('Verification error:', error);
        showNotification('❌ Verification service unavailable');
        return null;
    }
}

// Save data to Supabase
async function saveDataToSupabase(formData) {
    try {
        showSupabaseStatus("Saving data to Supabase...");
        
        const { data, error } = await supabase
            .from('voter_profiles')
            .insert([formData])
            .select();
        
        if (error) {
            showSupabaseStatus("Error saving to Supabase", false);
            throw error;
        }
        
        showSupabaseStatus("Data saved to Supabase successfully", true);
        return data;
    } catch (error) {
        console.error('Supabase error:', error);
        throw error;
    }
}

// Setup event listeners
function setupEventListeners() {
    // Login button
    document.getElementById('loginBtn').addEventListener('click', async () => {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        await handleLogin(email, password);
    });
    
    // Allow Enter key to submit login form
    document.getElementById('password').addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            await handleLogin(email, password);
        }
    });
    
    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    
    // Test Supabase connection
    document.getElementById('testSupabaseConnection').addEventListener('click', checkSupabaseConnection);
    
    // Navigation buttons
    document.getElementById('toStep2').addEventListener('click', () => goToStep(2));
    document.getElementById('toStep1').addEventListener('click', () => goToStep(1));
    document.getElementById('toStep3').addEventListener('click', () => goToStep(3));
    document.getElementById('toStep2Back').addEventListener('click', () => goToStep(2));
    document.getElementById('toStep4').addEventListener('click', () => goToStep(4));
    document.getElementById('toStep8').addEventListener('click', () => goToStep(8));
    document.getElementById('toSummary').addEventListener('click', () => {
        goToStep(10); // Summary is step 10
        updateSummary();
    });
    
    // Verify ID button - UPDATED TO USE PYTHON BOT
    document.getElementById('verifyBtn').addEventListener('click', async () => {
        const idNumber = document.getElementById('idNumber').value;
        
        if (idNumber.length === 13 && !isNaN(idNumber)) {
            // Disable button during processing
            const verifyBtn = document.getElementById('verifyBtn');
            verifyBtn.disabled = true;
            verifyBtn.textContent = 'Verifying with IEC...';
            
            try {
                // Call the Python bot API
                const verificationResult = await verifyWithIEC(idNumber);
                
                if (verificationResult) {
                    // Show verification results
                    document.getElementById('verificationResults').style.display = 'block';
                    
                    // Fill in the form with real data from IEC
                    document.getElementById('fullName').value = verificationResult.identity_number || 'Verified Voter';
                    document.getElementById('age').value = 'Based on ID: ' + calculateAgeFromID(idNumber);
                    document.getElementById('ward').value = verificationResult.ward || 'Ward information';
                    document.getElementById('votingDistrict').value = verificationResult.voting_district || 'District information';
                    document.getElementById('votingStation').value = verificationResult.voting_district || 'Station information';
                    
                    showNotification('✅ ID successfully verified with IEC');
                } else {
                    // Fallback to simulation if API fails
                    simulateVerification(idNumber);
                    showNotification('⚠️ Using simulated data (API unavailable)');
                }
            } catch (error) {
                console.error('Verification error:', error);
                simulateVerification(idNumber);
                showNotification('⚠️ Using simulated data (API error)');
            } finally {
                // Re-enable button
                verifyBtn.disabled = false;
                verifyBtn.textContent = 'Verify with IEC';
            }
        } else {
            showNotification('Please enter a valid 13-digit ID number');
        }
    });
    
    // Helper function to calculate age from ID
    function calculateAgeFromID(idNumber) {
        const year = parseInt(idNumber.substring(0, 2));
        const currentYear = new Date().getFullYear();
        const birthYear = year > 25 ? 1900 + year : 2000 + year;
        return currentYear - birthYear;
    }
    
    // Fallback simulation function
    function simulateVerification(idNumber) {
        document.getElementById('verificationResults').style.display = 'block';
        document.getElementById('fullName').value = 'Simulated Voter Name';
        document.getElementById('age').value = 'Based on ID: ' + calculateAgeFromID(idNumber);
        document.getElementById('ward').value = 'Ward ' + (parseInt(idNumber.substring(7, 8)) + 1);
        document.getElementById('votingDistrict').value = 'District ' + (parseInt(idNumber.substring(9, 10)) + 1);
        document.getElementById('votingStation').value = 'Station ' + (parseInt(idNumber.substring(10, 12)) + 1);
    }
    
    // Consent checkbox
    document.getElementById('consentCheck').addEventListener('change', function() {
        document.getElementById('submitBtn').disabled = !this.checked;
    });
    
    // Submit button - Now saves to Supabase
    document.getElementById('submitBtn').addEventListener('click', async () => {
        // Show confirmation screen
        goToStep(11); // Confirmation is step 11
        
        // Save data to Supabase
        try {
            const formData = collectFormData();
            const result = await saveDataToSupabase(formData);
            
            if (result) {
                showNotification('Data successfully saved to database');
            }
        } catch (error) {
            showNotification('Error saving to database: ' + error.message);
            console.error('Database Error:', error);
        }
    });
    
    // Download profile button
    document.getElementById('downloadProfile').addEventListener('click', () => {
        showNotification('Profile download started');
        // In a real app, this would generate a PDF
    });
    
    // New entry button
    document.getElementById('newEntry').addEventListener('click', () => {
        // Reset the form
        currentStep = 1;
        document.querySelectorAll('input, select').forEach(element => {
            if (element.type !== 'button') {
                element.value = '';
                if (element.type === 'radio' || element.type === 'checkbox') {
                    element.checked = false;
                }
            }
        });
        // Reset first radio buttons
        document.querySelector('input[name="changeStation"]').checked = true;
        document.getElementById('verificationResults').style.display = 'none';
        
        updateProgress();
    });
}

// Collect all form data
function collectFormData() {
    return {
        id_number: document.getElementById('idNumber').value,
        full_name: document.getElementById('fullName').value,
        age: document.getElementById('age').value,
        ward: document.getElementById('ward').value,
        voting_district: document.getElementById('votingDistrict').value,
        voting_station: document.getElementById('votingStation').value,
        change_station: document.querySelector('input[name="changeStation"]:checked').value,
        gender: document.querySelector('input[name="gender"]:checked')?.value,
        marital_status: document.getElementById('maritalStatus').value,
        household_size: document.getElementById('householdSize').value,
        housing_type: document.getElementById('housingType').value,
        priority: document.getElementById('priority').value,
        wants_notifications: document.querySelector('input[name="notifications"]:checked')?.value === 'yes',
        collected_by: currentUser.email,
        collected_at: new Date().toISOString()
    };
}

// Update summary with entered data
function updateSummary() {
    document.getElementById('summary-id').textContent = document.getElementById('idNumber').value;
    document.getElementById('summary-name').textContent = document.getElementById('fullName').value;
    document.getElementById('summary-station').textContent = document.getElementById('votingStation').value;
    
    const gender = document.querySelector('input[name="gender"]:checked');
    const maritalStatus = document.getElementById('maritalStatus').value;
    document.getElementById('summary-demographics').textContent = 
        `${gender ? gender.value : 'Not specified'}, ${maritalStatus || 'Not specified'}`;
    
    const householdSize = document.getElementById('householdSize').value;
    const housingType = document.getElementById('housingType').value;
    document.getElementById('summary-household').textContent = 
        `${householdSize} people, ${housingType || 'Not specified'}`;
    
    const priority = document.getElementById('priority').value;
    document.getElementById('summary-priority').textContent = priority || 'Not specified';
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);
