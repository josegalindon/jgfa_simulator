// Portfolio Dashboard JavaScript
// Handles API calls, data visualization, and user interactions

let charts = {};
let positionsData = { long: [], short: [] };

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', handleRefresh);

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });

    // Table search and sort
    document.getElementById('longSearch').addEventListener('input', function() {
        filterTable('long', this.value);
    });

    document.getElementById('shortSearch').addEventListener('input', function() {
        filterTable('short', this.value);
    });

    document.getElementById('longSort').addEventListener('change', function() {
        sortTable('long', this.value);
    });

    document.getElementById('shortSort').addEventListener('change', function() {
        sortTable('short', this.value);
    });

    // Start periodic status updates (every 60 seconds)
    updateStatusDisplay();
    setInterval(updateStatusDisplay, 60000);
}

// Initialize dashboard - load all data
async function initializeDashboard() {
    showLoading(true);

    try {
        // Load all data in parallel
        const [summaryData, positionsData, chartData] = await Promise.all([
            fetchPortfolioSummary(),
            fetchPositions(),
            fetchChartData()
        ]);

        // Update UI
        updateSummaryCards(summaryData);
        updatePerformers(summaryData);
        updatePositionsTables(positionsData);
        createCharts(chartData);

        // Update status display (last update time, next scheduled update)
        updateStatusDisplay();

        showLoading(false);
        document.getElementById('mainContent').style.display = 'block';
    } catch (error) {
        showError('Failed to load portfolio data: ' + error.message);
        showLoading(false);
    }
}

// Fetch portfolio summary
async function fetchPortfolioSummary() {
    const response = await fetch('/api/portfolio/summary');
    const result = await response.json();

    if (!result.success) {
        throw new Error(result.error || 'Failed to fetch summary');
    }

    return result.data;
}

// Fetch positions
async function fetchPositions() {
    const response = await fetch('/api/portfolio/positions');
    const result = await response.json();

    if (!result.success) {
        throw new Error(result.error || 'Failed to fetch positions');
    }

    positionsData = result.data;
    return result.data;
}

// Fetch chart data
async function fetchChartData() {
    const response = await fetch('/api/portfolio/charts');
    const result = await response.json();

    if (!result.success) {
        throw new Error(result.error || 'Failed to fetch chart data');
    }

    return result.data;
}

// Handle refresh button click
async function handleRefresh() {
    const refreshBtn = document.getElementById('refreshBtn');
    const refreshIcon = document.getElementById('refreshIcon');

    refreshBtn.disabled = true;
    refreshIcon.classList.add('rotating');

    try {
        // Start background update
        const response = await fetch('/api/portfolio/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Failed to start update');
        }

        // Show user feedback
        showError(`Update started! Fetching ${result.total_tickers} tickers in background...`);

        // Poll for status
        await pollUpdateStatus();

        // Reload dashboard with fresh data
        await initializeDashboard();

        // Hide message and show success
        document.getElementById('errorMessage').style.display = 'none';
        console.log('Update completed successfully');

    } catch (error) {
        showError('Failed to refresh data: ' + error.message);
    } finally {
        refreshBtn.disabled = false;
        refreshIcon.classList.remove('rotating');
    }
}

// Poll the update status endpoint
async function pollUpdateStatus() {
    return new Promise((resolve, reject) => {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/portfolio/update/status');
                const result = await response.json();

                if (!result.success) {
                    clearInterval(pollInterval);
                    reject(new Error('Failed to get update status'));
                    return;
                }

                const status = result.status;

                // Update user feedback
                if (status.message) {
                    showError(status.message);
                }

                // Check if complete
                if (!status.running) {
                    clearInterval(pollInterval);
                    if (status.error) {
                        reject(new Error(status.error));
                    } else {
                        resolve();
                    }
                }
            } catch (error) {
                clearInterval(pollInterval);
                reject(error);
            }
        }, 2000); // Poll every 2 seconds
    });
}

// Update status display (last update time and next scheduled update)
async function updateStatusDisplay() {
    try {
        const response = await fetch('/api/portfolio/update/status');
        const result = await response.json();

        if (!result.success) {
            return;
        }

        const status = result.status;

        // Update last update time
        if (status.last_update_time) {
            const lastUpdate = new Date(status.last_update_time);
            document.getElementById('lastUpdateTime').textContent = lastUpdate.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                hour12: true,
                timeZoneName: 'short'
            });
        } else {
            document.getElementById('lastUpdateTime').textContent = 'Not yet updated';
        }

        // Update next scheduled update
        if (status.next_scheduled_update) {
            const nextUpdate = new Date(status.next_scheduled_update);
            const now = new Date();
            const hoursUntil = Math.floor((nextUpdate - now) / (1000 * 60 * 60));
            const minutesUntil = Math.floor(((nextUpdate - now) % (1000 * 60 * 60)) / (1000 * 60));

            let nextUpdateText;
            if (hoursUntil < 0) {
                nextUpdateText = 'Updating soon...';
            } else if (hoursUntil === 0 && minutesUntil < 60) {
                nextUpdateText = `In ${minutesUntil} minute${minutesUntil !== 1 ? 's' : ''}`;
            } else {
                nextUpdateText = nextUpdate.toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                    hour12: true,
                    timeZoneName: 'short'
                });
            }

            document.getElementById('nextUpdateTime').textContent = nextUpdateText;
        }

    } catch (error) {
        console.error('Failed to update status display:', error);
    }
}

// Update summary cards
function updateSummaryCards(data) {
    // Portfolio value
    document.getElementById('portfolioValue').textContent = formatCurrency(data.current_value);
    const changeEl = document.getElementById('portfolioChange');
    changeEl.textContent = formatPercent(data.total_return_pct);
    changeEl.className = 'metric-change ' + ((data.total_return_pct || 0) >= 0 ? 'positive' : 'negative');

    // Total P&L
    const pnlEl = document.getElementById('totalPnL');
    pnlEl.textContent = formatCurrency(data.total_pnl);
    pnlEl.className = 'metric-value ' + ((data.total_pnl || 0) >= 0 ? 'positive' : 'negative');

    document.getElementById('longPnL').textContent = formatCurrency(data.long_pnl);
    document.getElementById('shortPnL').textContent = formatCurrency(data.short_pnl);

    // Sharpe Ratio
    document.getElementById('sharpeRatio').textContent = (data.sharpe_ratio || 0).toFixed(2);

    // Max Drawdown
    document.getElementById('maxDrawdown').textContent = formatPercent(data.max_drawdown);
    document.getElementById('volatility').textContent = formatPercent(data.volatility);

    // Benchmark comparison
    document.getElementById('portfolioReturn').textContent = formatPercent(data.total_return_pct);
    document.getElementById('sp500Return').textContent = formatPercent(data.sp500_return);
    document.getElementById('russell3000Return').textContent = formatPercent(data.russell3000_return);

    const alphaSP500 = (data.total_return_pct || 0) - (data.sp500_return || 0);
    const alphaSP500El = document.getElementById('alphaSP500');
    alphaSP500El.textContent = formatPercent(alphaSP500);
    alphaSP500El.className = 'stat-value ' + (alphaSP500 >= 0 ? 'positive' : 'negative');

    const alphaRussell3000 = (data.total_return_pct || 0) - (data.russell3000_return || 0);
    const alphaRussell3000El = document.getElementById('alphaRussell3000');
    alphaRussell3000El.textContent = formatPercent(alphaRussell3000);
    alphaRussell3000El.className = 'stat-value ' + (alphaRussell3000 >= 0 ? 'positive' : 'negative');
}

// Update best/worst performers
function updatePerformers(data) {
    const bestContainer = document.getElementById('bestPerformers');
    const worstContainer = document.getElementById('worstPerformers');

    const bestPositions = data.best_positions || [];
    const worstPositions = data.worst_positions || [];

    if (bestPositions.length === 0) {
        bestContainer.innerHTML = '<div class="performer-item">No data available yet</div>';
    } else {
        bestContainer.innerHTML = bestPositions.map(pos => `
            <div class="performer-item positive">
                <div>
                    <div class="performer-ticker">${pos.ticker}</div>
                    <div class="performer-return">${formatPercent(pos.total_return_pct)} return</div>
                </div>
                <div class="performer-pnl positive">${formatCurrency(pos.pnl)}</div>
            </div>
        `).join('');
    }

    if (worstPositions.length === 0) {
        worstContainer.innerHTML = '<div class="performer-item">No data available yet</div>';
    } else {
        worstContainer.innerHTML = worstPositions.map(pos => `
            <div class="performer-item negative">
                <div>
                    <div class="performer-ticker">${pos.ticker}</div>
                    <div class="performer-return">${formatPercent(pos.total_return_pct)} return</div>
                </div>
                <div class="performer-pnl negative">${formatCurrency(pos.pnl)}</div>
            </div>
        `).join('');
    }
}

// Update positions tables
function updatePositionsTables(data) {
    renderTable('long', data.long || []);
    renderTable('short', data.short || []);
}

// Render position table
function renderTable(side, positions) {
    const tableId = side === 'long' ? 'longPositionsTable' : 'shortPositionsTable';
    const tbody = document.getElementById(tableId);

    if (positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7">No positions found</td></tr>';
        return;
    }

    tbody.innerHTML = positions.map(pos => `
        <tr>
            <td class="ticker-cell">${pos.ticker}</td>
            <td>${formatCurrency(pos.inception_price)}</td>
            <td>${formatCurrency(pos.current_price)}</td>
            <td class="${pos.total_return_pct >= 0 ? 'positive' : 'negative'}">${formatPercent(pos.total_return_pct)}</td>
            <td>${formatCurrency(pos.position_size)}</td>
            <td>${formatCurrency(pos.current_value)}</td>
            <td class="${pos.pnl >= 0 ? 'positive' : 'negative'}">${formatCurrency(pos.pnl)}</td>
        </tr>
    `).join('');
}

// Filter table by search term
function filterTable(side, searchTerm) {
    const positions = positionsData[side];
    const filtered = positions.filter(pos =>
        pos.ticker.toLowerCase().includes(searchTerm.toLowerCase())
    );
    renderTable(side, filtered);
}

// Sort table
function sortTable(side, sortBy) {
    let positions = [...positionsData[side]];

    switch(sortBy) {
        case 'pnl':
            positions.sort((a, b) => b.pnl - a.pnl);
            break;
        case 'return':
            positions.sort((a, b) => b.total_return_pct - a.total_return_pct);
            break;
        case 'ticker':
            positions.sort((a, b) => a.ticker.localeCompare(b.ticker));
            break;
    }

    renderTable(side, positions);
}

// Switch between tabs
function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === tabName + 'Tab');
    });
}

// Create all charts
function createCharts(data) {
    if (!data || !data.dates || data.dates.length === 0) {
        console.log('No chart data available yet');
        return;
    }

    // Cumulative Returns Chart
    charts.cumulativeReturns = createLineChart(
        'cumulativeReturnsChart',
        data.dates,
        [
            { label: 'Portfolio', data: data.portfolio_returns || [], color: 'rgb(30, 58, 138)' },
            { label: 'S&P 500', data: data.sp500_returns || [], color: 'rgb(156, 163, 175)' },
            { label: 'Russell 3000', data: data.russell3000_returns || [], color: 'rgb(59, 130, 246)' }
        ],
        'Cumulative Return (%)'
    );

    // Portfolio Value Chart
    charts.portfolioValue = createLineChart(
        'portfolioValueChart',
        data.dates,
        [{ label: 'Value', data: data.portfolio_values || [], color: 'rgb(16, 185, 129)' }],
        'Portfolio Value ($)'
    );

    // Daily Returns Chart
    charts.dailyReturns = createBarChart(
        'dailyReturnsChart',
        data.dates,
        data.daily_returns || [],
        'Daily Return (%)'
    );

    // Drawdown Chart
    charts.drawdown = createLineChart(
        'drawdownChart',
        data.dates,
        [{ label: 'Drawdown', data: data.drawdown || [], color: 'rgb(239, 68, 68)' }],
        'Drawdown (%)',
        true
    );
}

// Create line chart
function createLineChart(canvasId, labels, datasets, yLabel, fillArea = false) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    const chartDatasets = datasets.map(ds => ({
        label: ds.label,
        data: ds.data,
        borderColor: ds.color,
        backgroundColor: fillArea ? ds.color.replace('rgb', 'rgba').replace(')', ', 0.1)') : 'transparent',
        borderWidth: 2,
        fill: fillArea,
        tension: 0.1,
        pointRadius: 0
    }));

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: chartDatasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: datasets.length > 1
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    display: true,
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: yLabel
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Create bar chart
function createBarChart(canvasId, labels, data, yLabel) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // Color bars based on positive/negative
    const backgroundColors = data.map(val => val >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)');
    const borderColors = data.map(val => val >= 0 ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)');

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily Return',
                data: data,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y || 0;
                            return value.toFixed(2) + '%';
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: yLabel
                    }
                }
            }
        }
    });
}

// Utility Functions
function formatCurrency(value) {
    if (value === undefined || value === null) return '$0.00';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function formatPercent(value) {
    if (value === undefined || value === null) return '0.00%';
    const sign = value >= 0 ? '+' : '';
    return sign + value.toFixed(2) + '%';
}

function showLoading(show) {
    document.getElementById('loadingSpinner').style.display = show ? 'flex' : 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    document.getElementById('errorText').textContent = message;
    errorDiv.style.display = 'flex';

    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}
