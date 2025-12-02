/**
 * Wispr Flow Complaints Dashboard
 * Interactive visualization of complaints data
 */

// Global state
let data = null;
let timeChart = null;
let barChart = null;
let selectedCategory = null;
let currentTimeRange = 'all';
let selectedSource = null;
let currentDataType = 'complaints'; // 'complaints', 'useCases', 'valueDrivers', or 'magicMoments'
let magicMomentsData = null;

// Data type configuration
const DATA_CONFIG = {
    complaints: {
        file: 'data/complaints.json',
        chartTitle: 'Top Complaints',
        itemsTitle: 'Complaints',
        itemKey: 'complaints'
    },
    useCases: {
        file: 'data/use_cases.json',
        chartTitle: 'Top Use Cases',
        itemsTitle: 'Use Cases',
        itemKey: 'useCases'
    },
    valueDrivers: {
        file: 'data/value_drivers.json',
        chartTitle: 'Top Value Drivers',
        itemsTitle: 'Value Drivers',
        itemKey: 'valueDrivers'
    }
};

// Chart colors - Wispr Flow theme (teal & pink)
const CHART_COLORS = {
    teal: '#034f46',
    tealLight: '#0a7a6d',
    tealLighter: '#1a9a8a',
    pink: '#E8D5E7',
    pinkDark: '#d4b8d3',
    grid: '#e8e8d8',
    text: '#5a5a52',
    textMuted: '#8d8d83'
};

// Generate colors for categories - all teal
function generateCategoryColors(count) {
    const colors = [];
    for (let i = 0; i < count; i++) {
        colors.push(CHART_COLORS.teal);
    }
    return colors;
}

// Initialize dashboard
async function init() {
    // Setup data toggle first
    setupDataToggle();

    // Setup search
    setupSearch();

    // Load initial data
    await loadData(currentDataType);
}

// Load data for the specified type
async function loadData(dataType) {
    const config = DATA_CONFIG[dataType];

    try {
        const response = await fetch(config.file);
        data = await response.json();

        // Normalize data structure - use 'complaints' key for items regardless of type
        // This allows reusing the existing rendering functions
        if (dataType === 'useCases') {
            data.categories.forEach(cat => {
                cat.complaints = cat.useCases || [];
            });
        } else if (dataType === 'valueDrivers') {
            data.categories.forEach(cat => {
                cat.complaints = cat.valueDrivers || [];
            });
        }

        // Update labels
        updateLabels(config);

        // Reset state
        selectedCategory = null;
        selectedBarIndex = null;
        selectedSource = null;
        hoveredBarIndex = null;

        // Destroy existing charts if they exist
        if (timeChart) {
            timeChart.destroy();
            timeChart = null;
        }
        if (barChart) {
            barChart.destroy();
            barChart = null;
        }

        // Initialize charts
        initTimeChart();
        initBarChart();

        // Setup event listeners (only once)
        if (!window.listenersInitialized) {
            setupTimeFilter();
            setupOtherButton();
            setupModal();
            window.listenersInitialized = true;
        } else {
            // Update uncategorized count
            updateUncategorizedCount();
        }

        // Pre-select first category
        const categories = data.categories.filter(c => c.name.toLowerCase() !== 'other');
        if (categories.length > 0) {
            selectCategory(categories[0].name, 0);
        }
    } catch (error) {
        console.error('Failed to load data:', error);
        document.querySelector('.charts-panel').innerHTML =
            `<div class="loading">Failed to load data: ${error.message}</div>`;
    }
}

// Update uncategorized button count
function updateUncategorizedCount() {
    const otherCategory = data.categories.find(c => c.name.toLowerCase() === 'other');
    const countSpan = document.getElementById('uncategorized-count');
    if (otherCategory && countSpan) {
        countSpan.textContent = otherCategory.count;
    } else if (countSpan) {
        countSpan.textContent = '0';
    }
}

// Update UI labels based on data type
function updateLabels(config) {
    document.getElementById('chart-title').textContent = config.chartTitle;
    document.getElementById('items-list-title').textContent = config.itemsTitle;

    // Hide uncategorized button for use cases and value drivers (no "other" category)
    const uncategorizedBtn = document.getElementById('view-uncategorized-btn');
    if (uncategorizedBtn) {
        const hideUncategorized = currentDataType === 'useCases' || currentDataType === 'valueDrivers';
        uncategorizedBtn.style.display = hideUncategorized ? 'none' : 'flex';
    }
}

// Setup data type toggle
function setupDataToggle() {
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    const mainContent = document.querySelector('.main-content');
    const magicMomentsContainer = document.getElementById('magic-moments-container');

    toggleBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            const newType = btn.dataset.type;
            if (newType === currentDataType) return;

            // Update active state
            toggleBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update current type
            currentDataType = newType;

            // Handle Magic Moments specially - no charts, just a list
            if (newType === 'magicMoments') {
                mainContent.style.display = 'none';
                magicMomentsContainer.style.display = 'block';
                await loadMagicMoments();
            } else {
                mainContent.style.display = '';
                magicMomentsContainer.style.display = 'none';
                await loadData(newType);
            }
        });
    });
}

// Initialize time series chart
function initTimeChart() {
    const ctx = document.getElementById('time-chart').getContext('2d');

    // Start with empty datasets - lines will be added on selection/hover
    const datasets = [];

    timeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.timeSeries.labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#ffffff',
                    titleColor: '#1A1A1A',
                    bodyColor: '#5a5a52',
                    borderColor: '#e5e5d6',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    boxWidth: 8,
                    boxHeight: 8,
                    boxPadding: 4
                }
            },
            scales: {
                x: {
                    grid: {
                        color: CHART_COLORS.grid,
                        drawBorder: false
                    },
                    ticks: {
                        color: CHART_COLORS.textMuted,
                        font: { size: 11 }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: CHART_COLORS.grid,
                        drawBorder: false
                    },
                    ticks: {
                        color: CHART_COLORS.textMuted,
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

// Initialize horizontal bar chart
function initBarChart() {
    const ctx = document.getElementById('bar-chart').getContext('2d');

    // Filter out "other" category and get all categories
    const categories = data.categories
        .filter(c => c.name.toLowerCase() !== 'other');

    // Dynamically set container height based on number of categories
    // ~30px per bar to match complaints layout
    const barHeight = 30;
    const containerHeight = Math.max(300, categories.length * barHeight);
    document.querySelector('.bar-chart-container').style.height = `${containerHeight}px`;

    const colors = generateCategoryColors(categories.length);

    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories.map(c => c.name),
            datasets: [{
                data: categories.map(c => c.count),
                backgroundColor: colors,
                borderColor: colors.map(() => 'transparent'),
                borderWidth: colors.map(() => 0),
                borderRadius: 3,
                barThickness: 18,
                categoryPercentage: 0.8,
                barPercentage: 0.9
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#ffffff',
                    titleColor: '#1A1A1A',
                    bodyColor: '#5a5a52',
                    borderColor: '#e5e5d6',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (context) => {
                            const total = context.dataset.data.reduce((sum, val) => sum + val, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            const itemLabel = currentDataType === 'useCases' ? 'use cases' : 'complaints';
                            return `${context.raw} ${itemLabel} (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: CHART_COLORS.grid,
                        drawBorder: false
                    },
                    ticks: {
                        color: CHART_COLORS.textMuted,
                        font: { size: 11 }
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    afterFit: (scale) => {
                        // Fix width to prevent shift when text becomes bold
                        // Different data types have different label lengths
                        const widths = { complaints: 340, useCases: 180, valueDrivers: 220 };
                        scale.width = widths[currentDataType] || 340;
                    },
                    ticks: {
                        autoSkip: false,
                        color: (context) => {
                            if (context.index === selectedBarIndex) {
                                return '#000000'; // Selected = black (darkest)
                            } else if (context.index === hoveredBarIndex) {
                                return '#1A1A1A'; // Hovered = very dark
                            }
                            return CHART_COLORS.text; // Default
                        },
                        font: (context) => {
                            return {
                                size: 15,
                                weight: context.index === selectedBarIndex ? 'bold' : 'normal'
                            };
                        }
                    }
                }
            },
            onHover: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    hoverBar(index);
                } else {
                    clearHover();
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const categoryName = categories[index].name;
                    selectCategory(categoryName, index);
                }
            }
        }
    });

    // Clear hover state when mouse leaves the chart canvas
    ctx.canvas.addEventListener('mouseleave', () => {
        clearHover();
    });
}

// Track hovered bar index
let hoveredBarIndex = null;
let selectedBarIndex = null;

// Get the current start index for time range filtering
function getCurrentStartIndex() {
    if (!data || currentTimeRange === 'all') return 0;

    const rawLabels = data.timeSeries.rawLabels;
    if (!rawLabels || rawLabels.length === 0) return 0;

    const lastLabel = rawLabels[rawLabels.length - 1];
    const [lastYear, lastMonth] = lastLabel.split('-').map(Number);
    const referenceDate = new Date(lastYear, lastMonth - 1, 1);

    let monthsBack;
    switch (currentTimeRange) {
        case '3m': monthsBack = 3; break;
        case '6m': monthsBack = 6; break;
        case '1y': monthsBack = 12; break;
        default: return 0;
    }

    const cutoffDate = new Date(referenceDate.getFullYear(), referenceDate.getMonth() - monthsBack + 1, 1);
    const cutoffStr = cutoffDate.toISOString().slice(0, 7);
    const startIndex = rawLabels.findIndex(label => label >= cutoffStr);
    return startIndex === -1 ? 0 : startIndex;
}

// Hover bar - visual highlight + pink line on time chart
function hoverBar(index) {
    if (!barChart) return;

    // Don't show hover line if hovering the selected bar
    if (index === selectedBarIndex) {
        hoveredBarIndex = null;
        removeHoverLine();
        updateBarColors();
        return;
    }

    hoveredBarIndex = index;
    updateBarColors();

    // Add pink hover line to time chart
    const categories = data.categories.filter(c => c.name.toLowerCase() !== 'other');
    const categoryName = categories[index]?.name;
    if (categoryName && timeChart) {
        addHoverLine(categoryName);
    }
}

// Clear hover
function clearHover() {
    if (!barChart) return;
    hoveredBarIndex = null;
    updateBarColors();
    removeHoverLine();
}

// Add pink hover line to time chart
function addHoverLine(categoryName) {
    if (!timeChart) return;

    const categoryData = data.timeSeries.datasets[categoryName] || [];
    const startIndex = getCurrentStartIndex();
    const filteredData = categoryData.slice(startIndex);

    // Remove existing hover line if present (it's always the last one if there are more than 1 or 2 datasets)
    removeHoverLine();

    // Add the hover line
    timeChart.data.datasets.push({
        label: categoryName + ' (hover)',
        data: filteredData,
        borderColor: CHART_COLORS.tealLighter,
        backgroundColor: CHART_COLORS.tealLighter + '20',
        borderWidth: 3,
        tension: 0.3,
        fill: false,
        pointRadius: 2,
        pointHoverRadius: 4,
        pointBackgroundColor: CHART_COLORS.tealLighter,
        isHoverLine: true  // Custom flag to identify hover line
    });

    timeChart.update('none');
}

// Remove hover line from time chart
function removeHoverLine() {
    if (!timeChart) return;

    // Remove any dataset marked as hover line
    const hoverIndex = timeChart.data.datasets.findIndex(ds => ds.isHoverLine);
    if (hoverIndex !== -1) {
        timeChart.data.datasets.splice(hoverIndex, 1);
        timeChart.update('none');
    }
}

// Update bar colors based on hover and selection state
function updateBarColors() {
    if (!barChart) return;
    const colors = barChart.data.datasets[0].backgroundColor;
    const borderColors = barChart.data.datasets[0].borderColor;
    const borderWidths = barChart.data.datasets[0].borderWidth;
    for (let i = 0; i < colors.length; i++) {
        if (i === selectedBarIndex) {
            colors[i] = CHART_COLORS.pinkDark; // Selected = dark pink
            borderColors[i] = '#000000'; // Black border for selected
            borderWidths[i] = 2;
        } else if (i === hoveredBarIndex) {
            colors[i] = CHART_COLORS.tealLighter; // Hovered = lighter teal
            borderColors[i] = 'transparent';
            borderWidths[i] = 0;
        } else {
            colors[i] = CHART_COLORS.teal; // Default = teal
            borderColors[i] = 'transparent';
            borderWidths[i] = 0;
        }
    }
    barChart.update(); // Full update to re-evaluate scriptable tick options
}

// Select category (click) - shows details
function selectCategory(categoryName, barIndex) {
    // If already selected, do nothing (always keep something selected)
    if (selectedCategory === categoryName) {
        return;
    } else {
        // Deselect "View uncategorized" button if it was selected
        const otherBtn = document.getElementById('view-uncategorized-btn');
        if (otherBtn) {
            otherBtn.classList.remove('active');
        }

        // Select new category
        selectedCategory = categoryName;
        selectedBarIndex = barIndex;

        // Add/update selected category line in time chart
        if (timeChart) {
            const categoryData = data.timeSeries.datasets[categoryName] || [];
            const startIndex = getCurrentStartIndex();
            const filteredData = categoryData.slice(startIndex);

            // Remove existing selected category line if present
            const selectedIndex = timeChart.data.datasets.findIndex(ds => ds.isSelectedLine);
            if (selectedIndex !== -1) {
                timeChart.data.datasets.splice(selectedIndex, 1);
            }

            // Add the selected category line (green)
            timeChart.data.datasets.push({
                label: categoryName,
                data: filteredData,
                borderColor: CHART_COLORS.pinkDark,
                backgroundColor: CHART_COLORS.pinkDark + '20',
                borderWidth: 3,
                tension: 0.3,
                fill: false,
                pointRadius: 3,
                pointHoverRadius: 5,
                pointBackgroundColor: CHART_COLORS.pinkDark,
                isSelectedLine: true  // Custom flag to identify selected line
            });

            timeChart.update('none');
        }

        // Update bar colors
        updateBarColors();

        // Show loading then category details
        showDetailsLoading();
        setTimeout(() => {
            showCategoryDetails(categoryName);
            hideDetailsLoading();
        }, 150);
    }
}

// Show/hide loading indicator
function showDetailsLoading() {
    document.getElementById('details-loading').classList.add('active');
}

function hideDetailsLoading() {
    document.getElementById('details-loading').classList.remove('active');
}

// Show category details in right panel
function showCategoryDetails(categoryName) {
    const category = data.categories.find(c => c.name.toLowerCase() === categoryName.toLowerCase());
    if (!category) return;

    // Update sub-header - show "Uncategorized" for "other" category
    const displayName = category.name.toLowerCase() === 'other' ? 'Uncategorized' : category.name;
    document.getElementById('selected-category-name').textContent = displayName;
    document.getElementById('selected-category-summary').textContent = category.aiSummary;

    // Reset source filter when changing categories
    selectedSource = null;

    // Update source badges and complaints
    updateSourceBadges(category);
    renderComplaints(category);
}

// Update source badges based on time-filtered complaints
function updateSourceBadges(category) {
    const sourceBadges = document.getElementById('source-badges');
    sourceBadges.innerHTML = '';

    const sourceIcons = {
        'reddit': 'icons/reddit.png',
        'appstore': 'icons/appstore.png',
        'producthunt': 'icons/producthunt.png',
        'trustpilot': 'icons/trustpilot.png',
        'microsoft': 'icons/windows.png'
    };

    const sourceNames = {
        'reddit': 'Reddit',
        'appstore': 'App Store',
        'producthunt': 'Product Hunt',
        'trustpilot': 'Trustpilot',
        'microsoft': 'Microsoft'
    };

    // Filter by time first, then count by platform
    const timeFilteredComplaints = filterComplaintsByTime(category.complaints);

    const platformCounts = {};
    timeFilteredComplaints.forEach(complaint => {
        let platform;
        if (complaint.sourceType === 'reddit_content') {
            platform = 'reddit';
        } else {
            platform = (complaint.source.platform || 'unknown').toLowerCase().replace(/\s+/g, '');
        }
        platformCounts[platform] = (platformCounts[platform] || 0) + 1;
    });

    // Sort by count descending
    const sortedPlatforms = Object.entries(platformCounts).sort((a, b) => b[1] - a[1]);

    for (const [platform, count] of sortedPlatforms) {
        const badge = document.createElement('div');
        badge.className = 'source-badge';
        badge.dataset.source = platform;
        if (selectedSource === platform) {
            badge.classList.add('active');
        }
        badge.innerHTML = `
            <img src="${sourceIcons[platform] || 'icons/reddit.png'}" alt="${platform}">
            <span>${sourceNames[platform] || platform}</span>
            <span class="count">${count}</span>
        `;
        badge.addEventListener('click', () => {
            toggleSourceFilter(platform, category);
        });
        sourceBadges.appendChild(badge);
    }
}

// Render complaints list with current filters
function renderComplaints(category) {
    const complaintsList = document.getElementById('complaints-list');
    complaintsList.innerHTML = '';

    // Filter complaints by current time range
    let filteredComplaints = filterComplaintsByTime(category.complaints);

    // Filter by selected source/platform if any
    if (selectedSource) {
        filteredComplaints = filteredComplaints.filter(c => {
            if (selectedSource === 'reddit') {
                return c.sourceType === 'reddit_content';
            } else {
                const platform = (c.source.platform || '').toLowerCase().replace(/\s+/g, '');
                return platform === selectedSource;
            }
        });
    }

    filteredComplaints.slice(0, 50).forEach(complaint => {
        const card = createComplaintCard(complaint);
        complaintsList.appendChild(card);
    });
}

// Toggle source filter
function toggleSourceFilter(source, category) {
    const badges = document.querySelectorAll('.source-badge');

    if (selectedSource === source) {
        // Deselect - show all sources
        selectedSource = null;
        badges.forEach(b => b.classList.remove('active'));
    } else {
        // Select this source
        selectedSource = source;
        badges.forEach(b => {
            if (b.dataset.source === source) {
                b.classList.add('active');
            } else {
                b.classList.remove('active');
            }
        });
    }

    // Re-render complaints with new filter
    renderComplaints(category);
}

// Create complaint card element
function createComplaintCard(complaint) {
    const card = document.createElement('div');
    card.className = 'complaint-card';

    const source = complaint.source;
    const isReddit = complaint.sourceType === 'reddit_content';

    // Format date
    const date = complaint.date ? new Date(complaint.date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    }) : '';

    // Build body text with quote in context
    let bodyText = '';
    const fullBody = source.body || '';
    const quote = complaint.quote || '';
    const maxTotalChars = 300; // max characters per card

    if (quote && fullBody) {
        // Find quote position in body (case-insensitive)
        const lowerBody = fullBody.toLowerCase();
        const lowerQuote = quote.toLowerCase();
        const quoteIndex = lowerBody.indexOf(lowerQuote);

        if (quoteIndex !== -1) {
            // Calculate remaining chars for context (after quote is included)
            const remainingChars = Math.max(0, maxTotalChars - quote.length);

            // Available text before and after quote
            const availableBefore = quoteIndex;
            const availableAfter = fullBody.length - (quoteIndex + quote.length);

            // Distribute remaining chars proportionally, but prefer showing more context
            let charsBefore, charsAfter;
            if (availableBefore + availableAfter <= remainingChars) {
                // Enough room for everything
                charsBefore = availableBefore;
                charsAfter = availableAfter;
            } else {
                // Need to truncate - split remaining chars evenly, but adjust if one side has less
                const halfRemaining = Math.floor(remainingChars / 2);
                if (availableBefore <= halfRemaining) {
                    charsBefore = availableBefore;
                    charsAfter = Math.min(availableAfter, remainingChars - charsBefore);
                } else if (availableAfter <= halfRemaining) {
                    charsAfter = availableAfter;
                    charsBefore = Math.min(availableBefore, remainingChars - charsAfter);
                } else {
                    charsBefore = halfRemaining;
                    charsAfter = halfRemaining;
                }
            }

            const startIndex = quoteIndex - charsBefore;
            const endIndex = quoteIndex + quote.length + charsAfter;

            // Extract the actual quote from body (preserving original case)
            const actualQuote = fullBody.substring(quoteIndex, quoteIndex + quote.length);

            // Build text with context
            let before = fullBody.substring(startIndex, quoteIndex);
            let after = fullBody.substring(quoteIndex + quote.length, endIndex);

            // Trim to word boundaries and add ellipsis
            let prefix = '';
            let suffix = '';

            if (startIndex > 0) {
                prefix = '...';
                const firstSpace = before.indexOf(' ');
                if (firstSpace >= 0) before = before.substring(firstSpace + 1);
            }
            if (endIndex < fullBody.length) {
                suffix = '...';
                const lastSpace = after.lastIndexOf(' ');
                if (lastSpace > 0) after = after.substring(0, lastSpace);
            }

            bodyText = `${prefix}${before}<mark>${actualQuote}</mark>${after}${suffix}`;
        } else {
            // Quote not found in body, just show the quote
            bodyText = `<mark>${quote}</mark>`;
        }
    } else if (quote) {
        // No body, just show quote
        bodyText = `<mark>${quote}</mark>`;
    } else if (fullBody) {
        // No quote, truncate body from end
        if (fullBody.length > maxTotalChars) {
            const truncated = fullBody.substring(0, maxTotalChars);
            const lastSpace = truncated.lastIndexOf(' ');
            bodyText = truncated.substring(0, lastSpace) + '...';
        } else {
            bodyText = fullBody;
        }
    }

    // Build meta info
    let metaHtml = '';
    if (isReddit) {
        const upvotes = source.upvotes || source.score || 0;
        metaHtml = `
            <span class="complaint-source">${source.type === 'post' ? 'Post' : 'Comment'}</span>
            ${source.community ? `<span class="complaint-community">${source.community}</span>` : ''}
            <span class="complaint-upvotes">▲ ${upvotes}</span>
        `;
    } else {
        metaHtml = `
            <span class="complaint-source">${source.platform || 'Review'}</span>
            ${source.rating ? `<span class="complaint-rating">${'★'.repeat(source.rating)}${'☆'.repeat(5 - source.rating)}</span>` : ''}
        `;
    }

    card.innerHTML = `
        <div class="complaint-header">
            <img src="icons/${complaint.icon}" alt="" class="complaint-icon">
            <div class="complaint-meta">
                ${metaHtml}
                <span class="complaint-date">${date}</span>
            </div>
        </div>
        ${source.title ? `<div class="complaint-title">${source.title}</div>` : ''}
        <div class="complaint-body">${bodyText}</div>
        ${source.url ? `<a href="${source.url}" target="_blank" rel="noopener" class="complaint-link">View original →</a>` : ''}
    `;

    return card;
}

// Filter complaints by time range
function filterComplaintsByTime(complaints) {
    if (currentTimeRange === 'all') return complaints;

    const now = new Date();
    let cutoffDate;

    switch (currentTimeRange) {
        case '3m':
            cutoffDate = new Date(now.setMonth(now.getMonth() - 3));
            break;
        case '6m':
            cutoffDate = new Date(now.setMonth(now.getMonth() - 6));
            break;
        case '1y':
            cutoffDate = new Date(now.setFullYear(now.getFullYear() - 1));
            break;
        default:
            return complaints;
    }

    return complaints.filter(c => {
        if (!c.date) return true;
        return new Date(c.date) >= cutoffDate;
    });
}

// Setup time filter buttons
function setupTimeFilter() {
    const buttons = document.querySelectorAll('.filter-btn');

    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update time range
            currentTimeRange = btn.dataset.range;

            // Update charts
            updateChartsForTimeRange();

            // Update details panel if category selected (without resetting source filter)
            if (selectedCategory) {
                const category = data.categories.find(c => c.name.toLowerCase() === selectedCategory.toLowerCase());
                if (category) {
                    // Update source badges and complaints list
                    updateSourceBadges(category);
                    renderComplaints(category);
                }
            }
        });
    });
}

// Setup "Other" category button
function setupOtherButton() {
    const btn = document.getElementById('view-uncategorized-btn');
    const countSpan = document.getElementById('uncategorized-count');

    // Find "other" category and set count
    const otherCategory = data.categories.find(c => c.name.toLowerCase() === 'other');
    if (otherCategory && countSpan) {
        countSpan.textContent = otherCategory.count;
    }

    // Hover handlers - show line on time chart
    btn.addEventListener('mouseenter', () => {
        if (selectedCategory !== 'other') {
            const otherCat = data.categories.find(c => c.name.toLowerCase() === 'other');
            if (otherCat) {
                addHoverLine(otherCat.name);
            }
        }
    });

    btn.addEventListener('mouseleave', () => {
        removeHoverLine();
    });

    // Click handler
    btn.addEventListener('click', () => {
        selectOtherCategory();
    });
}

// Select "Other" category
function selectOtherCategory() {
    const btn = document.getElementById('view-uncategorized-btn');
    const otherCategory = data.categories.find(c => c.name.toLowerCase() === 'other');

    if (!otherCategory) return;

    // If "other" is already selected, do nothing (always keep something selected)
    if (selectedCategory === 'other') {
        return;
    }

    // Deselect current bar selection
    selectedBarIndex = null;
    updateBarColors();

    // Update button state
    btn.classList.add('active');

    // Update selected category
    selectedCategory = 'other';

    // Add green line to time chart for "other"
    if (timeChart) {
        // Find the correct category name (handle case sensitivity)
        const otherCat = data.categories.find(c => c.name.toLowerCase() === 'other');
        const otherKey = otherCat ? otherCat.name : 'other';
        const categoryData = data.timeSeries.datasets[otherKey] || [];
        const startIndex = getCurrentStartIndex();
        const filteredData = categoryData.slice(startIndex);

        // Remove existing selected category line if present
        const selectedIndex = timeChart.data.datasets.findIndex(ds => ds.isSelectedLine);
        if (selectedIndex !== -1) {
            timeChart.data.datasets.splice(selectedIndex, 1);
        }

        // Add the selected category line (green)
        timeChart.data.datasets.push({
            label: otherKey,
            data: filteredData,
            borderColor: CHART_COLORS.pinkDark,
            backgroundColor: CHART_COLORS.pinkDark + '20',
            borderWidth: 3,
            tension: 0.3,
            fill: false,
            pointRadius: 3,
            pointHoverRadius: 5,
            pointBackgroundColor: CHART_COLORS.pinkDark,
            isSelectedLine: true
        });

        timeChart.update('none');
    }

    // Show loading then category details
    showDetailsLoading();
    setTimeout(() => {
        showCategoryDetails('other');
        hideDetailsLoading();
    }, 150);
}

// Update charts based on time range
function updateChartsForTimeRange() {
    if (!data) return;

    // Clear hover state when changing time range
    removeHoverLine();
    hoveredBarIndex = null;

    // Determine which months to include based on the data's date range
    const rawLabels = data.timeSeries.rawLabels;
    let startIndex = 0;

    if (currentTimeRange !== 'all' && rawLabels && rawLabels.length > 0) {
        // Use the most recent date in the data as the reference point
        const lastLabel = rawLabels[rawLabels.length - 1];
        const [lastYear, lastMonth] = lastLabel.split('-').map(Number);
        const referenceDate = new Date(lastYear, lastMonth - 1, 1);

        let monthsBack;
        switch (currentTimeRange) {
            case '3m':
                monthsBack = 3;
                break;
            case '6m':
                monthsBack = 6;
                break;
            case '1y':
                monthsBack = 12;
                break;
            default:
                monthsBack = 0;
        }

        const cutoffDate = new Date(referenceDate.getFullYear(), referenceDate.getMonth() - monthsBack + 1, 1);
        const cutoffStr = cutoffDate.toISOString().slice(0, 7);
        startIndex = rawLabels.findIndex(label => label >= cutoffStr);
        if (startIndex === -1) startIndex = 0;
    }

    // Update time chart labels
    const filteredLabels = data.timeSeries.labels.slice(startIndex);
    timeChart.data.labels = filteredLabels;

    // Update selected category line if present
    const selectedLine = timeChart.data.datasets.find(ds => ds.isSelectedLine);
    if (selectedLine && selectedCategory) {
        // Find the correct category name (handle case sensitivity)
        const categoryObj = data.categories.find(c => c.name.toLowerCase() === selectedCategory.toLowerCase());
        const categoryKey = categoryObj ? categoryObj.name : selectedCategory;
        const categoryData = data.timeSeries.datasets[categoryKey] || [];
        selectedLine.data = categoryData.slice(startIndex);
    }

    timeChart.update();

    // Recalculate bar chart counts
    const categories = data.categories
        .filter(c => c.name.toLowerCase() !== 'other')
        ;

    const newCounts = categories.map(cat => {
        const filtered = filterComplaintsByTime(cat.complaints);
        return filtered.length;
    });

    barChart.data.datasets[0].data = newCounts;
    barChart.update();
}

// Setup modal functionality
function setupModal() {
    const expandBtn = document.getElementById('expand-complaints-btn');
    const modal = document.getElementById('complaints-modal');
    const closeBtn = document.getElementById('modal-close-btn');

    // Open modal
    expandBtn.addEventListener('click', () => {
        openComplaintsModal();
    });

    // Close modal on X button
    closeBtn.addEventListener('click', () => {
        closeComplaintsModal();
    });

    // Close modal on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeComplaintsModal();
        }
    });

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeComplaintsModal();
        }
    });
}

// Open complaints modal
function openComplaintsModal() {
    const modal = document.getElementById('complaints-modal');
    const modalCategoryName = document.getElementById('modal-category-name');
    const modalSources = document.getElementById('modal-sources');
    const modalComplaintsList = document.getElementById('modal-complaints-list');

    // Get current category
    const category = data.categories.find(c => c.name === selectedCategory);
    if (!category) return;

    // Filter complaints by time
    const timeFilteredComplaints = filterComplaintsByTime(category.complaints);
    const totalComplaints = timeFilteredComplaints.length;

    // Calculate percentage of all complaints across all categories
    const allCategoriesTotal = data.categories.reduce((sum, cat) => {
        return sum + filterComplaintsByTime(cat.complaints).length;
    }, 0);
    const categoryPercentage = ((totalComplaints / allCategoriesTotal) * 100).toFixed(1);

    // Set category name with count and percentage
    const itemLabel = currentDataType === 'useCases' ? 'use cases' : 'complaints';
    modalCategoryName.textContent = `${category.name} — ${totalComplaints} ${itemLabel} (${categoryPercentage}%)`;

    // Build source badges with percentages
    modalSources.innerHTML = '';
    const sourceIcons = {
        'reddit': 'icons/reddit.png',
        'appstore': 'icons/appstore.png',
        'producthunt': 'icons/producthunt.png',
        'trustpilot': 'icons/trustpilot.png',
        'microsoft': 'icons/windows.png'
    };
    const sourceNames = {
        'reddit': 'Reddit',
        'appstore': 'App Store',
        'producthunt': 'Product Hunt',
        'trustpilot': 'Trustpilot',
        'microsoft': 'Microsoft'
    };

    // Count by platform
    const platformCounts = {};
    timeFilteredComplaints.forEach(complaint => {
        let platform;
        if (complaint.sourceType === 'reddit_content') {
            platform = 'reddit';
        } else {
            platform = (complaint.source.platform || 'unknown').toLowerCase().replace(/\s+/g, '');
        }
        platformCounts[platform] = (platformCounts[platform] || 0) + 1;
    });

    // Sort by count descending
    const sortedPlatforms = Object.entries(platformCounts).sort((a, b) => b[1] - a[1]);

    for (const [platform, count] of sortedPlatforms) {
        const badge = document.createElement('div');
        badge.className = 'source-badge';
        badge.dataset.source = platform;
        if (selectedSource === platform) {
            badge.classList.add('active');
        }
        badge.innerHTML = `
            <img src="${sourceIcons[platform] || 'icons/reddit.png'}" alt="${platform}">
            <span>${sourceNames[platform] || platform}</span>
            <span class="count">${count}</span>
        `;
        badge.addEventListener('click', () => {
            // Toggle selection
            if (selectedSource === platform) {
                selectedSource = null;
                modalSources.querySelectorAll('.source-badge').forEach(b => b.classList.remove('active'));
            } else {
                selectedSource = platform;
                modalSources.querySelectorAll('.source-badge').forEach(b => {
                    b.classList.toggle('active', b.dataset.source === platform);
                });
            }
            // Re-render modal complaints
            renderModalComplaints(category);
            // Also update main panel
            document.querySelectorAll('#source-badges .source-badge').forEach(b => {
                b.classList.toggle('active', b.dataset.source === selectedSource);
            });
            renderComplaints(category);
        });
        modalSources.appendChild(badge);
    }

    // Render complaints in modal (show all, not limited to 50)
    renderModalComplaints(category);

    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Render complaints in modal
function renderModalComplaints(category) {
    const modalComplaintsList = document.getElementById('modal-complaints-list');
    modalComplaintsList.innerHTML = '';

    // Filter complaints by current time range
    let filteredComplaints = filterComplaintsByTime(category.complaints);

    // Filter by selected source/platform if any
    if (selectedSource) {
        filteredComplaints = filteredComplaints.filter(c => {
            if (selectedSource === 'reddit') {
                return c.sourceType === 'reddit_content';
            } else {
                const platform = (c.source.platform || '').toLowerCase().replace(/\s+/g, '');
                return platform === selectedSource;
            }
        });
    }

    // Show all complaints in modal (no limit)
    filteredComplaints.forEach(complaint => {
        const card = createComplaintCard(complaint);
        modalComplaintsList.appendChild(card);
    });
}

// Close complaints modal
function closeComplaintsModal() {
    const modal = document.getElementById('complaints-modal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// ============ SEARCH FUNCTIONALITY ============

// Sources data (loaded separately from complaints/use cases)
let sourcesData = null;
let selectedSearchSource = null; // 'posts', 'comments', or platform name like 'appstore'

const SOURCE_ICONS = {
    'reddit': 'icons/reddit.png',
    'appstore': 'icons/appstore.png',
    'producthunt': 'icons/producthunt.png',
    'trustpilot': 'icons/trustpilot.png',
    'microsoft': 'icons/windows.png'
};

const SOURCE_NAMES = {
    'reddit': 'Reddit',
    'appstore': 'App Store',
    'producthunt': 'Product Hunt',
    'trustpilot': 'Trustpilot',
    'microsoft': 'Microsoft'
};

// Load sources data for search
async function loadSourcesData() {
    if (sourcesData) return sourcesData;

    try {
        const response = await fetch('data/sources.json');
        sourcesData = await response.json();
        return sourcesData;
    } catch (error) {
        console.error('Failed to load sources data:', error);
        return null;
    }
}


// Count sources from search results (handles both raw sources and { item, matches } format)
function countSearchSources(results) {
    const counts = {
        posts: 0,
        comments: 0,
        reviews: 0
    };

    // Also count by platform
    const platformCounts = {};

    for (const result of results) {
        // Handle both raw source and { item, matches } format
        const source = result.item || result;

        if (source.type === 'reddit') {
            if (source.contentType === 'post') {
                counts.posts++;
            } else {
                counts.comments++;
            }
            platformCounts['reddit'] = (platformCounts['reddit'] || 0) + 1;
        } else {
            counts.reviews++;
            const platform = source.platform || 'unknown';
            platformCounts[platform] = (platformCounts[platform] || 0) + 1;
        }
    }

    return { counts, platformCounts };
}

// Search across all sources (case-insensitive substring match)
function searchSources(query, limit = 50) {
    if (!sourcesData) return [];

    const sources = sourcesData.sources || [];

    if (!query || query.length < 2) {
        return sources.map(s => ({ item: s }));
    }

    const lowerQuery = query.toLowerCase();
    const results = [];

    for (const source of sources) {
        const title = (source.title || '').toLowerCase();
        const body = (source.body || '').toLowerCase();

        if (title.includes(lowerQuery) || body.includes(lowerQuery)) {
            results.push({ item: source });
            if (results.length >= limit) break;
        }
    }

    return results;
}

// Highlight matching text in search results
function highlightSearchMatch(text, query) {
    if (!text) return '';
    if (!query || query.length < 2) {
        const maxLength = 250;
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    const maxLength = 300;
    const lowerText = text.toLowerCase();
    const lowerQuery = query.toLowerCase();

    // Find match position
    const matchIndex = lowerText.indexOf(lowerQuery);

    let truncated;
    if (matchIndex !== -1 && text.length > maxLength) {
        // Show context around match
        const start = Math.max(0, matchIndex - 50);
        const end = Math.min(text.length, matchIndex + query.length + 200);
        truncated = (start > 0 ? '...' : '') + text.substring(start, end) + (end < text.length ? '...' : '');
    } else {
        truncated = text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    // Highlight the match
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return truncated.replace(regex, '<mark>$1</mark>');
}

// Escape HTML special characters
function escapeHtml(str) {
    const htmlEscapes = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };
    return str.replace(/[&<>"']/g, char => htmlEscapes[char]);
}

// Escape special regex characters
function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Render source badges in search modal
function renderSearchSources(sources) {
    const container = document.getElementById('search-modal-sources');
    const { counts, platformCounts } = countSearchSources(sources);

    // Build badges HTML
    let html = '';

    // Posts badge
    if (counts.posts > 0) {
        const isActive = selectedSearchSource === 'posts' ? 'active' : '';
        html += `
            <button class="search-source-badge ${isActive}" data-source-filter="posts">
                <img src="icons/reddit.png" alt="Posts">
                <span>Posts</span>
                <span class="count">${counts.posts}</span>
            </button>
        `;
    }

    // Comments badge
    if (counts.comments > 0) {
        const isActive = selectedSearchSource === 'comments' ? 'active' : '';
        html += `
            <button class="search-source-badge ${isActive}" data-source-filter="comments">
                <img src="icons/reddit.png" alt="Comments">
                <span>Comments</span>
                <span class="count">${counts.comments}</span>
            </button>
        `;
    }

    // Review badges by platform
    for (const [platform, count] of Object.entries(platformCounts)) {
        if (platform === 'reddit') continue; // Already shown as posts/comments
        const isActive = selectedSearchSource === platform ? 'active' : '';
        html += `
            <button class="search-source-badge ${isActive}" data-source-filter="${platform}">
                <img src="${SOURCE_ICONS[platform] || 'icons/reddit.png'}" alt="${platform}">
                <span>${SOURCE_NAMES[platform] || platform}</span>
                <span class="count">${count}</span>
            </button>
        `;
    }

    container.innerHTML = html;

    // Add click handlers to badges
    container.querySelectorAll('.search-source-badge').forEach(badge => {
        badge.addEventListener('click', () => {
            const filter = badge.dataset.sourceFilter;

            // Toggle filter (click again to deselect)
            if (selectedSearchSource === filter) {
                selectedSearchSource = null;
            } else {
                selectedSearchSource = filter;
            }

            // Re-run current search with filter
            triggerSearchWithFilter();
        });
    });
}

// Filter results by selected source
function filterBySource(results) {
    if (!selectedSearchSource) return results;

    return results.filter(result => {
        const source = result.item || result;

        if (selectedSearchSource === 'posts') {
            return source.type === 'reddit' && source.contentType === 'post';
        } else if (selectedSearchSource === 'comments') {
            return source.type === 'reddit' && source.contentType === 'comment';
        } else {
            // Platform filter (appstore, trustpilot, etc.)
            return source.platform === selectedSearchSource;
        }
    });
}

// Trigger search with current query and source filter
function triggerSearchWithFilter() {
    const input = document.getElementById('search-modal-input');
    const query = input.value.trim();

    const results = searchSources(query);
    const filteredResults = filterBySource(results);

    renderSearchSources(results); // Show all counts
    renderSearchModalResults(filteredResults, query);
}

// Render search results in modal (like complaint cards)
function renderSearchModalResults(results, query) {
    const container = document.getElementById('search-modal-results');

    if (results.length === 0) {
        container.innerHTML = '<div class="search-no-results">No results found</div>';
        return;
    }

    container.innerHTML = results.map(result => {
        // Handle both raw source and { item } format
        const source = result.item || result;

        const isReddit = source.type === 'reddit';
        const platform = isReddit ? 'reddit' : (source.platform || 'unknown');

        // Format date
        const date = source.date ? new Date(source.date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        }) : '';

        // Build content with highlighting
        const highlightedBody = highlightSearchMatch(source.body, query);
        const highlightedTitle = source.title ? highlightSearchMatch(source.title, query) : '';

        // Build meta info
        let metaHtml = '';
        if (isReddit) {
            metaHtml = `
                <span class="search-result-type">${source.contentType === 'post' ? 'Post' : 'Comment'}</span>
                ${source.community ? `<span class="search-result-community">${source.community}</span>` : ''}
                <span class="search-result-upvotes">▲ ${source.upvotes || 0}</span>
            `;
        } else {
            metaHtml = `
                <span class="search-result-type">${SOURCE_NAMES[platform] || platform}</span>
                ${source.rating ? `<span class="search-result-rating">${'★'.repeat(source.rating)}${'☆'.repeat(5 - source.rating)}</span>` : ''}
            `;
        }

        return `
            <div class="search-result-card">
                <div class="search-result-header">
                    <img src="${SOURCE_ICONS[platform] || 'icons/reddit.png'}" alt="${platform}" class="search-result-icon">
                    <div class="search-result-meta">
                        ${metaHtml}
                        <span class="search-result-date">${date}</span>
                    </div>
                </div>
                ${highlightedTitle ? `<div class="search-result-title">${highlightedTitle}</div>` : ''}
                <div class="search-result-body">${highlightedBody}</div>
                ${source.url ? `<a href="${source.url}" target="_blank" rel="noopener" class="search-result-link">View original →</a>` : ''}
            </div>
        `;
    }).join('');
}

// Open search modal
async function openSearchModal() {
    const modal = document.getElementById('search-modal');
    const input = document.getElementById('search-modal-input');
    const resultsContainer = document.getElementById('search-modal-results');

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Show loading state
    resultsContainer.innerHTML = '<div class="search-modal-placeholder">Loading sources...</div>';

    // Load sources data if not already loaded
    await loadSourcesData();

    if (sourcesData) {
        // Show ALL sources in counts, but only first 50 in results
        const allSources = sourcesData.sources.map(s => ({ item: s }));
        const filteredSources = filterBySource(allSources);
        const displaySources = filteredSources.slice(0, 50);

        renderSearchSources(allSources); // Show all counts
        renderSearchModalResults(displaySources, '');

        // Update autocomplete suggestion counts
        updateAutocompleteCounts();
    } else {
        resultsContainer.innerHTML = '<div class="search-no-results">Failed to load sources data</div>';
    }

    // Focus input
    setTimeout(() => input.focus(), 100);
}

// Count how many sources match a query
function countSourceMatches(query) {
    if (!sourcesData) return 0;

    const lowerQuery = query.toLowerCase();
    let count = 0;

    for (const source of sourcesData.sources) {
        const title = (source.title || '').toLowerCase();
        const body = (source.body || '').toLowerCase();

        if (title.includes(lowerQuery) || body.includes(lowerQuery)) {
            count++;
        }
    }

    return count;
}

// Update counts for all autocomplete suggestions
function updateAutocompleteCounts() {
    const countElements = document.querySelectorAll('.option-count[data-count-for]');

    countElements.forEach(el => {
        const query = el.dataset.countFor;
        const count = countSourceMatches(query);
        el.textContent = count;
    });
}

// Close search modal
function closeSearchModal() {
    const modal = document.getElementById('search-modal');
    const input = document.getElementById('search-modal-input');
    const autocomplete = document.getElementById('search-autocomplete');

    modal.classList.remove('active');
    document.body.style.overflow = '';
    input.value = '';

    // Reset autocomplete visibility for next open
    autocomplete.classList.remove('hidden');

    // Reset source filter
    selectedSearchSource = null;
}

// Perform search and update UI
function performSearch(query) {
    const input = document.getElementById('search-modal-input');
    const autocomplete = document.getElementById('search-autocomplete');

    // Update input value
    input.value = query;

    // Hide autocomplete when searching
    if (query.trim()) {
        autocomplete.classList.add('hidden');
    } else {
        autocomplete.classList.remove('hidden');
    }

    // Perform search with source filter
    const results = searchSources(query);
    const filteredResults = filterBySource(results);

    renderSearchSources(results); // Show all counts
    renderSearchModalResults(filteredResults, query);
}

// Setup search functionality
function setupSearch() {
    const trigger = document.getElementById('search-trigger');
    const modal = document.getElementById('search-modal');
    const closeBtn = document.getElementById('search-modal-close');
    const input = document.getElementById('search-modal-input');
    const autocomplete = document.getElementById('search-autocomplete');
    const autocompleteOptions = document.querySelectorAll('.autocomplete-option');

    let debounceTimer;
    let selectedIndex = -1;

    // Open modal on trigger click
    trigger.addEventListener('click', openSearchModal);

    // Close modal
    closeBtn.addEventListener('click', closeSearchModal);

    // Close on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeSearchModal();
        }
    });

    // Prevent blur when clicking autocomplete options
    autocomplete.addEventListener('mousedown', (e) => {
        e.preventDefault();
    });

    // Autocomplete option clicks
    autocompleteOptions.forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.dataset.query;
            performSearch(query);
            input.focus();
        });
    });

    // Show autocomplete on focus (if input is empty)
    input.addEventListener('focus', () => {
        if (!input.value.trim()) {
            autocomplete.classList.remove('hidden');
        }
    });

    // Hide autocomplete on blur
    input.addEventListener('blur', () => {
        autocomplete.classList.add('hidden');
    });

    // Keyboard navigation for autocomplete
    input.addEventListener('keydown', (e) => {
        if (autocomplete.classList.contains('hidden')) return;

        const options = Array.from(autocompleteOptions);

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, options.length - 1);
            updateAutocompleteSelection(options, selectedIndex);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, -1);
            updateAutocompleteSelection(options, selectedIndex);
        } else if (e.key === 'Enter' && selectedIndex >= 0) {
            e.preventDefault();
            const query = options[selectedIndex].dataset.query;
            performSearch(query);
        }
    });

    // Close on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeSearchModal();
        }
    });

    // Search input handler
    input.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        // Show/hide autocomplete
        if (query) {
            autocomplete.classList.add('hidden');
        } else {
            autocomplete.classList.remove('hidden');
            selectedIndex = -1;
            updateAutocompleteSelection(Array.from(autocompleteOptions), -1);
        }

        clearTimeout(debounceTimer);

        debounceTimer = setTimeout(() => {
            const results = searchSources(query);
            const filteredResults = filterBySource(results);

            renderSearchSources(results); // Show all counts
            renderSearchModalResults(filteredResults, query);
        }, 150);
    });
}

// Update autocomplete selection highlight
function updateAutocompleteSelection(options, index) {
    options.forEach((opt, i) => {
        opt.classList.toggle('selected', i === index);
    });
}

// ============ MAGIC MOMENTS FUNCTIONALITY ============

// Load magic moments data
async function loadMagicMoments() {
    const listContainer = document.getElementById('magic-moments-list');
    const countSpan = document.getElementById('magic-moments-count');

    // Show loading state
    listContainer.innerHTML = '<div class="loading-spinner"></div>';

    try {
        if (!magicMomentsData) {
            const response = await fetch('data/magic_moments.json');
            magicMomentsData = await response.json();
        }

        const moments = magicMomentsData.moments || [];
        // Filter to only show moments with body text less than 300 characters
        const filteredMoments = moments.filter(m => {
            const body = m.source?.body || m.quote || '';
            return body.length < 300;
        });
        countSpan.textContent = `${filteredMoments.length} moments`;

        renderMagicMoments(filteredMoments);
    } catch (error) {
        console.error('Failed to load magic moments:', error);
        listContainer.innerHTML = `<div class="search-no-results">Failed to load magic moments: ${error.message}</div>`;
    }
}

// Render magic moments cards
function renderMagicMoments(moments) {
    const listContainer = document.getElementById('magic-moments-list');

    if (moments.length === 0) {
        listContainer.innerHTML = '<div class="search-no-results">No magic moments found</div>';
        return;
    }

    listContainer.innerHTML = moments.map(moment => {
        const source = moment.source || {};
        const isReddit = moment.sourceType === 'reddit_content';

        // Format date
        const date = moment.date ? new Date(moment.date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        }) : '';

        // Show the full body text
        const fullBody = source.body || moment.quote || '';

        // Build meta info
        let metaHtml = '';
        if (isReddit) {
            const upvotes = source.upvotes || 0;
            metaHtml = `
                <span class="magic-moment-type">${source.type === 'post' ? 'Post' : 'Comment'}</span>
                ${source.community ? `<span class="magic-moment-community">${source.community}</span>` : ''}
                <span class="magic-moment-upvotes">▲ ${upvotes}</span>
            `;
        } else {
            metaHtml = `
                <span class="magic-moment-type">${source.platform || 'Review'}</span>
                ${source.rating ? `<span class="magic-moment-rating">${'★'.repeat(source.rating)}${'☆'.repeat(5 - source.rating)}</span>` : ''}
            `;
        }

        return `
            <div class="magic-moment-card">
                <div class="magic-moment-header">
                    <img src="icons/${moment.icon}" alt="" class="magic-moment-icon">
                    <div class="magic-moment-meta">
                        ${metaHtml}
                        <span class="magic-moment-date">${date}</span>
                    </div>
                </div>
                <div class="magic-moment-body">${escapeHtml(fullBody)}</div>
                ${source.url ? `<a href="${source.url}" target="_blank" rel="noopener" class="magic-moment-link">View original →</a>` : ''}
            </div>
        `;
    }).join('');
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
