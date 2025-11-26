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
    try {
        const response = await fetch('data/complaints.json');
        data = await response.json();

        // Update stats
        document.getElementById('total-complaints').textContent = data.meta.totalComplaints;
        document.getElementById('total-categories').textContent = data.meta.totalCategories;

        // Initialize charts
        initTimeChart();
        initBarChart();

        // Setup event listeners
        setupTimeFilter();
        setupOtherButton();

        // Pre-select first category
        const categories = data.categories.filter(c => c.name.toLowerCase() !== 'other');
        if (categories.length > 0) {
            selectCategory(categories[0].name, 0);
        }
    } catch (error) {
        console.error('Failed to load data:', error);
        document.querySelector('.charts-panel').innerHTML =
            '<div class="loading">Failed to load data. Please run generate_data.py first.</div>';
    }
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

    const colors = generateCategoryColors(categories.length);

    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories.map(c => c.name),
            datasets: [{
                data: categories.map(c => c.count),
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 0,
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
                        label: (context) => `${context.raw} complaints`
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
        borderColor: CHART_COLORS.pink,
        backgroundColor: CHART_COLORS.pink + '20',
        borderWidth: 3,
        tension: 0.3,
        fill: false,
        pointRadius: 2,
        pointHoverRadius: 4,
        pointBackgroundColor: CHART_COLORS.pink,
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
    for (let i = 0; i < colors.length; i++) {
        if (i === selectedBarIndex) {
            colors[i] = CHART_COLORS.green; // Selected = green
        } else if (i === hoveredBarIndex) {
            colors[i] = CHART_COLORS.pink; // Hovered = pink
        } else {
            colors[i] = CHART_COLORS.teal; // Default = teal
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
        // Deselect "Other" button if it was selected
        const otherBtn = document.getElementById('other-category-btn');
        const otherLabel = document.getElementById('other-label');
        if (otherBtn) {
            otherBtn.classList.remove('active');
            if (otherLabel) otherLabel.textContent = 'View uncategorized';
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
                borderColor: CHART_COLORS.green,
                backgroundColor: CHART_COLORS.green + '20',
                borderWidth: 3,
                tension: 0.3,
                fill: false,
                pointRadius: 3,
                pointHoverRadius: 5,
                pointBackgroundColor: CHART_COLORS.green,
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
    const timeFilteredComplaints = filterComplaintsByTime(category.complaints);
    document.getElementById('selected-category-name').textContent = displayName;
    document.getElementById('selected-category-count').textContent = `${timeFilteredComplaints.length} complaints`;
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
                    // Update complaint count in sub-header
                    const timeFilteredComplaints = filterComplaintsByTime(category.complaints);
                    document.getElementById('selected-category-count').textContent = `${timeFilteredComplaints.length} complaints`;

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
    const btn = document.getElementById('other-category-btn');
    const tooltip = document.getElementById('other-tooltip');

    // Find "other" category and set tooltip content
    const otherCategory = data.categories.find(c => c.name.toLowerCase() === 'other');
    if (otherCategory) {
        tooltip.textContent = `${otherCategory.count} complaints`;
    }

    // Show tooltip on hover
    btn.addEventListener('mouseenter', (e) => {
        const rect = btn.getBoundingClientRect();
        const parentRect = btn.parentElement.getBoundingClientRect();
        tooltip.style.top = (rect.bottom - parentRect.top + 6) + 'px';
        tooltip.style.right = '0px';
        tooltip.classList.add('visible');
    });

    btn.addEventListener('mouseleave', () => {
        tooltip.classList.remove('visible');
    });

    btn.addEventListener('click', () => {
        selectOtherCategory();
    });
}

// Select "Other" category
function selectOtherCategory() {
    const btn = document.getElementById('other-category-btn');
    const label = document.getElementById('other-label');
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
    if (label) label.textContent = 'Viewing uncategorized';

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
            borderColor: CHART_COLORS.green,
            backgroundColor: CHART_COLORS.green + '20',
            borderWidth: 3,
            tension: 0.3,
            fill: false,
            pointRadius: 3,
            pointHoverRadius: 5,
            pointBackgroundColor: CHART_COLORS.green,
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

    // Update total count
    const totalFiltered = data.categories.reduce((sum, cat) => {
        return sum + filterComplaintsByTime(cat.complaints).length;
    }, 0);
    document.getElementById('total-complaints').textContent = totalFiltered;
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
