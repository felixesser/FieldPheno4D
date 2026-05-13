document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const tabsContainer = document.getElementById('tabs-container');
    const timeSlider = document.getElementById('time-slider');
    const sliderTicks = document.getElementById('slider-ticks');
    const dateLabel = document.getElementById('current-date-label');
    const nadirView = document.getElementById('nadir-view');
    const sideXzView = document.getElementById('side-xz-view');
    const sideYzView = document.getElementById('side-yz-view');
    const imageViewer = document.querySelector('.image-viewer');
    const viewerRight = document.querySelector('.viewer-right');
    const nadirContainer = nadirView.closest('.figure-container');
    const sideXzContainer = sideXzView.closest('.figure-container');
    const sideYzContainer = sideYzView.closest('.figure-container');

    let dataset = {};
    let activePlot = null;
    let loadingCombinedImage = false;

    // Theme Toggle
    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
    });

    // Fetch Plot Data
    fetch('/api/plots')
        .then(response => response.json())
        .then(data => {
            dataset = data;
            const plots = Object.keys(data);
            if (plots.length > 0) {
                renderTabs(plots);
                selectPlot(plots[0]);
            }
        });

    function renderTabs(plots) {
        tabsContainer.innerHTML = '';
        plots.forEach(plot => {
            const btn = document.createElement('button');
            btn.className = 'tab';
            btn.textContent = plot;
            btn.onclick = () => selectPlot(plot);
            tabsContainer.appendChild(btn);
        });
    }

    function selectPlot(plot) {
        activePlot = plot;
        // Update Tabs UI
        document.querySelectorAll('.tab').forEach(t => {
            t.classList.toggle('active', t.textContent === plot);
        });

        // Update Slider
        const dates = dataset[plot];
        if (dates && dates.length > 0) {
            timeSlider.min = 0;
            timeSlider.max = dates.length - 1;
            timeSlider.value = 0;
            renderSliderTicks(dates);
            updateImage(0);
        }
    }

    function renderSliderTicks(dates) {
        sliderTicks.innerHTML = '';
        const count = dates.length;
        dates.forEach((date, i) => {
            const tickContainer = document.createElement('div');
            tickContainer.className = 'tick-container';
            
            // Calculate absolute position to align with standard range slider thumbs
            // A thumb is usually in the center when min/max values are reached
            const percentage = count > 1 ? (i / (count - 1)) * 100 : 50;
            tickContainer.style.left = `calc(${percentage}%)`;

            const tick = document.createElement('div');
            tick.className = 'tick-label';
            tick.textContent = formatDateString(date);
            tick.onclick = () => {
                timeSlider.value = i;
                updateImage(i);
            };
            
            tickContainer.appendChild(tick);
            sliderTicks.appendChild(tickContainer);
        });
    }

    function formatDateString(dateStr) {
        if (dateStr.length === 6) {
            // Converts 230530 to 2023-05-30
            return `20${dateStr.slice(0,2)}-${dateStr.slice(2,4)}-${dateStr.slice(4,6)}`;
        }
        return dateStr;
    }

    timeSlider.addEventListener('input', (e) => {
        updateImage(e.target.value);
    });

    function updateImage(index) {
        if (!activePlot || !dataset[activePlot]) return;
        const date = dataset[activePlot][index];
        dateLabel.textContent = formatDateString(date);
        
        // Prefer combined images (single frame per date) located in dem/png/combined/
        const combinedUrl = `/data/${activePlot}/dem/png/combined/${date}_combined.png`;
        loadingCombinedImage = true;

        // If combined exists, display it in the main nadir pane and hide side views.
        // Otherwise, fall back to legacy nadir + side images.
        nadirView.onload = () => {
            if (loadingCombinedImage) {
                // Combined loaded successfully — hide side views
                if (imageViewer) imageViewer.classList.add('combined-layout');
                if (viewerRight) viewerRight.style.display = 'none';
            }
            if (nadirContainer) nadirContainer.style.display = '';
            if (loadingCombinedImage) {
                if (sideXzContainer) sideXzContainer.style.display = 'none';
                if (sideYzContainer) sideYzContainer.style.display = 'none';
            }
        };

        nadirView.onerror = () => {
            // Combined not found — fallback to legacy three-image layout
            nadirView.onerror = null;
            loadingCombinedImage = false;
            nadirView.src = `/data/${activePlot}/dem/png/nadir/${date}.png`;
            sideXzView.src = `/data/${activePlot}/dem/png/side_xz/${date}_side_xz.png`;
            sideYzView.src = `/data/${activePlot}/dem/png/side_yz/${date}_side_yz.png`;
            if (imageViewer) imageViewer.classList.remove('combined-layout');
            if (viewerRight) viewerRight.style.display = '';
            if (nadirContainer) nadirContainer.style.display = '';
            if (sideXzContainer) sideXzContainer.style.display = '';
            if (sideYzContainer) sideYzContainer.style.display = '';
        };

        // Trigger load attempt for combined image
        nadirView.src = combinedUrl;
    }
});