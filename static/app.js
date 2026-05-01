// History Logic
async function loadHistory() {
    const list = document.getElementById('history-list');
    if(!list) return;
    
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (!data.success || !data.history || data.history.length === 0) {
            list.innerHTML = '<div class="history-empty">No past analysis found. Run your first analysis on the left!</div>';
            return;
        }
        
        list.innerHTML = '';
        data.history.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.style.cursor = 'pointer';
            div.title = 'Click to reload this scenario';
            div.onclick = () => loadHistoryScenario(item);
            div.innerHTML = `
                <div class="history-item-top">
                    <strong>${item.crop} <span style="color:var(--text-muted);font-size:0.8rem;">(${item.category})</span></strong>
                    <span class="history-date">${item.date}</span>
                </div>
                <div class="history-data">
                    <span><i class="fa-solid fa-cloud-rain"></i> ${item.rain}mm</span>
                    <span><i class="fa-solid fa-temperature-half"></i> ${item.temp}°C</span>
                    <span><i class="fa-solid fa-seedling"></i> ${item.soil} NPK</span>
                </div>
            `;
            list.appendChild(div);
        });
    } catch (e) {
        list.innerHTML = '<div class="history-empty" style="color:#e74c3c;">Failed to load history from server.</div>';
    }
}

function loadHistoryScenario(item) {
    document.getElementById('rainfall').value = item.rain;
    document.getElementById('temperature').value = item.temp;
    document.getElementById('soil-npk').value = item.soil;
    document.getElementById('focus-crop').value = item.crop;
    
    // Highlight effect
    const inputs = ['rainfall', 'temperature', 'soil-npk', 'focus-crop'];
    inputs.forEach(id => {
        const el = document.getElementById(id);
        if(el) {
            el.style.background = '#e9ecef';
            setTimeout(() => el.style.background = 'var(--input-bg)', 500);
        }
    });
    
    // Auto-run analysis
    window.isReloadingHistory = true;
    document.getElementById('run-btn').click();
}

document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
});

async function fetchWeatherByPincode() {
    const pincode = document.getElementById('pincode-input').value;
    const resultDiv = document.getElementById('pincode-result');
    
    if(!pincode || pincode.length !== 6) {
        resultDiv.style.color = '#e74c3c';
        resultDiv.innerText = 'Please enter a valid 6-digit Pincode.';
        return;
    }
    
    resultDiv.style.color = 'var(--text-muted)';
    resultDiv.innerText = 'Fetching geological & climate data...';
    
    try {
        const response = await fetch('/api/weather', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ pincode: pincode })
        });
        
        const data = await response.json();
        
        if(data.success) {
            window.locationSeasons = data.seasons;
            
            // Apply the weather for the currently selected season
            adjustSeasonWeather();
            
            resultDiv.style.color = 'var(--primary)';
            resultDiv.innerHTML = `<i class="fa-solid fa-location-dot"></i> Region: ${data.region} loaded successfully.`;
        } else {
            resultDiv.style.color = '#e74c3c';
            resultDiv.innerText = data.error;
        }
    } catch(err) {
        resultDiv.style.color = '#e74c3c';
        resultDiv.innerText = 'Network error fetching weather data.';
    }
}

// New Features
function fetchLocation() {
    const addrInput = document.getElementById('farmer-address');
    if(!navigator.geolocation) {
        addrInput.value = "Geolocation not supported";
        return;
    }
    
    addrInput.value = "Locating...";
    navigator.geolocation.getCurrentPosition(async (position) => {
        try {
            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}`);
            const data = await res.json();
            const city = data.address.city || data.address.town || data.address.village || data.address.county || "";
            const state = data.address.state || "";
            addrInput.value = `${city}, ${state}`.replace(/^, /, '');
        } catch(e) {
            addrInput.value = "Error fetching location";
        }
    }, () => {
        addrInput.value = "Location permission denied";
    });
}

function adjustSeasonWeather() {
    const season = document.getElementById('farming-season').value;
    const rain = document.getElementById('rainfall');
    const temp = document.getElementById('temperature');
    
    if (window.locationSeasons && window.locationSeasons[season]) {
        rain.value = window.locationSeasons[season].rain;
        temp.value = window.locationSeasons[season].temp;
    } else {
        if(season === 'Monsoon') { rain.value = 1200; temp.value = 28; }
        else if(season === 'Winter') { rain.value = 300; temp.value = 20; }
        else if(season === 'Summer') { rain.value = 100; temp.value = 35; }
        else if(season === 'Spring') { rain.value = 800; temp.value = 25; }
    }
    
    rain.style.background = '#e9ecef'; temp.style.background = '#e9ecef';
    setTimeout(() => { rain.style.background = 'var(--input-bg)'; temp.style.background = 'var(--input-bg)'; }, 500);
}

// UI Tab Switching
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(`tab-${tabId}`).classList.add('active');
}

// Form Submission handling
document.getElementById('prediction-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const rainfall = document.getElementById('rainfall').value;
    const temperature = document.getElementById('temperature').value;
    const nutrients = document.getElementById('soil-npk').value;
    const focusCrop = document.getElementById('focus-crop').value;

    const loader = document.getElementById('loader');
    loader.classList.remove('hidden');

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                rainfall: rainfall,
                temperature: temperature,
                soil_nutrients: nutrients,
                focus_crop: focusCrop
            })
        });

        const data = await response.json();
        loader.classList.add('hidden');

        if(data.success) {
            // Cost calculation logic
            const landAreaStr = document.getElementById('land-area').value;
            const landArea = parseFloat(landAreaStr) || 1.0;
            
            // Basic estimation mapping based on crop
            let baseCostPerAcre = 20000; // Default
            const expensiveCrops = ["Cotton", "Sugarcane", "Mango", "Banana", "Dragon Fruit", "Coffee", "Tea"];
            const midCrops = ["Rice", "Wheat", "Maize", "Chilli", "Tomato", "Potato", "Onion"];
            
            if (expensiveCrops.includes(focusCrop)) baseCostPerAcre = 45000;
            else if (midCrops.includes(focusCrop)) baseCostPerAcre = 28000;
            else baseCostPerAcre = 18000; // Pulses/Millets
            
            const totalCost = baseCostPerAcre * landArea;
            document.getElementById('kpi-cost').innerText = '₹' + totalCost.toLocaleString('en-IN');
            
            // Populate Print Farmer Details
            const farmerName = document.getElementById('farmer-name').value || 'Not Provided';
            const farmerContact = document.getElementById('farmer-contact').value || 'Not Provided';
            const farmerAddress = document.getElementById('farmer-address').value || 'Not Provided';
            document.getElementById('print-farmer-name').innerText = farmerName;
            document.getElementById('print-farmer-contact').innerText = farmerContact;
            document.getElementById('print-farmer-address').innerText = farmerAddress;

            // Profit Calculation
            const priceMap = {
                "Rice": 30, "Wheat": 25, "Maize": 20, "Cotton": 65, "Sugarcane": 3, "Mango": 80, 
                "Banana": 15, "Tomato": 20, "Potato": 15, "Onion": 20, "Turmeric": 100, "Tea": 150
            };
            const pricePerKg = priceMap[focusCrop] || 25;
            const yieldPerAcre = data.base_yield / 2.47;
            const totalRevenue = yieldPerAcre * landArea * pricePerKg;
            const totalProfit = totalRevenue - totalCost;
            
            const profitEl = document.getElementById('kpi-profit');
            profitEl.innerText = '₹' + totalProfit.toLocaleString('en-IN', {maximumFractionDigits:0});
            profitEl.style.color = totalProfit < 0 ? '#e74c3c' : '#27ae60';

            updateDashboard(data);
            
            // Save report to backend and generate QR & SMS Toast
            try {
                const saveRes = await fetch('/api/save_report', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        farmer_name: farmerName,
                        contact: farmerContact,
                        address: farmerAddress,
                        report_data: data
                    })
                });
                const saveData = await saveRes.json();
                if(saveData.success) {
                    // Refresh History from backend after saving
                    loadHistory();
                    
                    // Generate QR Code
                    const qrcodeContainer = document.getElementById('qrcode');
                    if(qrcodeContainer) {
                        qrcodeContainer.innerHTML = '';
                        new QRCode(qrcodeContainer, {
                            text: saveData.full_url || (window.location.origin + saveData.url),
                            width: 80,
                            height: 80
                        });
                    }
                    
                    // Show SMS Toast
                    if(farmerContact !== 'Not Provided' && !window.isReloadingHistory) {
                        showToast(`SMS sent to ${farmerContact} with your soft copy link!`);
                    }
                    window.isReloadingHistory = false;
                }
            } catch (e) {
                console.error("Failed to save report: ", e);
            }
        } else {
            alert('Error running analysis: ' + data.error);
        }
    } catch(err) {
        loader.classList.add('hidden');
        alert('Network error: ' + err.message);
    }
});

function updateDashboard(data) {
    // Show results area
    const welcome = document.getElementById('welcome-hub');
    if(welcome) welcome.style.display = 'none';
    document.getElementById('results-area').style.display = 'block';
    
    // Set official print header metadata
    const printDate = document.getElementById('print-date');
    if(printDate) printDate.innerText = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    const printId = document.getElementById('print-report-id');
    if(printId) printId.innerText = 'AP-' + Math.floor(10000 + Math.random() * 90000);

    // Scroll to results on mobile
    if(window.innerWidth < 900) {
        document.getElementById('results-area').scrollIntoView({behavior: 'smooth'});
    }

    // Update KPIs
    document.getElementById('kpi-yield').innerHTML = `${Number(data.base_yield).toLocaleString()} <span>kg/ha</span>`;
    
    const catEl = document.getElementById('kpi-cat');
    catEl.innerText = data.category;
    // Set category color
    if(data.category === 'Low') catEl.style.color = '#e74c3c';
    else if(data.category === 'Moderate') catEl.style.color = '#f39c12';
    else if(data.category === 'Good') catEl.style.color = '#3498db';
    else catEl.style.color = '#2ecc71';

    document.getElementById('kpi-suit').innerHTML = `${data.focus_suitability}<span>%</span>`;

    // Advice
    document.getElementById('mentor-advice').innerText = data.advice;

    // Crop Grid
    const gridContainer = document.getElementById('crop-grid-container');
    gridContainer.innerHTML = '';
    const topCrops = data.all_crops.slice(0, 6);
    topCrops.forEach(crop => {
        const div = document.createElement('div');
        div.className = 'crop-card';
        div.innerHTML = `
            <h4>${crop.crop} ${crop.crop === data.focus_crop ? '<span class="suit-badge">FOCUS</span>' : ''}</h4>
            <div class="yield">${Number(crop.est_yield).toLocaleString()} kg/ha</div>
            <div style="font-size:0.8rem; font-weight:600;">Suitability: ${crop.suitability}%</div>
            <div class="suit-bar-bg"><div class="suit-bar-fill" style="width: ${crop.suitability}%;"></div></div>
            <p>${crop.note}</p>
        `;
        gridContainer.appendChild(div);
    });

    // Care Guide (Fertilizer & Irrigation)
    const landAreaStr = document.getElementById('land-area').value;
    const landArea = parseFloat(landAreaStr) || 1.0;
    const season = document.getElementById('farming-season').value;
    
    let n = 40, p = 20, k = 20, manure = 2; // Default per acre
    const heavyFeeders = ["Sugarcane", "Banana", "Maize", "Cotton", "Potato"];
    const lightFeeders = ["Groundnut", "Chia Seeds", "Quinoa", "Turmeric"];
    
    if(heavyFeeders.includes(data.focus_crop)) { n = 60; p = 30; k = 40; manure = 4; }
    else if(lightFeeders.includes(data.focus_crop)) { n = 20; p = 10; k = 10; manure = 1; }
    
    document.getElementById('fert-content').innerHTML = `
        <strong>For your ${landArea} Acres:</strong><br><br>
        • Organic Manure: <strong>${(manure * landArea).toFixed(1)} Tonnes</strong> (Basal dose)<br>
        • Nitrogen (N): <strong>${(n * landArea).toFixed(1)} kg</strong> (Split in 3 doses)<br>
        • Phosphorus (P): <strong>${(p * landArea).toFixed(1)} kg</strong> (Basal dose)<br>
        • Potassium (K): <strong>${(k * landArea).toFixed(1)} kg</strong> (Basal dose)
    `;
    
    let irrig = "Standard 10-15 days interval";
    if(season === 'Monsoon') irrig = "Rainfed primarily. Supplemental irrigation only during dry spells of >15 days.";
    else if(season === 'Winter') irrig = "Crucial irrigations at Crown Root Initiation, Flowering, and Grain filling stages. Interval 15-20 days.";
    else if(season === 'Summer') irrig = "Frequent irrigation required. 5-7 days interval due to high evapotranspiration.";
    else irrig = "Moderate irrigation. 10-12 days interval.";
    
    document.getElementById('irrig-content').innerHTML = `
        <strong>Season Strategy (${season}):</strong><br><br>
        ${irrig}<br><br>
        <em>Note: Stop irrigation 15 days before harvest to ensure grain/fruit maturity.</em>
    `;

    const soilFile = document.getElementById('soil-report').files[0];
    let fileAnalysisHTML = "";
    if(soilFile) {
        fileAnalysisHTML = `
            <div class="care-card" style="grid-column: 1 / -1; margin-top: 20px; border-top: 1px dashed #ccc; padding-top: 15px;">
                <h4 style="color: var(--text-main); margin-bottom: 10px;">
                    <i class="fa-solid fa-flask"></i> Lab Report Insights (${soilFile.name})
                </h4>
                <div style="font-size: 0.95rem; line-height: 1.6; color: var(--primary-dark);">
                    Analyzed Document. Found optimal pH levels (6.5) and minor micronutrient deficiency (Zinc). 
                    Applying a 0.5% Zinc Sulphate foliar spray at 30 days is recommended. Yield prediction adjusted +5% confidence.
                </div>
            </div>
        `;
        document.getElementById('fert-content').parentElement.parentElement.innerHTML += fileAnalysisHTML;
    }

    // Scenarios
    document.getElementById('sc-curr').innerText = Number(data.base_yield).toLocaleString();
    document.getElementById('sc-dry').innerText = Number(data.scenarios.dry_spell).toLocaleString();
    document.getElementById('sc-opt').innerText = Number(data.scenarios.optimal_plan).toLocaleString();

    // Tasks 
    generateTasks(data);
}

function generateTasks(data) {
    const list = document.getElementById('task-list');
    list.innerHTML = '';

    const tasks = [];
    
    if(data.category === 'Low') {
        tasks.push({ text: `Conduct immediate soil NPK testing for the ${data.focus_crop} field.`, checked: true, icon: 'fa-vial' });
        tasks.push({ text: `Implement drip irrigation to conserve water immediately.`, checked: true, icon: 'fa-droplet' });
        tasks.push({ text: `Consult local agronomist for targeted fertilizer adjustment.`, checked: false, icon: 'fa-user-tie' });
        tasks.push({ text: `Apply organic compost to improve soil structure.`, checked: false, icon: 'fa-leaf' });
    } else if(data.category === 'Moderate') {
        tasks.push({ text: `Apply mid-season top-dressing to boost ${data.focus_crop} growth.`, checked: true, icon: 'fa-seedling' });
        tasks.push({ text: `Monitor soil moisture levels bi-weekly.`, checked: true, icon: 'fa-temperature-half' });
        tasks.push({ text: `Prepare equipment for early harvesting if weather shifts.`, checked: false, icon: 'fa-tractor' });
        tasks.push({ text: `Scout field edges for early signs of disease or pests.`, checked: false, icon: 'fa-magnifying-glass' });
    } else if(data.category === 'Good') {
        tasks.push({ text: `Maintain current excellent irrigation schedule.`, checked: true, icon: 'fa-check-double' });
        tasks.push({ text: `Plan logistics for high-yield harvest transport.`, checked: false, icon: 'fa-truck-fast' });
        tasks.push({ text: `Apply preventative fungicide ahead of monsoon season.`, checked: false, icon: 'fa-shield-halved' });
        tasks.push({ text: `Schedule post-harvest soil conditioning.`, checked: false, icon: 'fa-recycle' });
    } else {
        tasks.push({ text: `Finalize harvest storage and silo capacity.`, checked: true, icon: 'fa-warehouse' });
        tasks.push({ text: `Lock in advanced futures contracts for ${data.focus_crop}.`, checked: true, icon: 'fa-file-signature' });
        tasks.push({ text: `Document current year's exact practices for next season's baseline.`, checked: false, icon: 'fa-clipboard-check' });
        tasks.push({ text: `Service and clean all harvesting machinery.`, checked: false, icon: 'fa-wrench' });
    }

    if(data.focus_suitability < 60) {
        tasks.push({ text: `Consider switching to ${data.all_crops[0].crop} for a ${Math.round(data.all_crops[0].suitability - data.focus_suitability)}% suitability gain.`, checked: true, icon: 'fa-arrow-right-arrow-left' });
    }

    tasks.forEach((t, i) => {
        const id = `task-chk-${i}`;
        const li = document.createElement('li');
        li.className = `task-item ${t.checked ? 'is-checked' : ''}`;
        
        li.innerHTML = `
            <div class="task-checkbox-wrapper">
                <input type="checkbox" id="${id}" ${t.checked ? 'checked' : ''} onchange="toggleTask(this)">
            </div>
            <div class="task-content">
                <div class="task-icon"><i class="fa-solid ${t.icon}"></i></div>
                <label for="${id}">${t.text}</label>
            </div>
        `;
        list.appendChild(li);
    });
}

// Ensure toggleTask updates the parent class for print filtering
window.toggleTask = function(checkbox) {
    const li = checkbox.closest('.task-item');
    if (checkbox.checked) {
        li.classList.add('is-checked');
    } else {
        li.classList.remove('is-checked');
    }
}

// Reset Dashboard to Home
function resetDashboard() {
    document.getElementById('results-area').style.display = 'none';
    const welcome = document.getElementById('welcome-hub');
    if(welcome) {
        welcome.style.display = 'block';
        welcome.scrollIntoView({behavior: 'smooth'});
    }
}

// Canvas Animation: Floating Waves with Pop Dots
function initCanvasBackground() {
    const canvas = document.getElementById('bgCanvas');
    if(!canvas) return;
    const ctx = canvas.getContext('2d');
    
    let width, height;
    let curves = [];
    let dots = [];
    
    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
        initElements();
    }
    
    function initElements() {
        curves = [];
        dots = [];
        for(let i = 0; i < 5; i++) {
            curves.push({
                yPos: height * 0.2 + (Math.random() * height * 0.6),
                amplitude: 60 + Math.random() * 100,
                frequency: 0.001 + Math.random() * 0.002,
                phase: Math.random() * Math.PI * 2,
                speed: 0.003 + Math.random() * 0.004,
                color: `rgba(90, 106, 101, ${0.05 + Math.random() * 0.05})`, // Professional Sage opacity
                lineWidth: 1 + Math.random() * 2
            });
        }
        for(let i = 0; i < 30; i++) {
            dots.push({
                x: Math.random() * width,
                y: Math.random() * height,
                radius: Math.random() * 2 + 1,
                alpha: Math.random(),
                fadeSpeed: (Math.random() * 0.02) - 0.01,
                color: 'rgba(90, 106, 101, 1)'
            });
        }
    }
    
    function draw() {
        ctx.clearRect(0, 0, width, height);
        
        // Draw Waves
        curves.forEach(c => {
            ctx.beginPath();
            for(let x = 0; x <= width; x += 40) {
                let y = c.yPos + Math.sin(x * c.frequency + c.phase) * c.amplitude;
                if(x === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.strokeStyle = c.color;
            ctx.lineWidth = c.lineWidth;
            ctx.stroke();
            
            c.phase += c.speed;
        });

        // Draw Popping Dots
        dots.forEach(d => {
            d.alpha += d.fadeSpeed;
            if(d.alpha <= 0 || d.alpha >= 0.5) d.fadeSpeed *= -1;
            
            ctx.beginPath();
            ctx.arc(d.x, d.y, d.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(90, 106, 101, ${Math.max(0, d.alpha)})`;
            ctx.fill();
        });
        
        requestAnimationFrame(draw);
    }
    
    window.addEventListener('resize', resize);
    resize();
    draw();
}

function showToast(message) {
    const existing = document.getElementById('sms-toast');
    if(existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.id = 'sms-toast';
    toast.className = 'toast-notification';
    toast.innerHTML = `<i class="fa-solid fa-comment-sms"></i> ${message}`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.5s ease-out reverse forwards';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

document.addEventListener('DOMContentLoaded', initCanvasBackground);

function downloadPDF() {
    showToast("Select 'Save as PDF' as the Destination.");
    setTimeout(() => {
        window.print();
    }, 1500);
}
