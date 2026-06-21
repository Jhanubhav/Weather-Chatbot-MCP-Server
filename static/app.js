// State Management
let currentUnit = 'C';
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const typingIndicator = document.getElementById('typingIndicator');
const statusDot = document.getElementById('statusDot');
const statusLabel = document.getElementById('statusLabel');

// Initialize time on the first message
document.getElementById('initTime').textContent = getFormattedTime();

// Poll for MCP server status on load and every 5 seconds
checkServerStatus();
setInterval(checkServerStatus, 5000);

async function checkServerStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        if (data.connected) {
            statusDot.className = 'status-dot status-online';
            statusLabel.textContent = 'MCP Server: Connected';
        } else {
            statusDot.className = 'status-dot status-offline';
            statusLabel.textContent = 'MCP Server: Offline';
        }
    } catch (error) {
        statusDot.className = 'status-dot status-offline';
        statusLabel.textContent = 'MCP Server: Unreachable';
    }
}

function getFormattedTime() {
    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    minutes = minutes < 10 ? '0' + minutes : minutes;
    return `${hours}:${minutes} ${ampm}`;
}

function celsiusToFahrenheit(c) {
    return Math.round((c * 9/5 + 32) * 10) / 10;
}

// Get country flag emoji from country code (e.g. "IN" -> 🇮🇳)
function getFlagEmoji(countryCode) {
    if (!countryCode || countryCode.length !== 2) return '🌍';
    const offset = 127397;
    return String.fromCodePoint(
        countryCode.charCodeAt(0) + offset,
        countryCode.charCodeAt(1) + offset
    );
}

// Change temperature unit globally
function setUnit(unit) {
    if (currentUnit === unit) return;
    currentUnit = unit;
    document.getElementById('unitC').classList.toggle('active', unit === 'C');
    document.getElementById('unitF').classList.toggle('active', unit === 'F');

    document.querySelectorAll('.temp-value').forEach(el => {
        const celsius = parseFloat(el.getAttribute('data-celsius'));
        el.textContent = unit === 'C' ? `${celsius}°C` : `${celsiusToFahrenheit(celsius)}°F`;
    });
    document.querySelectorAll('.temp-apparent').forEach(el => {
        const celsius = parseFloat(el.getAttribute('data-celsius'));
        el.textContent = unit === 'C' ? `Feels like: ${celsius}°C` : `Feels like: ${celsiusToFahrenheit(celsius)}°F`;
    });
}

// Send message
async function sendMessage(event) {
    if (event) event.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    userInput.value = '';
    appendUserMessage(text);
    showTyping(true);
    scrollToBottom();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        const data = await response.json();
        showTyping(false);
        if (data.type === 'weather') {
            appendWeatherMessage(data.data);
        } else {
            appendBotMessage(data.text);
        }
    } catch (error) {
        showTyping(false);
        appendBotMessage('Oops! Could not reach the server. Please check your connection and try again.');
    }
    scrollToBottom();
}

function quickSearch(cityName) {
    userInput.value = `What is the temperature in ${cityName}?`;
    sendMessage();
}

function showTyping(show) {
    typingIndicator.classList.toggle('hidden', !show);
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendUserMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user-message animate-fade-in';
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = getFormattedTime();
    msgDiv.appendChild(contentDiv);
    msgDiv.appendChild(timeSpan);
    chatMessages.appendChild(msgDiv);
}

function formatMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br/>');
}

function appendBotMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot-message animate-fade-in';
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatMarkdown(text);
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = getFormattedTime();
    msgDiv.appendChild(contentDiv);
    msgDiv.appendChild(timeSpan);
    chatMessages.appendChild(msgDiv);
}

function getWeatherSVG(code, isDay) {
    if (code === 0 || code === 1) {
        return isDay
            ? `<svg viewBox="0 0 24 24" fill="none" stroke="#eab308" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                 <circle cx="12" cy="12" r="5"></circle>
                 <line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line>
                 <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                 <line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line>
                 <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
               </svg>`
            : `<svg viewBox="0 0 24 24" fill="none" stroke="#93c5fd" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                 <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
               </svg>`;
    }
    if (code === 2 || code === 3) {
        return `<svg viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path>
                </svg>`;
    }
    if (code === 45 || code === 48) {
        return `<svg viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="5" y1="9" x2="19" y2="9"></line><line x1="3" y1="13" x2="21" y2="13"></line><line x1="6" y1="17" x2="18" y2="17"></line>
                </svg>`;
    }
    if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) {
        return `<svg viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="8" y1="19" x2="8" y2="21"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="16" y1="19" x2="16" y2="21"></line>
                  <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path>
                </svg>`;
    }
    if ((code >= 71 && code <= 77) || (code >= 85 && code <= 86)) {
        return `<svg viewBox="0 0 24 24" fill="none" stroke="#a5f3fc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path>
                  <line x1="8" y1="16" x2="8.01" y2="16"></line><line x1="12" y1="16" x2="12.01" y2="16"></line><line x1="16" y1="16" x2="16.01" y2="16"></line>
                </svg>`;
    }
    if (code >= 95) {
        return `<svg viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M19 10.9A7 7 0 1 0 7.8 17h11.2a4 4 0 0 0 0-8z"></path>
                  <polyline points="13 14 11 18 14 18 12 22"></polyline>
                </svg>`;
    }
    return `<svg viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path>
            </svg>`;
}

function appendWeatherMessage(data) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot-message animate-fade-in';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const introP = document.createElement('p');
    const locationStr = [data.city, data.state, data.country].filter(Boolean).join(', ');
    introP.innerHTML = formatMarkdown(`Here is the live weather for **${locationStr}**:`);
    contentDiv.appendChild(introP);

    const weatherCard = document.createElement('div');
    weatherCard.className = 'weather-card';

    const tempC = data.temperature;
    const apparentC = data.apparent_temperature;
    const displayTemp = currentUnit === 'C' ? `${tempC}°C` : `${celsiusToFahrenheit(tempC)}°F`;
    const displayApparent = currentUnit === 'C' ? `Feels like: ${apparentC}°C` : `Feels like: ${celsiusToFahrenheit(apparentC)}°F`;

    // Build flag from country_code
    const flag = getFlagEmoji(data.country_code || '');
    const locationDisplay = data.state ? `${data.state}, ${data.country}` : data.country;
    const localTime = data.time ? data.time.split('T')[1] || data.time : 'N/A';

    weatherCard.innerHTML = `
        <div class="weather-header">
            <div class="weather-location">
                <h3>📍 ${data.city}</h3>
                <span>${locationDisplay}</span>
            </div>
            <div class="india-flag">${flag} ${data.country_code || ''}</div>
        </div>
        <div class="weather-main">
            <div class="temp-container">
                <span class="temp-value" data-celsius="${tempC}">${displayTemp}</span>
                <span class="temp-apparent" data-celsius="${apparentC}">${displayApparent}</span>
            </div>
            <div class="weather-icon-box">
                ${getWeatherSVG(data.weather_code, data.is_day)}
            </div>
        </div>
        <div class="weather-condition-pill">${data.weather_description}</div>
        <div class="weather-details-grid">
            <div class="metric-item">
                <span class="metric-icon">💧</span>
                <div class="metric-info">
                    <span class="metric-label">Humidity</span>
                    <span class="metric-value">${data.humidity}%</span>
                </div>
            </div>
            <div class="metric-item">
                <span class="metric-icon">💨</span>
                <div class="metric-info">
                    <span class="metric-label">Wind</span>
                    <span class="metric-value">${data.wind_speed} km/h</span>
                </div>
            </div>
            <div class="metric-item">
                <span class="metric-icon">🌐</span>
                <div class="metric-info">
                    <span class="metric-label">Latitude</span>
                    <span class="metric-value">${data.latitude.toFixed(2)}°</span>
                </div>
            </div>
            <div class="metric-item">
                <span class="metric-icon">🌐</span>
                <div class="metric-info">
                    <span class="metric-label">Longitude</span>
                    <span class="metric-value">${data.longitude.toFixed(2)}°</span>
                </div>
            </div>
        </div>
        <div class="weather-footer">
            <span>Local Time: ${localTime}</span>
            <span>${data.is_day ? 'Daytime ☀️' : 'Night 🌙'}</span>
        </div>
    `;

    contentDiv.appendChild(weatherCard);

    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = getFormattedTime();

    msgDiv.appendChild(contentDiv);
    msgDiv.appendChild(timeSpan);
    chatMessages.appendChild(msgDiv);
}
