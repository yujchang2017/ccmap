$(document).ready(function() {
    // 全域儲存最新查詢結果
    let latestResults = [];

    // 確認 jQuery 是否載入
    if (typeof $ === 'undefined') {
        console.error('jQuery is not loaded. Please ensure the jQuery CDN is accessible.');
        return;
    } else {
        console.log('jQuery loaded successfully.');
    }

    // Cookie 同意邏輯
    const cookieBanner = $('#cookie-banner');
    if (localStorage.getItem('cookieAccepted') !== 'yes') {
        cookieBanner.css({ display: 'flex', justifyContent: 'center', alignItems: 'center' });
    } else {
        cookieBanner.hide();
    }
    $('#accept-cookies').on('click', function() {
        localStorage.setItem('cookieAccepted', 'yes');
        cookieBanner.hide();
    });

    // 新手引導邏輯 - 第一次訪問學習地圖頁面時顯示引導
    const welcomeModal = $('#welcomeGuideModal');
    if (welcomeModal.length > 0) {
        // 檢查是否為第一次訪問
        if (localStorage.getItem('hasSeenWelcomeGuide') !== 'yes') {
            // 延遲一點顯示，讓頁面完全載入
            setTimeout(function() {
                const modal = new bootstrap.Modal(welcomeModal[0]);
                modal.show();
            }, 500);
        }
        
        // 「開始使用」按鈕點擊處理
        $('#startUsingBtn').on('click', function() {
            // 檢查是否勾選「下次不再顯示」
            if ($('#dontShowAgain').is(':checked')) {
                localStorage.setItem('hasSeenWelcomeGuide', 'yes');
            }
        });
        
        // 當 Modal 被關閉時也檢查
        welcomeModal.on('hidden.bs.modal', function() {
            if ($('#dontShowAgain').is(':checked')) {
                localStorage.setItem('hasSeenWelcomeGuide', 'yes');
            }
        });
    }

    // 取得或產生使用者 UUID
    function getUUID() {
        let uuid = localStorage.getItem("user_uuid");
        const uuidPattern = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
        if (!uuid || !uuidPattern.test(uuid)) {
            if (crypto && crypto.randomUUID) {
                uuid = crypto.randomUUID();
            } else {
                // Fallback: generate UUID v4 format manually
                uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                });
            }
            localStorage.setItem("user_uuid", uuid);
        }
        return uuid;
    }
    console.log("User UUID:", getUUID());

    // 進度條顯示／隱藏
    function showProgress() { $('#progress-container').show(); }
    function hideProgress() { $('#progress-container').hide(); }

    // 記錄資源點擊
    window.logResourceClick = function(resName, resURL) {
        const userUuid = getUUID();
        $.ajax({
            url: "/log_event",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ uuid: userUuid, event_type: "click_resource", event_data: { resource_name: resName, resource_url: resURL } })
        });
        return true;
    };

    // 載入主題選單
    function loadTopics(stage, domain) {
        if (!stage || !domain || domain === '不拘') {
            $('#topic').html('<option value="">請先選擇領域</option>').prop('disabled', true);
            $('#content').html('<option value="">請選擇領域</option>').prop('disabled', true);
            return;
        }
        $('#topic').prop('disabled', false);
        $.ajax({
            url: "/get_topics",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ stage: stage, domain: domain }),
            success: function(response) {
                const topicSelect = $('#topic').empty();
                topicSelect.append(new Option('不拘', '不拘'));
                (response.topics || []).forEach(t => topicSelect.append(new Option(t, t)));
                loadOptions(stage, domain, topicSelect.val());
            },
            error: function() {
                console.error('Error fetching topic options');
                $('#topic').html('<option value="">載入失敗</option>').prop('disabled', true);
                $('#content').html('<option value="">載入失敗</option>').prop('disabled', true);
            }
        });
    }

    // 載入細分內容選單
    function loadOptions(stage, domain, topic) {
        if (!stage || !domain || domain === '不拘') {
            $('#content').html('<option value="">請選擇領域</option>').prop('disabled', true);
            return;
        }
        $('#content').prop('disabled', false);
        $.ajax({
            url: "/get_options",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ stage: stage, domain: domain, topic: topic || '不拘' }),
            success: function(response) {
                const contentSelect = $('#content').empty();
                contentSelect.append(new Option('請選擇細分內容', ''));
                response.options.forEach(opt => contentSelect.append(new Option(opt, opt)));
            },
            error: function() {
                console.error('Error fetching content options');
                $('#content').html('<option value="">載入失敗</option>').prop('disabled', true);
            }
        });
    }
    loadTopics($('#stage').val(), $('#domain').val());
    $('#stage, #domain').change(() => loadTopics($('#stage').val(), $('#domain').val()));
    $('#topic').change(() => loadOptions($('#stage').val(), $('#domain').val(), $('#topic').val()));

    // 查詢 Keyideas
    $('#query-btn').click(function() {
        const stage = $('#stage').val();
        const domain = $('#domain').val();
        const topic = $('#topic').val() || '';
        const selectedContent = $('#content').val() || '';
        const additionalInput = $('#additional_input').val();
        const userUuid = getUUID();
        if (!stage || !domain || (!selectedContent && !additionalInput)) {
            alert('請至少選擇學習階段、領域，並選擇細分內容或輸入其他內容。');
            return;
        }
        $('#results').empty();
        showProgress();
        $.ajax({
            url: '/query', method: 'POST', contentType: 'application/json',
            data: JSON.stringify({ uuid: userUuid, stage: stage, domain: domain, topic: topic, selected_content: selectedContent, additional_input: additionalInput }),
            success: function(resp) {
                hideProgress();
                if (resp.error) {
                    // 後端返回錯誤訊息
                    $('#results').html(`<div class="alert alert-warning">${resp.error}</div>`);
                } else if (resp.results && resp.results.length > 0) {
                    // 有查詢結果
                    $(document).trigger('resultsLoaded', [resp.results]);
                } else {
                    // 無查詢結果
                    $('#results').html('<div class="text-center text-muted py-5"><svg width="48" height="48" fill="currentColor" class="bi bi-search mb-3" viewBox="0 0 16 16"><path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/></svg><p>無符合條件的結果</p></div>');
                }
            },
            error: function(err) {
                console.error('Query failed:', err);
                hideProgress();
                $('#results').html('<div class="alert alert-danger">查詢失敗，請稍後再試。</div>');
            }
        });
    });

    // 綁定學習地圖按鈕事件
    $('#results').on('click', '.learning-map', function() {
        const id = $(this).data('id');
        const $list = $(this).closest('.result-card').find('.resource-list');
        const clicked = latestResults.find(r => (r.key_id||r.id) == id);
        if ($list.is(':visible') && $list.hasClass('outcomes-loaded')) {
            $list.slideUp().removeClass('outcomes-loaded');
        } else {
            let html;
            if (clicked && clicked.construct_outcome && clicked.construct_outcome.length) {
                const items = clicked.construct_outcome.map(co => `<li><strong>${co.construct}</strong>：${co.outcome}</li>`).join('');
                html = `<h6>學習目標</h6><ul>${items}</ul>`;
            } else {
                html = `<h6>學習目標</h6><p>無學習目標資料</p>`;
            }
            $list.html(html).addClass('outcomes-loaded').slideDown();
        }
    });

    // 綁定相關資源按鈕事件（整合篩選器到資源列表中）
    $('#results').on('click', '.related-resources', function() {
        const keyidea = $(this).closest('.result-card').data('keyidea');
        const $list = $(this).closest('.result-card').find('.resource-list');
        const $btn = $(this);
        
        // 如果已經展開，則收合
        if ($list.is(':visible') && !$list.hasClass('outcomes-loaded')) {
            $list.slideUp();
            $btn.text('相關資源');
            return;
        }
        
        showProgress();
        $btn.text('載入中...');
        
        $.ajax({
            url: '/resources', method: 'POST', contentType: 'application/json',
            data: JSON.stringify({
                uuid: getUUID(), 
                keyidea: keyidea,
                lang: 'all', 
                res_type: 'all',
                source: 'all', 
                age: 'all'
            }),
            success: resp => {
                hideProgress();
                $btn.text('收合');
                let html;
                
                if (!resp.resources || !resp.resources.length) {
                    html = `<h6>相關教學資源</h6>
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                目前沒有與「${keyidea}」相關的教學素材。
                            </div>`;
                } else {
                    // 建立篩選器
                    html = `
                        <div class="resource-filters mb-3" style="background-color: #fff; border: 2px solid #dee2e6; border-radius: 8px; padding: 1rem;">
                            <div class="d-flex align-items-center mb-2">
                                <i class="fas fa-filter me-2 text-primary"></i>
                                <strong>篩選器</strong>
                                <span class="ms-2 text-muted resource-count">(找到 ${resp.resources.length} 筆素材)</span>
                            </div>
                            <div class="row g-2 align-items-end">
                                <div class="col-md-2">
                                    <label class="form-label fw-semibold" style="font-size: 0.9rem;">語言</label>
                                    <select class="form-select form-select-sm filter-lang">
                                        <option value="all">全部</option>
                                        <option value="cn">中文</option>
                                        <option value="en">英文</option>
                                    </select>
                                </div>
                                <div class="col-md-2">
                                    <label class="form-label fw-semibold" style="font-size: 0.9rem;">類型</label>
                                    <select class="form-select form-select-sm filter-type">
                                        <option value="all">全部</option>
                                        <option value="PPT">簡報</option>
                                        <option value="video">影片</option>
                                        <option value="game">遊戲</option>
                                        <option value="curriculum">課程</option>
                                        <option value="lesson_plan">教案</option>
                                        <option value="activity">活動</option>
                                    </select>
                                </div>
                                <div class="col-md-2">
                                    <label class="form-label fw-semibold" style="font-size: 0.9rem;">來源</label>
                                    <select class="form-select form-select-sm filter-source">
                                        <option value="all">全部</option>
                                    </select>
                                </div>
                                <div class="col-md-2">
                                    <label class="form-label fw-semibold" style="font-size: 0.9rem;">學習階段</label>
                                    <select class="form-select form-select-sm filter-age">
                                        <option value="all">全部</option>
                                    </select>
                                </div>
                                <div class="col-md-2">
                                    <button class="btn btn-primary btn-sm w-100 apply-filter-btn">
                                        <i class="fas fa-check me-1"></i>確定篩選
                                    </button>
                                </div>
                                <div class="col-md-2">
                                    <button class="btn btn-outline-secondary btn-sm w-100 reset-filter-btn">
                                        <i class="fas fa-redo me-1"></i>重設
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;

                    // 建立資源表格
                    const langMap = { cn: '中文', en: '英文' };
                    const typeMap = { 
                        lesson_plan: '教案', 
                        game: '遊戲', 
                        video: '影片', 
                        PPT: '簡報', 
                        curriculum: '課程', 
                        activity: '活動' 
                    };

                    const ADL_LOGIN_NOTE = '素材來源為adl.edu.tw者，是教育部因材網的教學資源。除了少數影片還在建置當中，如果無法觀看影片，請先用因材網帳號登入一次後，再點選網址便可順利觀看影片';
                    let hasAdlResource = false;

                    html += `
                        <div class="adl-login-note alert alert-warning fw-semibold fs-6 py-2 px-3 mb-2" style="display:none;"></div>
                        <table class="table table-sm table-hover table-bordered">
                            <thead class="table-light">
                                <tr>
                                    <th style="width: 6%;" class="text-center">語言</th>
                                    <th style="width: 8%;" class="text-center">類型</th>
                                    <th style="width: 20%;">名稱</th>
                                    <th style="width: 25%;">簡介</th>
                                    <th style="width: 12%;" class="text-center">來源網站</th>
                                    <th style="width: 10%;" class="text-center">來源</th>
                                    <th style="width: 8%;" class="text-center">學習階段</th>
                                    <th style="width: 7%;" class="text-center">相似度</th>
                                    <th style="width: 4%;" class="text-center">回報</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    // 收集所有來源和階段用於篩選器
                    const sources = new Set();
                    const ages = new Set();

                    const normalizeOpt = (val) => {
                        if (val == null) return '';
                        return String(val).trim();
                    };

                    const rebuildFilterOptions = (resources) => {
                        const $sourceFilter = $list.find('.filter-source');
                        const $ageFilter = $list.find('.filter-age');
                        if (!$sourceFilter.length || !$ageFilter.length) return;

                        const prevSource = $sourceFilter.val() || 'all';
                        const prevAge = $ageFilter.val() || 'all';

                        const srcSet = new Set();
                        const ageSet = new Set();
                        (resources || []).forEach(r => {
                            const s = normalizeOpt(r && r.source);
                            const a = normalizeOpt(r && r.age);
                            if (s) srcSet.add(s);
                            if (a) ageSet.add(a);
                        });

                        $sourceFilter.find('option:not([value="all"])').remove();
                        $ageFilter.find('option:not([value="all"])').remove();

                        Array.from(srcSet).sort((a, b) => a.localeCompare(b, 'zh-Hant')).forEach(s => {
                            $sourceFilter.append(`<option value="${s}">${s}</option>`);
                        });
                        Array.from(ageSet).sort((a, b) => a.localeCompare(b, 'zh-Hant')).forEach(a => {
                            $ageFilter.append(`<option value="${a}">${a}</option>`);
                        });

                        if ($sourceFilter.find(`option[value="${prevSource}"]`).length) {
                            $sourceFilter.val(prevSource);
                        } else {
                            $sourceFilter.val('all');
                        }
                        if ($ageFilter.find(`option[value="${prevAge}"]`).length) {
                            $ageFilter.val(prevAge);
                        } else {
                            $ageFilter.val('all');
                        }
                    };

                    resp.resources.forEach(res => {
                        const langLabel = langMap[res.lang] || res.lang || '-';
                        const typeLabel = typeMap[res.type] || res.type || '-';
                        const name = res.name || '無名稱';
                        const description = res.description || '無描述';
                        const source = res.source || '';
                        const ageLabel = res.age || '';
                        const similarity = (res.similarity != null) ? Number(res.similarity).toFixed(4) : '-';

                        if (!hasAdlResource && res.URL && String(res.URL).includes('adl.edu.tw')) {
                            hasAdlResource = true;
                        }
                        
                        if (normalizeOpt(res.source)) sources.add(normalizeOpt(res.source));
                        if (normalizeOpt(res.age)) ages.add(normalizeOpt(res.age));

                        let site = '-';
                        try {
                            if (res.URL) {
                                const url = new URL(res.URL);
                                site = url.hostname;
                            }
                        } catch (e) {
                            site = '未知來源';
                        }

                        const escapedName = (name || '').replace(/'/g, "\\'");
                        const escapedUrl = (res.URL || '#').replace(/'/g, "\\'");
                        
                        // 處理簡介: 預設顯示前50個字
                        const shortDesc = description.length > 50 ? description.substring(0, 50) + '...' : description;
                        const descId = `desc-${res.id || Math.random().toString(36).substr(2, 9)}`;

                        html += `
                            <tr data-lang="${res.lang || ''}" 
                                data-type="${res.type || ''}" 
                                data-source="${res.source || ''}"
                                data-age="${res.age || ''}">
                                <td class="text-center">${langLabel}</td>
                                <td class="text-center">${typeLabel}</td>
                                <td class="cell-name" title="${name}">
                                    ${res.URL ? `<a href="${res.URL}" onclick="logResourceClick('${escapedName}','${escapedUrl}')" target="_blank" class="text-decoration-none text-primary">${name}</a>` : name}
                                </td>
                                <td>
                                    <span class="description-short" id="${descId}-short">${shortDesc}</span>
                                    <span class="description-full" id="${descId}-full" style="display: none;">${description}</span>
                                    ${description.length > 50 ? `<a href="javascript:void(0)" class="toggle-description text-primary ms-1" data-target="${descId}" style="font-size: 0.85em;">[展開]</a>` : ''}
                                </td>
                                <td class="text-center cell-source-url">
                                    ${res.URL ? `<a href="${res.URL}" target="_blank" class="text-decoration-none">${site}</a>` : site}
                                </td>
                                <td class="text-center">${source ? source : '<span class="text-muted">-</span>'}</td>
                                <td class="text-center">${ageLabel ? ageLabel : '<span class="text-muted">-</span>'}</td>
                                <td class="text-center"><span class="badge bg-success">${similarity}</span></td>
                                <td class="text-center">
                                    <button class="btn btn-sm btn-outline-warning report-resource" 
                                            data-resource-identifier="${res.id || res.URL}" 
                                            data-resource-name="${escapedName}"
                                            title="回報問題">
                                        <i class="fas fa-flag"></i>
                                    </button>
                                </td>
                            </tr>
                        `;
                    });

                    html += `
                            </tbody>
                        </table>
                    `;

                    // 填充來源和階段選項（在 DOM 插入後）
                    $list.html(html).removeClass('outcomes-loaded').slideDown(() => {
                        const $adlNote = $list.find('.adl-login-note');
                        if (hasAdlResource) {
                            $adlNote.text(ADL_LOGIN_NOTE).show();
                        } else {
                            $adlNote.hide();
                        }

                        // 初次載入就以目前回傳結果建立選項
                        rebuildFilterOptions(resp.resources);

                        const buildTableRows = (resources) => {
                            let rowsHtml = '';
                            resources.forEach(res => {
                                const langLabel = langMap[res.lang] || res.lang || '-';
                                const typeLabel = typeMap[res.type] || res.type || '-';
                                const name = res.name || '無名稱';
                                const description = res.description || '無描述';
                                const source = res.source || '';
                                const ageLabel = res.age || '';
                                const similarity = (res.similarity != null) ? Number(res.similarity).toFixed(4) : '-';

                                let site = '-';
                                try {
                                    if (res.URL) {
                                        const url = new URL(res.URL);
                                        site = url.hostname;
                                    }
                                } catch (e) {
                                    site = '未知來源';
                                }

                                const escapedName = (name || '').replace(/'/g, "\\'");
                                const escapedUrl = (res.URL || '#').replace(/'/g, "\\'");

                                const shortDesc = description.length > 50 ? description.substring(0, 50) + '...' : description;
                                const descId = `desc-${res.id || Math.random().toString(36).substr(2, 9)}`;

                                rowsHtml += `
                                    <tr data-lang="${res.lang || ''}" 
                                        data-type="${res.type || ''}" 
                                        data-source="${res.source || ''}"
                                        data-age="${res.age || ''}">
                                        <td class="text-center">${langLabel}</td>
                                        <td class="text-center">${typeLabel}</td>
                                        <td class="cell-name" title="${name}">
                                            ${res.URL ? `<a href="${res.URL}" onclick="logResourceClick('${escapedName}','${escapedUrl}')" target="_blank" class="text-decoration-none text-primary">${name}</a>` : name}
                                        </td>
                                        <td>
                                            <span class="description-short" id="${descId}-short">${shortDesc}</span>
                                            <span class="description-full" id="${descId}-full" style="display: none;">${description}</span>
                                            ${description.length > 50 ? `<a href="javascript:void(0)" class="toggle-description text-primary ms-1" data-target="${descId}" style="font-size: 0.85em;">[展開]</a>` : ''}
                                        </td>
                                        <td class="text-center cell-source-url">
                                            ${res.URL ? `<a href="${res.URL}" target="_blank" class="text-decoration-none">${site}</a>` : site}
                                        </td>
                                        <td class="text-center">${source ? source : '<span class="text-muted">-</span>'}</td>
                                        <td class="text-center">${ageLabel ? ageLabel : '<span class="text-muted">-</span>'}</td>
                                        <td class="text-center"><span class="badge bg-success">${similarity}</span></td>
                                        <td class="text-center">
                                            <button class="btn btn-sm btn-outline-warning report-resource" 
                                                    data-resource-identifier="${res.id || res.URL}" 
                                                    data-resource-name="${escapedName}"
                                                    title="回報問題">
                                                <i class="fas fa-flag"></i>
                                            </button>
                                        </td>
                                    </tr>
                                `;
                            });

                            return rowsHtml;
                        };

                        const fetchAndRenderResources = (filters, topK) => {
                            showProgress();

                            $.ajax({
                                url: '/resources', method: 'POST', contentType: 'application/json',
                                data: JSON.stringify({
                                    uuid: getUUID(),
                                    keyidea: keyidea,
                                    lang: filters.lang,
                                    res_type: filters.type,
                                    source: filters.source,
                                    age: filters.age,
                                    top_k: topK
                                }),
                                success: (r) => {
                                    hideProgress();

                                    const resourcesAll = (r && r.resources) ? r.resources : [];

                                    // 每次重新查詢都同步更新來源/階段選單，避免「表格有、選單沒有」
                                    rebuildFilterOptions(resourcesAll);

                                    // Update ADL login note based on current results
                                    const hasAdlNow = resourcesAll.some(x => x && x.URL && String(x.URL).includes('adl.edu.tw'));
                                    const $adlNoteNow = $list.find('.adl-login-note');
                                    if (hasAdlNow) {
                                        $adlNoteNow.text(ADL_LOGIN_NOTE).show();
                                    } else {
                                        $adlNoteNow.hide();
                                    }

                                    const displayLimit = 50;
                                    const resources = resourcesAll.slice(0, displayLimit);
                                    const $tbody = $list.find('tbody');

                                    if (!resourcesAll.length) {
                                        $tbody.html('<tr><td colspan="9" class="text-center text-muted py-4">無符合條件的素材（已擴大候選結果仍為 0）</td></tr>');
                                        $list.find('.resource-count').text('(找到 0 筆素材)');
                                        return;
                                    }

                                    $tbody.html(buildTableRows(resources));
                                    const suffix = resourcesAll.length > resources.length ? `（僅顯示前 ${resources.length} 筆）` : '';
                                    $list.find('.resource-count').text(`(找到 ${resourcesAll.length} 筆素材${suffix})`);
                                },
                                error: (err) => {
                                    console.error('Error fetching filtered resources:', err);
                                    hideProgress();
                                    const $tbody = $list.find('tbody');
                                    $tbody.html('<tr><td colspan="9" class="text-center text-danger py-4">篩選失敗，請稍後再試</td></tr>');
                                }
                            });
                        };

                        // Avoid duplicated handlers if user expands/collapses repeatedly
                        $list.off('click', '.apply-filter-btn');
                        $list.off('click', '.reset-filter-btn');
                        $list.off('keypress', '.filter-lang, .filter-type, .filter-source, .filter-age');

                        // 綁定確定篩選按鈕：改為重新向後端查詢（擴大 top_k，避免只在前 20 筆裡篩到 0）
                        $list.on('click', '.apply-filter-btn', function(e) {
                            e.preventDefault();
                            const filters = {
                                lang: $list.find('.filter-lang').val(),
                                type: $list.find('.filter-type').val(),
                                source: $list.find('.filter-source').val(),
                                age: $list.find('.filter-age').val()
                            };
                            fetchAndRenderResources(filters, 200);
                        });

                        // 綁定重設按鈕：重設選項並回到預設 20 筆
                        $list.on('click', '.reset-filter-btn', function(e) {
                            e.preventDefault();
                            $list.find('.filter-lang').val('all');
                            $list.find('.filter-type').val('all');
                            $list.find('.filter-source').val('all');
                            $list.find('.filter-age').val('all');

                            fetchAndRenderResources({ lang: 'all', type: 'all', source: 'all', age: 'all' }, 20);
                        });

                        // 支援 Enter 鍵觸發篩選
                        $list.on('keypress', '.filter-lang, .filter-type, .filter-source, .filter-age', function(e) {
                            if (e.which === 13) {
                                e.preventDefault();
                                const filters = {
                                    lang: $list.find('.filter-lang').val(),
                                    type: $list.find('.filter-type').val(),
                                    source: $list.find('.filter-source').val(),
                                    age: $list.find('.filter-age').val()
                                };
                                fetchAndRenderResources(filters, 200);
                            }
                        });

                        // Update count label for initial load (server returned top 20)
                        $list.find('.resource-count').text(`(找到 ${resp.resources.length} 筆素材)`);
                    });

                    return; // 避免執行下面的 slideDown
                }
                
                $list.html(html).removeClass('outcomes-loaded').slideDown();
            },
            error: err => {
                console.error('Error fetching resources:', err);
                hideProgress();
                $btn.text('相關資源');
                $list.html('<div class="alert alert-danger">載入相關資源失敗</div>').removeClass('outcomes-loaded').slideDown();
            }
        });
    });

    // KeyIdea 回報按鈕
    $(document).on('click', '.report-btn', function() {
        $('#report-resource-identifier').val($(this).data('id'));
        $('#report-issue').val('other');
        $('#reportModal').modal('show');
    });

    // 資源列表回報按鈕
    $('#results').on('click', '.report-resource', function() {
        $('#report-resource-identifier').val($(this).data('resource-identifier'));
        $('#report-issue').val('broken_link');
        $('#reportModal').modal('show');
    });

    // 簡介展開/收合功能
    $('#results').on('click', '.toggle-description', function(e) {
        e.preventDefault();
        const target = $(this).data('target');
        const $short = $(`#${target}-short`);
        const $full = $(`#${target}-full`);
        const $link = $(this);

        if ($short.is(':visible')) {
            // 展開
            $short.hide();
            $full.show();
            $link.text('[收合]');
        } else {
            // 收合
            $full.hide();
            $short.show();
            $link.text('[展開]');
        }
    });

    // 根據問題類型更新說明欄位是否必填
    $('#report-issue').change(function() {
        const issue = $(this).val();
        if (issue === 'other') {
            $('#comment-required').text('(必填)').removeClass('text-muted').addClass('text-danger');
            $('#report-comment').attr('placeholder', '請詳細描述遇到的問題...');
        } else {
            $('#comment-required').text('(選填)').removeClass('text-danger').addClass('text-muted');
            $('#report-comment').attr('placeholder', '如有需要，可補充說明...');
        }
    });

    // 送出回報
    $('#submit-report').click(function() {
        const id = $('#report-resource-identifier').val();
        const issue = $('#report-issue').val();
        const comment = $('#report-comment').val();
        if (!id || !issue) { alert('請選擇問題類型'); return; }
        // Only require comment for 'other' issue type
        if (issue === 'other' && !comment.trim()) {
            alert('請填寫問題說明');
            return;
        }
        $.ajax({
            url: '/report', method: 'POST', contentType: 'application/json',
            data: JSON.stringify({ uuid: getUUID(), resource_id: String(id), issue: issue, comment: comment || '' }),
            success: () => { $('#reportModal').modal('hide'); alert('回報已送出，感謝！'); $('#report-comment').val(''); },
            error: () => alert('回報送出失敗，請稍後再試')
        });
    });

    // ========== 使用者回饋功能 ==========
    
    // 星星評分功能
    let currentRating = 0;
    $('#feedback-rating .star').on('click', function() {
        currentRating = $(this).data('value');
        $('#feedback-rating-value').val(currentRating);
        $('#feedback-rating .star').each(function() {
            if ($(this).data('value') <= currentRating) {
                $(this).css('color', '#f39c12');
            } else {
                $(this).css('color', '#ddd');
            }
        });
    });
    
    // 星星 hover 效果
    $('#feedback-rating .star').on('mouseenter', function() {
        const hoverValue = $(this).data('value');
        $('#feedback-rating .star').each(function() {
            if ($(this).data('value') <= hoverValue) {
                $(this).css('color', '#f39c12');
            } else {
                $(this).css('color', '#ddd');
            }
        });
    });
    
    $('#feedback-rating').on('mouseleave', function() {
        $('#feedback-rating .star').each(function() {
            if ($(this).data('value') <= currentRating) {
                $(this).css('color', '#f39c12');
            } else {
                $(this).css('color', '#ddd');
            }
        });
    });
    
    // 「其他」參與方式的條件顯示
    $('#participate-other').on('change', function() {
        if ($(this).is(':checked')) {
            $('#participation-other-container').slideDown();
        } else {
            $('#participation-other-container').slideUp();
            $('#participation-other-text').val('');
        }
    });
    
    // 浮動按鈕 hover 效果
    $('#floating-feedback-btn').on('mouseenter', function() {
        $(this).css('transform', 'translateY(-3px) scale(1.05)');
        $(this).css('box-shadow', '0 6px 20px rgba(46, 204, 113, 0.5)');
    }).on('mouseleave', function() {
        $(this).css('transform', 'translateY(0) scale(1)');
        $(this).css('box-shadow', '0 4px 15px rgba(46, 204, 113, 0.4)');
    });
    
    // 送出回饋
    $('#submit-feedback').click(function() {
        const feedbackType = $('#feedback-type').val();
        const message = $('#feedback-message').val().trim();
        const rating = $('#feedback-rating-value').val() ? parseInt($('#feedback-rating-value').val()) : null;
        const email = $('#feedback-email').val().trim();
        
        // 收集參與意願
        const participationInterests = [];
        $('.participation-options input:checked').each(function() {
            participationInterests.push($(this).val());
        });
        const participationOther = $('#participation-other-text').val().trim();
        
        // 驗證必填欄位
        if (!feedbackType) {
            alert('請選擇回饋類型');
            return;
        }
        if (!message) {
            alert('請填寫詳細說明');
            return;
        }
        
        // 驗證 email 格式（如果有填寫）
        if (email && !isValidEmail(email)) {
            alert('請輸入正確的電子郵件格式');
            return;
        }
        
        // 送出請求
        const $btn = $(this);
        $btn.prop('disabled', true).html('<i class="bi bi-hourglass-split me-1"></i>送出中...');
        
        $.ajax({
            url: '/feedback',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                uuid: getUUID(),
                feedback_type: feedbackType,
                rating: rating,
                message: message,
                participation_interests: participationInterests,
                participation_other: participationOther,
                email: email || null,
                current_page: window.location.pathname
            }),
            success: function(response) {
                $('#feedbackModal').modal('hide');
                alert('感謝您的寶貴意見！我們會認真參考您的回饋。');
                
                // 重置表單
                resetFeedbackForm();
            },
            error: function(xhr) {
                let errorMsg = '回饋送出失敗，請稍後再試';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMsg = xhr.responseJSON.message;
                }
                alert(errorMsg);
            },
            complete: function() {
                $btn.prop('disabled', false).html('<i class="bi bi-send me-1"></i>送出回饋');
            }
        });
    });
    
    // 重置回饋表單
    function resetFeedbackForm() {
        currentRating = 0;
        $('#feedback-rating-value').val('');
        $('#feedback-rating .star').css('color', '#ddd');
        $('#feedback-type').val('');
        $('#feedback-message').val('');
        $('#feedback-email').val('');
        $('.participation-options input').prop('checked', false);
        $('#participation-other-container').hide();
        $('#participation-other-text').val('');
    }
    
    // Email 格式驗證
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    // Modal 關閉時重置表單
    $('#feedbackModal').on('hidden.bs.modal', function() {
        resetFeedbackForm();
    });

    // 渲染查詢結果（只更新 DOM，並更新 latestResults）
    $(document).on('resultsLoaded', function(e, results) {
        latestResults = results || [];
        if (!results || !results.length) {
            $('#results').html('<div class="text-center text-muted py-5"><svg width="48" height="48" fill="currentColor" class="bi bi-search mb-3" viewBox="0 0 16 16"><path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/></svg><p>無符合條件的結果</p></div>');
            return;
        }
        let html = `<div class="alert alert-success"><strong>查詢完成!</strong> 找到 ${results.length} 筆相關資料</div>`;
        results.forEach(r => {
            const id = r.key_id || r.id || '';
            const text = r.key_id
              ? `${r.key_id}　${r.keyidea}`
              : r.keyidea || '無標題';
            const sim = r.similarity != null
              ? r.similarity.toFixed(4)
              : 'N/A';
            html += `<div class="result-card" data-keyidea="${r.keyidea}" data-result-id="${id}">
                       <div class="d-flex justify-content-between align-items-center">
                         <h5>${text}　(相似度: ${sim})</h5>
                         <button class="btn btn-sm btn-outline-info learning-map" data-id="${id}">學習地圖</button>
                         <button class="btn btn-sm btn-outline-success related-resources" data-id="${id}">相關資源</button>
                       </div>
                       <div class="resource-list" id="resources-${id}"></div>
                     </div>`;
        });
        $('#results').html(html);
    });

});
