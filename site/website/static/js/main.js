document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const plotsGrid = document.getElementById('plots-grid');
    const assetBase = (window.ASSET_BASE || '/static').replace(/\/$/, '');
    const dataBase = (window.DATA_BASE || '/data').replace(/\/$/, '');

    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
    });

    const renderFromData = (data) => {
        const plots = Object.keys(data || {});
        renderPlotCards(plots, data || {});
    };

    if (window.PLOTS_DATA && Object.keys(window.PLOTS_DATA).length > 0) {
        renderFromData(window.PLOTS_DATA);
    } else {
        fetch('api/plots')
            .then(response => response.json())
            .then(data => {
                renderFromData(data);
            })
            .catch(() => {
                renderFromData({});
            });
    }

    function renderPlotCards(plots, dataset) {
        if (!plotsGrid) return;
        plotsGrid.innerHTML = '';
        plots.forEach((plot, index) => {
            const dates = dataset[plot] || [];
            const linkData = window.DOWNLOAD_LINKS && window.DOWNLOAD_LINKS[plot] ? window.DOWNLOAD_LINKS[plot] : null;
            const card = createPlotCard(plot, dates, linkData, false);
            plotsGrid.appendChild(card);
        });
    }

    function createPlotCard(plot, dates, linkData, openByDefault) {
        const card = document.createElement('article');
        card.className = 'plot-card';

        const teaser = document.createElement('div');
        teaser.className = 'plot-teaser';

        const teaserImage = document.createElement('img');
        // Try a set of candidate paths for a plot-specific teaser orthophoto, falling back to the dummy teaser.
        const candidates = [];
        // 1) If plot matches PlotNN pattern, try PNN_orthophoto.png inside the plot folder
        const plotNumMatch = plot.match(/Plot(\d{1,3})$/);
        if (plotNumMatch) {
            const idx = plotNumMatch[1].padStart(2, '0');
            candidates.push(`${dataBase}/${plot}/P${idx}_orthophoto.png`);
        }
        // 2) Try direct P*-orthophoto (for plots already named P###)
        candidates.push(`${dataBase}/${plot}/${plot}_orthophoto.png`);
        // 3) try common fallback name
        candidates.push(`${dataBase}/${plot}/${plot.replace(/[^0-9]/g, '')}_orthophoto.png`);
        // finally fall back to embedded dummy
        candidates.push(`${assetBase}/images/dummy_teaser.svg`);

        let candIndex = 0;
        const tryNextCandidate = () => {
            if (candIndex >= candidates.length) return;
            teaserImage.src = candidates[candIndex++];
        };
        teaserImage.onerror = () => {
            // try next candidate
            if (candIndex < candidates.length) {
                tryNextCandidate();
            }
        };
        tryNextCandidate();
        teaserImage.alt = `${plot} teaser image`;
        teaser.appendChild(teaserImage);

        const teaserBody = document.createElement('div');
        teaserBody.className = 'plot-teaser-body';

        const title = document.createElement('h3');
        title.className = 'plot-title';
        title.textContent = plot;
        teaserBody.appendChild(title);

        // (collapse/summary removed) — viewer is always visible now

        const meta = document.createElement('div');
        meta.className = 'plot-meta';
        const cropLabel = linkData && linkData.species ? linkData.species : '';
        meta.textContent = cropLabel
            ? `Crop: ${cropLabel} · ${dates.length} available point clouds`
            : `${dates.length} available point clouds`;
        teaserBody.appendChild(meta);

        const linkWrap = document.createElement('div');
        linkWrap.className = 'plot-link-wrap';
        if (!linkData || !linkData.url || linkData.url === 'TBD') {
            const missing = document.createElement('div');
            missing.className = 'download-link-card download-link-card--missing';
            missing.textContent = 'Link Not Provided Yet.';
            linkWrap.appendChild(missing);
        } else {
            const link = document.createElement('a');
            link.className = 'download-link download-link--compact';
            link.href = linkData.url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = 'Download .zip';
            linkWrap.appendChild(link);
        }
        teaserBody.appendChild(linkWrap);
        teaser.appendChild(teaserBody);
        card.appendChild(teaser);


        // use a collapsible details element; start collapsed by default
        const details = document.createElement('details');
        details.className = 'plot-details';
        details.open = false;

        const summary = document.createElement('summary');
        summary.className = 'plot-summary';
        summary.innerHTML = `<svg viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false"><path d="M2 1 L8 5 L2 9 Z" fill="currentColor"/></svg><span class="summary-text">Show dataset</span>`;
        details.appendChild(summary);
        const viewer = document.createElement('div');
        viewer.className = 'plot-viewer';
        viewer.dataset.plot = plot;

        const sliderContainer = document.createElement('div');
        sliderContainer.className = 'slider-container';
        const sliderLabel = document.createElement('label');
        sliderLabel.innerHTML = 'Date: <span class="current-date-label"></span>';
        const currentDateLabel = sliderLabel.querySelector('.current-date-label');
        const sliderWrapper = document.createElement('div');
        sliderWrapper.className = 'slider-wrapper';
        const timeSlider = document.createElement('input');
        timeSlider.type = 'range';
        timeSlider.min = 0;
        timeSlider.max = Math.max(0, dates.length - 1);
        timeSlider.value = 0;
        timeSlider.step = 1;
        const sliderTicks = document.createElement('div');
        sliderTicks.className = 'slider-ticks';
        sliderWrapper.appendChild(timeSlider);
        sliderWrapper.appendChild(sliderTicks);
        sliderContainer.appendChild(sliderLabel);
        sliderContainer.appendChild(sliderWrapper);
        viewer.appendChild(sliderContainer);

        const imageViewer = document.createElement('div');
        imageViewer.className = 'image-viewer';

        const viewerLeft = document.createElement('div');
        viewerLeft.className = 'viewer-column viewer-left';
        const nadirContainer = document.createElement('div');
        nadirContainer.className = 'figure-container';
        const nadirView = document.createElement('img');
        nadirView.alt = 'Combined nadir or nadir image';
        nadirContainer.appendChild(nadirView);

        const sideXzContainer = document.createElement('div');
        sideXzContainer.className = 'figure-container';
        const sideXzView = document.createElement('img');
        sideXzView.alt = 'Side XZ image';
        sideXzContainer.appendChild(sideXzView);

        viewerLeft.appendChild(nadirContainer);
        viewerLeft.appendChild(sideXzContainer);

        const viewerRight = document.createElement('div');
        viewerRight.className = 'viewer-column viewer-right';
        const sideYzContainer = document.createElement('div');
        sideYzContainer.className = 'figure-container figure-tall';
        const sideYzView = document.createElement('img');
        sideYzView.alt = 'Side YZ image';
        sideYzContainer.appendChild(sideYzView);
        viewerRight.appendChild(sideYzContainer);

        imageViewer.appendChild(viewerLeft);
        imageViewer.appendChild(viewerRight);
        viewer.appendChild(imageViewer);
        details.appendChild(viewer);
        card.appendChild(details);

        const state = {
            plot,
            dates,
            timeSlider,
            sliderTicks,
            currentDateLabel,
            nadirView,
            sideXzView,
            sideYzView,
            imageViewer,
            viewerRight,
            nadirContainer,
            sideXzContainer,
            sideYzContainer,
            loadingCombinedImage: false,
        };

        timeSlider.addEventListener('input', (event) => {
            updatePlotImage(state, Number(event.target.value));
        });

        details.addEventListener('toggle', () => {
            const isOpen = details.open;
            const label = summary.querySelector('.summary-text');
            if (label) label.textContent = isOpen ? 'Hide dataset' : 'Show dataset';
            if (isOpen && state.dates.length > 0) {
                renderSliderTicks(state);
                updatePlotImage(state, Number(timeSlider.value || 0));
            }
        });

        // keep collapsed by default; if openByDefault is true open and render immediately
        if (openByDefault) {
            details.open = true;
            if (state.dates.length > 0) {
                renderSliderTicks(state);
                updatePlotImage(state, 0);
            }
            const label = summary.querySelector('.summary-text');
            if (label) label.textContent = 'Hide dataset';
        }

        return card;
    }

    function renderSliderTicks(state) {
        const { sliderTicks, timeSlider, dates } = state;
        sliderTicks.innerHTML = '';
        const count = dates.length;
        const containerWidth = sliderTicks.clientWidth || sliderTicks.getBoundingClientRect().width || 800;
        const estLabelWidth = 86;

        const sliderRect = timeSlider.getBoundingClientRect();
        const ticksRect = sliderTicks.getBoundingClientRect();
        const sliderLeftOffset = sliderRect.left - ticksRect.left;
        const sliderWidth = sliderRect.width;
        const trackInset = 8;

        const availableTrackWidth = sliderWidth && sliderWidth > 1 ? Math.max(0, sliderWidth - trackInset * 2) : containerWidth;
        const gapIfAll = count > 1 ? (availableTrackWidth / (count - 1)) : availableTrackWidth;
        const skip = gapIfAll > 0 ? Math.max(1, Math.ceil((estLabelWidth + 8) / gapIfAll)) : 1;

        dates.forEach((date, i) => {
            const tickContainer = document.createElement('div');
            tickContainer.className = 'tick-container';
            const percentage = count > 1 ? (i / (count - 1)) : 0;
            if (sliderWidth && sliderWidth > 1) {
                const leftPx = sliderLeftOffset + trackInset + percentage * Math.max(0, sliderWidth - trackInset * 2);
                tickContainer.style.left = `${leftPx}px`;
            } else {
                tickContainer.style.left = `${percentage * 100}%`;
            }
            tickContainer.onclick = () => {
                timeSlider.value = i;
                updatePlotImage(state, i);
            };
            const shouldShowLabel = (i === 0) || (i === count - 1) || (i % skip === 0);
            if (shouldShowLabel) {
                const tick = document.createElement('div');
                tick.className = 'tick-label';
                tick.textContent = formatDateString(date);
                tickContainer.appendChild(tick);
            }
            sliderTicks.appendChild(tickContainer);
        });
    }

    function formatDateString(dateStr) {
        if (dateStr.length === 6) {
            return `${dateStr.slice(2, 4)}-${dateStr.slice(4, 6)}`;
        }
        return dateStr;
    }

    function updatePlotImage(state, index) {
        const { plot, dates, currentDateLabel, nadirView, sideXzView, sideYzView, imageViewer, viewerRight, nadirContainer, sideXzContainer, sideYzContainer } = state;
        if (!dates || dates.length === 0) return;
        const safeIndex = Math.max(0, Math.min(index, dates.length - 1));
        const date = dates[safeIndex];
        currentDateLabel.textContent = formatDateString(date);

        const combinedUrl = `${dataBase}/${plot}/dem/png/combined/${date}_combined.png`;
        state.loadingCombinedImage = true;

        nadirView.onload = () => {
            if (state.loadingCombinedImage) {
                if (imageViewer) imageViewer.classList.add('combined-image');
                if (viewerRight) viewerRight.style.display = 'none';
                if (nadirContainer) nadirContainer.style.gridColumn = '1 / -1';
                if (sideXzContainer) sideXzContainer.style.display = 'none';
                if (sideYzContainer) sideYzContainer.style.display = 'none';
            }
            if (nadirContainer) nadirContainer.style.display = '';
        };

        nadirView.onerror = () => {
            nadirView.onerror = null;
            state.loadingCombinedImage = false;
            nadirView.src = `${dataBase}/${plot}/dem/png/nadir/${date}.png`;
            sideXzView.src = `${dataBase}/${plot}/dem/png/side_xz/${date}_side_xz.png`;
            sideYzView.src = `${dataBase}/${plot}/dem/png/side_yz/${date}_side_yz.png`;
            if (imageViewer) imageViewer.classList.remove('combined-image');
            if (viewerRight) viewerRight.style.display = '';
            if (nadirContainer) {
                nadirContainer.style.display = '';
                nadirContainer.style.gridColumn = '';
            }
            if (sideXzContainer) sideXzContainer.style.display = '';
            if (sideYzContainer) sideYzContainer.style.display = '';
        };

        nadirView.src = combinedUrl;
    }
});
