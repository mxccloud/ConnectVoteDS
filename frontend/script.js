// Configuration - Updated with your specific details
const SUPABASE_URL = 'https://gujmsxxkwzhpvfdawyeu.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd1am1zeHhrd3pocHZmZGF3eWV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2Mzk4NTYsImV4cCI6MjA3NjIxNTg1Nn0.-eJki5EWV7RU4NoS4i6En6Pa6kIvgny9-gdYQFa9zmI';

// Backend API URL - Will be updated after Railway deployment
// For now, using a placeholder that will be replaced
const BOT_API_URL = 'https://onnectVoteDS.up.railway.app/verify-voter';

// Initialize Supabase client
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

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
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    const notificationText = document.getElementById('notificationText');
    
    // Set background color based on type
    if (type === 'error') {
        notification.style.background = '#e74c3c';
    } else if (type === 'warning') {
        notification.style.background = '#f39c12';
    } else {
        notification.style.background = 'var(--anc-green)';
    }
    
    notificationText.textContent = message;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 4000);
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
        showNotification('Please enter both email and password', 'warning');
        return false;
    }
    
    try {
        showNotification('Logging in...', 'warning');
        
        const { data, error } = await supabase.auth.signInWithPassword({
            email: email,
            password: password,
        });
        
        if (error) {
            showNotification('Login error: ' + error.message, 'error');
            return false;
        }
        
        currentUser = data.user;
        localStorage.setItem('supabaseUser', JSON.stringify(currentUser));
        
        showApp();
        showNotification(`Welcome back, ${currentUser.email}!`);
        checkSupabaseConnection();
        return true;
    } catch (error) {
        showNotification('Login failed: ' + error.message, 'error');
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
        const verifyBtn = document.getElementById('verifyBtn');
        const verifyBtnText = document.getElementById('verifyBtnText');
        
        // Show loading state
        verifyBtn.disabled = true;
        verifyBtn.classList.add('btn-loading');
        verifyBtnText.textContent = 'Verifying with IEC...';
        
        showNotification('🔍 Verifying with IEC... This may take 20-30 seconds', 'warning');
        
        const response = await fetch(BOT_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id_number: idNumber })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Reset button state
        verifyBtn.disabled = false;
        verifyBtn.classList.remove('btn-loading');
        verifyBtnText.textContent = 'Verify with IEC';
        
        if (result.status === 'success') {
            showNotification('✅ Voter verification successful!');
            return result;
        } else {
            showNotification('❌ Verification failed: ' + (result.error || 'Unknown error'), 'error');
            return null;
        }
    } catch (error) {
        console.error('Verification error:', error);
        
        // Reset button state
        const verifyBtn = document.getElementById('verifyBtn');
        const verifyBtnText = document.getElementById('verifyBtnText');
        verifyBtn.disabled = false;
        verifyBtn.classList.remove('btn-loading');
        verifyBtnText.textContent = 'Verify with IEC';
        
        showNotification('❌ Verification service unavailable. Using simulated data.', 'warning');
        
        // Fallback to simulated data
        return simulateVerificationData(idNumber);
    }
}

// Simulate verification data (fallback)
function simulateVerificationData(idNumber) {
    const age = calculateAgeFromID(idNumber);
    return {
        status: 'success',
        identity_number: idNumber,
        full_name: 'Simulated Voter Name',
        age: age,
        ward: 'Ward ' + (parseInt(idNumber.substring(7, 8)) + 1),
        voting_district: 'District ' + (parseInt(idNumber.substring(9, 10)) + 1),
        voting_station: 'Station ' + (parseInt(idNumber.substring(10, 12)) + 1),
        ward_number: (parseInt(idNumber.substring(7, 8)) + 1).toString(),
        municipality: 'Simulated Municipality',
        province: 'Simulated Province',
        processing_time: '0.5 seconds',
        note: 'Simulated data - Backend service unavailable'
    };
}

// Calculate age from South African ID number
function calculateAgeFromID(idNumber) {
    const year = parseInt(idNumber.substring(0, 2));
    const month = parseInt(idNumber.substring(2, 4));
    const day = parseInt(idNumber.substring(4, 6));
    const currentYear = new Date().getFullYear();
    
    // Determine century (1900s or 2000s)
    const birthYear = year > 25 ? 1900 + year : 2000 + year;
    const age = currentYear - birthYear;
    
    return age;
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
    
    // Navigation buttons
    document.getElementById('toStep2').addEventListener('click', () => goToStep(2));
    document.getElementById('toStep8').addEventListener('click', () => goToStep(8));
    document.getElementById('toSummary').addEventListener('click', () => {
        goToStep(10); // Summary is step 10
        updateSummary();
    });
    
    // Verify ID button
    document.getElementById('verifyBtn').addEventListener('click', async () => {
        const idNumber = document.getElementById('idNumber').value.trim();
        
        if (idNumber.length === 13 && !isNaN(idNumber)) {
            const verificationResult = await verifyWithIEC(idNumber);
            
            if (verificationResult) {
                // Show verification results
                document.getElementById('verificationResults').style.display = 'block';
                
                // Fill in the form with data
                document.getElementById('fullName').value = verificationResult.full_name || 'Verified Voter';
                document.getElementById('age').value = 'Age: ' + verificationResult.age;
                document.getElementById('ward').value = verificationResult.ward;
                document.getElementById('votingDistrict').value = verificationResult.voting_district;
                document.getElementById('votingStation').value = verificationResult.voting_station;
            }
        } else {
            showNotification('Please enter a valid 13-digit ID number', 'warning');
        }
    });
    
    // Consent checkbox
    document.getElementById('consentCheck').addEventListener('change', function() {
        document.getElementById('submitBtn').disabled = !this.checked;
    });
    
    // Submit button
    document.getElementById('submitBtn').addEventListener('click', async () => {
        // Show confirmation screen
        goToStep(11);
        
        // Save data to Supabase
        try {
            const formData = collectFormData();
            const result = await saveDataToSupabase(formData);
            
            if (result) {
                showNotification('Data successfully saved to database');
            }
        } catch (error) {
            showNotification('Error saving to database: ' + error.message, 'error');
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
        resetForm();
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
        change_station: document.querySelector('input[name="changeStation"]:checked')?.value || 'no',
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
    
    const priority = document.getElementById('priority').value;
    document.getElementById('summary-priority').textContent = priority || 'Not specified';
}

// Reset form for new entry
function resetForm() {
    currentStep = 1;
    document.querySelectorAll('input, select').forEach(element => {
        if (element.type !== 'button' && element.type !== 'submit') {
            element.value = '';
            if (element.type === 'radio' || element.type === 'checkbox') {
                element.checked = false;
            }
        }
    });
    
    // Reset default radio buttons
    const defaultRadio = document.querySelector('input[name="changeStation"][value="no"]');
    if (defaultRadio) defaultRadio.checked = true;
    
    document.getElementById('verificationResults').style.display = 'none';
    document.getElementById('consentCheck').checked = false;
    
    updateProgress();
    showNotification('Form reset for new entry');
}

// Initialize the app when DOM is loaded

document.addEventListener('DOMContentLoaded', initApp);
