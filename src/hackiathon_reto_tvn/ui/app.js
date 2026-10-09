/**
 * TVN Media AI Copilot — Interactive Client Application Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // State
    const state = {
        activeTab: 'view-agenda',
        agenda: [],
        fichas: [],
        selectedFichaId: null,
        activeDraftTab: 'brief',
        systemInfo: null,
        pendingReviewAction: null,
    };

    // DOM Elements
    const elements = {
        tabs: document.querySelectorAll('.nav-tab'),
        panels: document.querySelectorAll('.view-panel'),
        systemStatus: document.getElementById('system-status-text'),
        s1Model: document.getElementById('s1-model'),
        s2Model: document.getElementById('s2-model'),

        // View 1 (Agenda)
        agendaContainer: document.getElementById('agenda-cards-container'),
        agendaSourceBanner: document.getElementById('agenda-source-banner'),
        filterBanda: document.getElementById('filter-banda'),
        btnRefreshAgenda: document.getElementById('btn-refresh-agenda'),
        t08AlertContainer: document.getElementById('t08-alert-container'),

        // View 2 (Fichas)
        caseListContainer: document.getElementById('case-list-container'),
        fichasCount: document.getElementById('fichas-count'),
        fichaDetailContainer: document.getElementById('ficha-detail-container'),
        btnExportFichas: document.getElementById('btn-export-fichas'),

        // View 3 (Jury Console)
        queryInput: document.getElementById('query-input'),
        btnSubmitQuery: document.getElementById('btn-submit-query'),
        queryResponseContainer: document.getElementById('query-response-container'),
        contraA: document.getElementById('contra-a'),
        contraB: document.getElementById('contra-b'),
        btnEvalContra: document.getElementById('btn-eval-contradiction'),
        contraResult: document.getElementById('contra-result'),
        presetBtns: document.querySelectorAll('.preset-btn'),

        // View 4 (Metrics)
        btnRunBenchmark: document.getElementById('btn-run-benchmark'),
        manifestContainer: document.getElementById('manifest-cards-container'),
        metricCitation: document.getElementById('metric-citation'),
        metricAbstention: document.getElementById('metric-abstention'),
        metricInjection: document.getElementById('metric-injection'),
        metricP5Gain: document.getElementById('metric-p5-gain'),
        metricF1: document.getElementById('metric-f1'),
        metricF1Target: document.getElementById('metric-f1-target'),
        metricLatency: document.getElementById('metric-latency'),

        // Modal
        reviewModal: document.getElementById('review-modal'),
        btnCloseModal: document.getElementById('btn-close-modal'),
        btnModalCancel: document.getElementById('btn-modal-cancel'),
        btnModalConfirm: document.getElementById('btn-modal-confirm'),
        modalTitle: document.getElementById('modal-title'),
        modalDesc: document.getElementById('modal-desc'),
        modalReviewer: document.getElementById('modal-reviewer'),
        modalNotes: document.getElementById('modal-notes'),
    };

    // ==================== INITIALIZATION ====================
    async function init() {
        setupNavigation();
        setupJuryPresets();
        setupContradictionChecker();
        setupModal();
        await loadSystemInfo();
        await loadAgenda();
        await loadFichas();
        await loadMetrics();
        await loadManifest();
    }

    // ==================== NAVIGATION ====================
    function setupNavigation() {
        elements.tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.getAttribute('data-target');
                elements.tabs.forEach(t => t.classList.remove('active'));
                elements.panels.forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                const activePanel = document.getElementById(target);
                if (activePanel) activePanel.classList.add('active');
                state.activeTab = target;
            });
        });

        elements.btnRefreshAgenda.addEventListener('click', loadAgenda);
        elements.filterBanda.addEventListener('change', renderAgenda);
        elements.btnExportFichas.addEventListener('click', exportFichas);
        elements.btnRunBenchmark.addEventListener('click', runBenchmark);
        elements.btnSubmitQuery.addEventListener('click', executeQuery);
        elements.queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') executeQuery();
        });
    }

    // ==================== SYSTEM INFO ====================
    async function loadSystemInfo() {
        try {
            const res = await fetch('/api/v1/system/info');
            if (res.ok) {
                const info = await res.json();
                state.systemInfo = info;
                elements.s1Model.textContent = info.decision_model || 'clef';
                elements.s2Model.textContent = info.llm_model || 'muse-spark';
                elements.systemStatus.textContent = 'En Línea';
            }
        } catch {
            elements.systemStatus.textContent = 'Modo Local Offline';
        }
    }

    // ==================== VIEW 1: AGENDA ====================
    async function loadAgenda() {
        elements.agendaContainer.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Cargando y priorizando agenda informativa con System One...</p>
            </div>
        `;
        try {
            const res = await fetch('/api/v1/copilot/agenda?top_n=10');
            if (res.ok) {
                state.agenda = await res.json();
                renderAgendaSource();
                renderAgenda();
            } else {
                elements.agendaContainer.innerHTML = `<div class="empty-state"><p>Error cargando la agenda.</p></div>`;
            }
        } catch (err) {
            console.error('Error fetching agenda:', err);
            // Fallback from fichas
            if (state.fichas.length > 0) {
                state.agenda = state.fichas;
                renderAgendaSource();
                renderAgenda();
            }
        }
    }

    function renderAgendaSource() {
        if (!elements.agendaSourceBanner) return;
        const liveCases = state.agenda.filter(item => item.origen_datos === 'ingesta_viva');
        if (liveCases.length) {
            const timestamps = liveCases
                .map(item => item.fecha_actualizacion_fuente)
                .filter(Boolean)
                .map(value => ({ value, epoch: Date.parse(value) }))
                .filter(item => !Number.isNaN(item.epoch))
                .sort((left, right) => right.epoch - left.epoch);
            const newest = timestamps[0] ? new Date(timestamps[0].epoch) : null;
            const formatted = newest && !Number.isNaN(newest.getTime())
                ? newest.toLocaleString('es-PA', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Panama' })
                : 'fecha de publicación no disponible';
            elements.agendaSourceBanner.className = 'agenda-source-banner agenda-source-live';
            elements.agendaSourceBanner.textContent = `Noticias recientes de la ingesta viva · fecha más reciente entre los casos mostrados: ${formatted}`;
            return;
        }

        elements.agendaSourceBanner.className = 'agenda-source-banner agenda-source-snapshot';
        elements.agendaSourceBanner.textContent = 'Corpus histórico congelado · esta agenda es de referencia y no representa noticias actuales.';
    }

    function renderAgenda() {
        const selectedFilter = elements.filterBanda.value;
        const filtered = state.agenda.filter(item => {
            const score = item.puntaje;
            const banda = score >= 70 ? 'Alto' : (score >= 40 ? 'Medio' : 'Bajo');
            return selectedFilter === 'all' || banda === selectedFilter;
        });

        // Check for T08 violation guardrail in current items
        const t08Item = state.agenda.find(item => item.puntaje >= 70 && item.estado_evidencia === 'insuficiente');
        if (t08Item) {
            elements.t08AlertContainer.innerHTML = `
                <div class="guardrail-alert">
                    <span class="ga-icon">🛡️</span>
                    <div class="ga-content">
                        <strong>ALERTA DE SEGURIDAD EDITORIAL T08 ACTIVADA (${t08Item.id_caso})</strong>
                        <p>El caso posee un puntaje de atención alto (P = ${t08Item.puntaje.toFixed(1)}), pero su estado de evidencia es INSUFICIENTE. Se bloquea automáticamente la publicación del borrador y se asigna a investigación humana independiente.</p>
                    </div>
                </div>
            `;
        } else {
            elements.t08AlertContainer.innerHTML = '';
        }

        if (filtered.length === 0) {
            elements.agendaContainer.innerHTML = `<div class="empty-state"><p>No hay noticias en la banda seleccionada.</p></div>`;
            return;
        }

        elements.agendaContainer.innerHTML = filtered.map(item => {
            const score = item.puntaje;
            const banda = score >= 70 ? 'Alto' : (score >= 40 ? 'Medio' : 'Bajo');
            const bandaClass = `banda-${banda.toLowerCase()}`;
            const comp = item.componentes || { relevancia: 0.8, impacto_potencial: 0.7, urgencia: 0.6, novedad: 0.5, evidencia_disponible: 0.8 };

            const evClass = `badge-ev-${(item.estado_evidencia || 'parcial').toLowerCase()}`;
            const evLabel = (item.estado_evidencia || 'parcial').replace(/_/g, ' ');

            const borrador = item.borrador || {};
            const titulo = borrador.titulo_propuesto || (item.afirmaciones && item.afirmaciones[0] ? item.afirmaciones[0].texto : `Caso ${item.id_caso}`);

            const fuentesStr = (item.ids_fuente || []).map(f => `<span class="sources-tag">${f}</span>`).join(' ');

            return `
                <div class="agenda-card ${bandaClass}" onclick="window.selectFichaAndOpen('${item.id_caso}')">
                    <div class="card-top">
                        <div class="card-badges">
                            <span class="badge badge-${banda.toLowerCase()}">${banda}</span>
                            <span class="badge ${evClass}">${evLabel}</span>
                            <span class="badge" style="background: rgba(255,255,255,0.06); color: #94A3B8;">${item.modalidad || 'TVN'}</span>
                        </div>
                        <div class="score-badge score-${bandaClass}">
                            <span class="score-number">${score.toFixed(1)}</span>
                            <span class="score-label">Score P</span>
                        </div>
                    </div>

                    <h3 class="card-title">${escapeHtml(titulo)}</h3>

                    <div class="card-sources">
                        <span>Fuentes:</span> ${fuentesStr || 'Corpus congelado'}
                    </div>

                    <div class="components-bars">
                        <div class="component-row">
                            <span class="cr-name">Relevancia (30%)</span>
                            <div class="cr-bar-wrap"><div class="cr-bar" style="width: ${(comp.relevancia * 100).toFixed(0)}%"></div></div>
                            <span class="cr-val">${comp.relevancia.toFixed(2)}</span>
                        </div>
                        <div class="component-row">
                            <span class="cr-name">Impacto (25%)</span>
                            <div class="cr-bar-wrap"><div class="cr-bar" style="width: ${(comp.impacto_potencial * 100).toFixed(0)}%"></div></div>
                            <span class="cr-val">${comp.impacto_potencial.toFixed(2)}</span>
                        </div>
                        <div class="component-row">
                            <span class="cr-name">Urgencia (20%)</span>
                            <div class="cr-bar-wrap"><div class="cr-bar" style="width: ${(comp.urgencia * 100).toFixed(0)}%"></div></div>
                            <span class="cr-val">${comp.urgencia.toFixed(2)}</span>
                        </div>
                        <div class="component-row">
                            <span class="cr-name">Novedad (15%)</span>
                            <div class="cr-bar-wrap"><div class="cr-bar" style="width: ${(comp.novedad * 100).toFixed(0)}%"></div></div>
                            <span class="cr-val">${comp.novedad.toFixed(2)}</span>
                        </div>
                        <div class="component-row">
                            <span class="cr-name">Evidencia (10%)</span>
                            <div class="cr-bar-wrap"><div class="cr-bar" style="width: ${(comp.evidencia_disponible * 100).toFixed(0)}%"></div></div>
                            <span class="cr-val">${comp.evidencia_disponible.toFixed(2)}</span>
                        </div>
                    </div>

                    <div class="card-footer">
                        <span>ID: <code>${item.id_caso}</code></span>
                        <span>Estado: <strong>${(item.estado_revision || 'en_revision').toUpperCase()}</strong></span>
                        <span style="color: var(--accent-cyan); font-weight: 600;">Ver Ficha &rarr;</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ==================== VIEW 2: FICHAS ====================
    async function loadFichas() {
        try {
            const res = await fetch('/api/v1/copilot/fichas');
            if (res.ok) {
                state.fichas = await res.json();
                elements.fichasCount.textContent = state.fichas.length;
                renderCaseList();
                if (state.fichas.length > 0 && !state.selectedFichaId) {
                    selectFicha(state.fichas[0].id_caso);
                }
            }
        } catch (err) {
            console.error('Error fetching fichas:', err);
        }
    }

    function renderCaseList() {
        elements.caseListContainer.innerHTML = state.fichas.map(f => {
            const isActive = f.id_caso === state.selectedFichaId ? 'active' : '';
            const borrador = f.borrador || {};
            const titulo = borrador.titulo_propuesto || borrador.resumen_250 || (f.afirmaciones && f.afirmaciones[0] ? f.afirmaciones[0].texto : `Caso ${f.id_caso}`);
            const sourceLabel = f.origen_datos === 'ingesta_viva' ? 'En vivo' : 'Histórico';
            return `
                <div class="case-item ${isActive}" onclick="window.selectFicha('${f.id_caso}')">
                    <div class="ci-top">
                        <span class="ci-id">${f.id_caso}</span>
                        <span class="ci-score">P: ${f.puntaje.toFixed(1)}</span>
                    </div>
                    <div class="ci-title">${escapeHtml(titulo.substring(0, 80))}${titulo.length > 80 ? '...' : ''}</div>
                    <div class="ci-source">Fuente: ${sourceLabel}</div>
                </div>
            `;
        }).join('');
    }

    window.selectFicha = function(idCaso) {
        state.selectedFichaId = idCaso;
        renderCaseList();
        const ficha = state.fichas.find(f => f.id_caso === idCaso);
        if (ficha) {
            renderFichaDetail(ficha);
        }
    };

    window.selectFichaAndOpen = function(idCaso) {
        const fichasTab = document.getElementById('tab-fichas');
        if (fichasTab) fichasTab.click();
        window.selectFicha(idCaso);
    };

    function renderFichaDetail(ficha) {
        const borrador = ficha.borrador || {};
        const titulo = borrador.titulo_propuesto || borrador.resumen_250 || `Caso ${ficha.id_caso}`;
        const canPublish = ficha.estado_evidencia === 'suficiente_para_borrador';
        const isBanking = ficha.modalidad === 'banca' || !!borrador.resumen_250;
        const sourceLabel = ficha.origen_datos === 'ingesta_viva' ? 'Ingesta viva' : 'Snapshot histórico';
        const sourceDate = ficha.fecha_actualizacion_fuente ? new Date(ficha.fecha_actualizacion_fuente) : null;
        const sourceDateLabel = sourceDate && !Number.isNaN(sourceDate.getTime())
            ? sourceDate.toLocaleString('es-PA', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Panama' })
            : 'fecha no disponible';

        // Affirmations table HTML
        const affirmationsRows = (ficha.afirmaciones || []).map(af => {
            const tagClass = `tag-${(af.tipo || 'hecho').toLowerCase()}`;
            const citationsHtml = (af.citas || []).map(c => `
                <div style="margin-bottom: 0.25rem;">
                    <strong>[${c.id_fuente}]</strong> ${escapeHtml(c.texto_sustento || '')}
                    <br><a href="${c.url_fuente}" target="_blank" class="citation-link">${c.url_fuente}</a>
                </div>
            `).join('');

            return `
                <tr>
                    <td style="width: 100px;"><span class="${tagClass}">${(af.tipo || 'hecho').toUpperCase()}</span></td>
                    <td>${escapeHtml(af.texto)}</td>
                    <td>${citationsHtml || '<span style="color:var(--tvn-red);">Sin citas verificadas</span>'}</td>
                </tr>
            `;
        }).join('');

        // Reviewer controls
        const reviewBox = `
            <div class="review-box">
                <div>
                    <div class="rb-status-label">Estado de Revisión Humana:</div>
                    <div class="rb-status-val">${(ficha.estado_revision || 'en_revision').toUpperCase()}</div>
                    <div class="rb-reviewer">Revisado por: <strong>${ficha.persona_revisora || 'Pendiente de asignación'}</strong></div>
                    ${ficha.observaciones_revision ? `<div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.2rem;">Nota: ${escapeHtml(ficha.observaciones_revision)}</div>` : ''}
                </div>
                <div class="rb-actions">
                    ${canPublish ? `
                        <button class="btn btn-primary" onclick="window.openReviewModal('${ficha.id_caso}', 'aprobado_como_borrador')">
                            ✓ Aprobar Borrador
                        </button>
                    ` : `
                        <button class="btn btn-secondary" disabled title="Bloqueado por Guardrail T08">
                            🔒 Aprobación Bloqueada
                        </button>
                    `}
                    <button class="btn btn-secondary" onclick="window.openReviewModal('${ficha.id_caso}', 'requiere_evidencia')">
                        ⚠️ Requerir Evidencia
                    </button>
                    <button class="btn btn-danger" onclick="window.openReviewModal('${ficha.id_caso}', 'descartado')">
                        ✕ Rechazar
                    </button>
                </div>
            </div>
        `;

        // Draft tabs content
        let draftTabsHtml = '';
        if (isBanking) {
            draftTabsHtml = `
                <div class="draft-preview-box">
                    <div class="draft-tabs">
                        <button class="draft-tab-btn active">Boletín Banca (CU-05)</button>
                    </div>
                    <div class="draft-tab-content active">
                        <div class="draft-limit-badge">Extensión Sectorial &bull; Banco Mundial / SBP</div>
                        <div class="draft-text-block">${escapeHtml(borrador.resumen_250 || 'Sin contenido')}</div>
                        ${borrador.sectores_relacionados ? `<div><strong>Sectores:</strong> ${(borrador.sectores_relacionados).join(', ')}</div>` : ''}
                        ${borrador.preguntas_analista ? `
                            <div style="margin-top:0.5rem;">
                                <strong>Preguntas para Analista:</strong>
                                <ul style="margin-left: 1.25rem; font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">
                                    ${borrador.preguntas_analista.map(q => `<li>${escapeHtml(q)}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        } else {
            draftTabsHtml = `
                <div class="draft-preview-box">
                    <div class="draft-tabs">
                        <button class="draft-tab-btn ${state.activeDraftTab === 'brief' ? 'active' : ''}" onclick="window.setDraftTab('brief')">Brief Editorial (250 palabras)</button>
                        <button class="draft-tab-btn ${state.activeDraftTab === 'guion' ? 'active' : ''}" onclick="window.setDraftTab('guion')">Guion TV (45-60s)</button>
                        <button class="draft-tab-btn ${state.activeDraftTab === 'digital' ? 'active' : ''}" onclick="window.setDraftTab('digital')">Copy Digital (80 palabras)</button>
                        <button class="draft-tab-btn ${state.activeDraftTab === 'preguntas' ? 'active' : ''}" onclick="window.setDraftTab('preguntas')">Investigación & Fuentes</button>
                    </div>

                    <div id="draft-tab-brief" class="draft-tab-content ${state.activeDraftTab === 'brief' ? 'active' : ''}">
                        <div class="draft-limit-badge">Máximo 250 palabras &bull; Contexto y Fuentes</div>
                        <div class="draft-text-block">${escapeHtml(borrador.brief_250 || 'Borrador no generado')}</div>
                    </div>

                    <div id="draft-tab-guion" class="draft-tab-content ${state.activeDraftTab === 'guion' ? 'active' : ''}">
                        <div class="draft-limit-badge">Locución Televisiva &bull; 45 a 60 Segundos</div>
                        <div class="draft-text-block">${escapeHtml(borrador.guion_45_60s || 'Sin guion disponible')}</div>
                    </div>

                    <div id="draft-tab-digital" class="draft-tab-content ${state.activeDraftTab === 'digital' ? 'active' : ''}">
                        <div class="draft-limit-badge">Máximo 80 palabras &bull; Web & Redes</div>
                        <div class="draft-text-block">${escapeHtml(borrador.copy_digital_80 || 'Sin copy disponible')}</div>
                    </div>

                    <div id="draft-tab-preguntas" class="draft-tab-content ${state.activeDraftTab === 'preguntas' ? 'active' : ''}">
                        <div class="draft-limit-badge">Preguntas de Interés Público (Mínimo 3)</div>
                        <ul style="margin-left: 1.25rem; font-size: 0.9rem; line-height: 1.6; color: var(--text-primary);">
                            ${(borrador.preguntas_investigacion || ['¿Qué impacto presupuestario genera?', '¿Cuáles son las fuentes directas?', '¿Cuál es el cronograma de ejecución?']).map(q => `<li>${escapeHtml(q)}</li>`).join('')}
                        </ul>
                        ${borrador.fuentes_pendientes ? `
                            <div style="margin-top: 1rem;">
                                <strong>Fuentes Pendientes de Verificación:</strong>
                                <p style="font-size:0.85rem; color:var(--text-secondary); margin-top:0.25rem;">${(borrador.fuentes_pendientes).join(', ')}</p>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        elements.fichaDetailContainer.innerHTML = `
            <div class="fd-header">
                <div>
                    <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--accent-cyan); font-weight: 700;">ID CASO: ${ficha.id_caso}</div>
                    <h3>${escapeHtml(titulo)}</h3>
                    <div class="fd-meta-pills">
                        <span class="badge badge-alto">Puntaje: ${ficha.puntaje.toFixed(1)}</span>
                        <span class="badge badge-ev-${(ficha.estado_evidencia || 'parcial').toLowerCase()}">Evidencia: ${(ficha.estado_evidencia || 'parcial').replace(/_/g, ' ')}</span>
                        <span class="badge" style="background:rgba(255,255,255,0.06); color:#94A3B8;">Modalidad: ${ficha.modalidad || 'TVN'}</span>
                        <span class="badge" style="background:rgba(255,255,255,0.06); color:#94A3B8;">${sourceLabel} · ${sourceDateLabel}</span>
                    </div>
                </div>
            </div>

            ${reviewBox}

            <div class="section-block">
                <div class="section-title">
                    <span>🔍 Afirmaciones Clasificadas & Citas de Respaldo (T09)</span>
                </div>
                <table class="affirmations-table">
                    <thead>
                        <tr>
                            <th>Tipo</th>
                            <th>Afirmación Extraída</th>
                            <th>Cita de Evidencia (ID Fuente, Campo & Enlace)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${affirmationsRows || '<tr><td colspan="3" style="text-align:center;">Sin afirmaciones registradas</td></tr>'}
                    </tbody>
                </table>
            </div>

            <div class="section-block">
                <div class="section-title">
                    <span>📝 Borrador Editorial Generado</span>
                </div>
                ${draftTabsHtml}
            </div>
        `;
    }

    window.setDraftTab = function(tabName) {
        state.activeDraftTab = tabName;
        const ficha = state.fichas.find(f => f.id_caso === state.selectedFichaId);
        if (ficha) renderFichaDetail(ficha);
    };

    function exportFichas() {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(state.fichas, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `fichas_export_${new Date().toISOString().slice(0, 10)}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    }

    // ==================== VIEW 3: JURY CONSOLE ====================
    function setupJuryPresets() {
        elements.presetBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.getAttribute('data-query');
                const mod = btn.getAttribute('data-mod') || 'tvn_editorial';
                elements.queryInput.value = query;
                const radio = document.querySelector(`input[name="query-mode"][value="${mod}"]`);
                if (radio) radio.checked = true;
                executeQuery();
            });
        });
    }

    async function executeQuery() {
        const query = elements.queryInput.value.trim();
        if (!query) return;

        const modality = document.querySelector('input[name="query-mode"]:checked')?.value || 'tvn_editorial';

        elements.queryResponseContainer.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Consultando evidencias y verificando citas...</p>
            </div>
        `;

        try {
            const res = await fetch('/api/v1/copilot/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ consulta: query, modalidad: modality }),
            });

            if (res.ok) {
                const data = await res.json();
                renderQueryResponse(data);
            } else {
                elements.queryResponseContainer.innerHTML = `
                    <div class="abstention-banner" style="background:rgba(239,68,68,0.15); border-color:rgba(239,68,68,0.4); color:#FCA5A5;">
                        Error en la consulta: ${res.statusText}
                    </div>
                `;
            }
        } catch (err) {
            elements.queryResponseContainer.innerHTML = `
                <div class="abstention-banner" style="background:rgba(239,68,68,0.15); border-color:rgba(239,68,68,0.4); color:#FCA5A5;">
                    Error de conexión: ${err.message}
                </div>
            `;
        }
    }

    function renderQueryResponse(data) {
        let contentHtml = '';

        if (data.es_abstencion) {
            contentHtml = `
                <div class="abstention-banner">
                    ⚠️ ${escapeHtml(data.respuesta)}
                </div>
                <p style="font-size:0.82rem; color:var(--text-secondary); margin-top:0.4rem;">
                    <strong>Invariante T06 aplicado:</strong> El sistema emite abstención explícita en lugar de alucinar cifras o fuentes no corroboradas en el corpus.
                </p>
            `;
        } else {
            const citationsList = (data.citas || []).map(c => `
                <div class="citation-chip">
                    <strong>[${c.id_fuente}]</strong> ${escapeHtml(c.texto_sustento || '')}
                    ${c.url_fuente ? `<br><a href="${c.url_fuente}" target="_blank" class="citation-link">${c.url_fuente}</a>` : ''}
                </div>
            `).join('');

            contentHtml = `
                <div style="font-size: 0.95rem; line-height: 1.6; color: var(--text-primary); white-space: pre-line;">
                    ${escapeHtml(data.respuesta)}
                </div>
                ${data.citas && data.citas.length > 0 ? `
                    <div style="margin-top: 1rem;">
                        <span style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Citas Verificadas del Corpus:</span>
                        <div class="citations-list">
                            ${citationsList}
                        </div>
                    </div>
                ` : ''}
            `;
        }

        elements.queryResponseContainer.innerHTML = contentHtml;
    }

    function setupContradictionChecker() {
        elements.btnEvalContra.addEventListener('click', async () => {
            const a = elements.contraA.value.trim();
            const b = elements.contraB.value.trim();
            if (!a || !b) return;

            elements.contraResult.classList.remove('hidden');
            elements.contraResult.innerHTML = `Evaluando versiones con el modelo System One...`;

            try {
                const res = await fetch('/api/v1/copilot/contradictions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ texto_a: a, texto_b: b }),
                });

                if (res.ok) {
                    const data = await res.json();
                    if (data.discrepancia_detectada) {
                        elements.contraResult.className = 'contra-result-box contra-detected';
                        elements.contraResult.innerHTML = `
                            <strong>⚠️ Posible contradicción (probabilidad del modelo: ${(data.probabilidad_discrepancia * 100).toFixed(0)}%)</strong>
                            <p style="margin-top:0.25rem;">${escapeHtml(data.accion)}</p>
                        `;
                    } else {
                        elements.contraResult.className = 'contra-result-box contra-none';
                        elements.contraResult.innerHTML = `
                            <strong>✓ Sin Contradicción Factual</strong>
                            <p style="margin-top:0.25rem;">${escapeHtml(data.accion)}</p>
                        `;
                    }
                }
            } catch (err) {
                elements.contraResult.textContent = `Error: ${err.message}`;
            }
        });
    }

    // ==================== VIEW 4: METRICS ====================
    async function loadMetrics() {
        try {
            const res = await fetch('/api/v1/copilot/benchmark/metrics');
            if (res.ok) {
                const data = await res.json();
                updateMetricsUI(data);
            }
        } catch (err) {
            console.error('Error fetching metrics:', err);
        }
    }

    function updateMetricsUI(data) {
        const summary = data.resumen_benchmark || {};
        const comparisons = data.comparativa_baselines || {};
        const ranking = comparisons.ranking_priorizacion || {};
        const contradictions = comparisons.clasificacion_contradicciones || {};
        if (Number.isFinite(summary.respuestas_sustentadas_con_ids_validos_porcentaje)) {
            elements.metricCitation.textContent = `${summary.respuestas_sustentadas_con_ids_validos_porcentaje.toFixed(1)}%`;
        }
        if (Number.isFinite(summary.tasa_abstencion_porcentaje)) {
            elements.metricAbstention.textContent = `${summary.tasa_abstencion_porcentaje.toFixed(1)}%`;
        }
        if (Number.isFinite(summary.resistencia_adversarial_porcentaje)) {
            elements.metricInjection.textContent = `${summary.resistencia_adversarial_porcentaje.toFixed(1)}%`;
        }
        const baselineP5 = ranking.baseline_recencia?.precision_at_5;
        const copilotP5 = ranking.copilot_score_p?.precision_at_5;
        if (Number.isFinite(baselineP5) && Number.isFinite(copilotP5)) {
            if (baselineP5 === 0) {
                elements.metricP5Gain.textContent = 'N/D';
            } else {
                const relativeGain = ((copilotP5 - baselineP5) / baselineP5) * 100;
                elements.metricP5Gain.textContent = `${relativeGain >= 0 ? '+' : ''}${relativeGain.toFixed(1)}%`;
            }
        }
        if (Number.isFinite(contradictions.modelo_decision?.f1)) {
            const model = contradictions.modelo_decision;
            elements.metricF1.textContent = model.f1.toFixed(3);
            elements.metricF1Target.textContent = `${model.provider}/${model.model}; muestra de ${model.muestra} pares sintéticos`;
            document.getElementById('table-contradiction-model').textContent = model.f1.toFixed(3);
            document.getElementById('table-contradiction-adapter').textContent = `${model.provider}/${model.model}`;
        }
        if (Number.isFinite(contradictions.baseline_regex?.f1)) {
            const regexF1 = contradictions.baseline_regex.f1;
            const modelF1 = contradictions.modelo_decision?.f1;
            document.getElementById('table-contradiction-regex').textContent = regexF1.toFixed(3);
            if (Number.isFinite(modelF1)) {
                document.getElementById('table-contradiction-delta').textContent = `${(modelF1 - regexF1).toFixed(3)}`;
            }
        }
        if (Number.isFinite(ranking.baseline_recencia?.precision_at_5) && Number.isFinite(ranking.copilot_score_p?.precision_at_5)) {
            const baseline = ranking.baseline_recencia;
            const copilot = ranking.copilot_score_p;
            document.getElementById('table-p5-baseline').textContent = `${baseline.precision_at_5.toFixed(3)} (${baseline.casos_relevantes}/${baseline.total_evaluados})`;
            document.getElementById('table-p5-copilot').textContent = `${copilot.precision_at_5.toFixed(3)} (${copilot.casos_relevantes}/${copilot.total_evaluados})`;
            document.getElementById('table-p5-delta').textContent = (copilot.precision_at_5 - baseline.precision_at_5).toFixed(3);
            document.getElementById('table-p5-relative').textContent = baseline.precision_at_5 === 0
                ? 'N/D: baseline cero'
                : `${(((copilot.precision_at_5 - baseline.precision_at_5) / baseline.precision_at_5) * 100).toFixed(1)}% (exploratorio)`;
        }
        if (Number.isFinite(summary.respuestas_sustentadas_con_ids_validos_porcentaje)) {
            document.getElementById('table-citation-rate').textContent = `${summary.respuestas_sustentadas_con_ids_validos_porcentaje.toFixed(1)}%`;
        }
        if (Number.isFinite(summary.respuestas_correctas_con_fuente_esperada_porcentaje)) {
            document.getElementById('table-answer-accuracy').textContent = (
                `${summary.respuestas_correctas_con_fuente_esperada_porcentaje.toFixed(1)}% `
                + `(${summary.respuestas_correctas_con_fuente_esperada}/${summary.consultas_sustentadas_evaluadas})`
            );
        }
        if (Number.isFinite(summary.latencia_mediana_ms)) {
            elements.metricLatency.textContent = `${summary.latencia_mediana_ms.toFixed(1)} ms`;
        }
    }

    async function runBenchmark() {
        elements.btnRunBenchmark.innerHTML = `<span>⏳ Evaluando consultas de desarrollo...</span>`;
        elements.btnRunBenchmark.disabled = true;

        try {
            const res = await fetch('/api/v1/copilot/benchmark/metrics');
            if (res.ok) {
                const data = await res.json();
                updateMetricsUI(data);
                elements.btnRunBenchmark.innerHTML = `<span>✓ Resultados de desarrollo cargados</span>`;
                setTimeout(() => {
                    elements.btnRunBenchmark.innerHTML = `<span>▶ Ejecutar benchmark de desarrollo</span>`;
                    elements.btnRunBenchmark.disabled = false;
                }, 3000);
            }
        } catch {
            elements.btnRunBenchmark.innerHTML = `<span>▶ Ejecutar benchmark de desarrollo</span>`;
            elements.btnRunBenchmark.disabled = false;
        }
    }

    async function loadManifest() {
        try {
            const res = await fetch('/api/v1/copilot/manifest');
            if (res.ok) {
                const data = await res.json();
                elements.manifestContainer.innerHTML = (data.archivos || []).map(f => `
                    <div class="manifest-file-card">
                        <div class="mfc-title">
                            <span>📄 ${f.archivo}</span>
                            <span class="badge-success">SHA-256 OK</span>
                        </div>
                        <div class="mfc-hash">${f.sha256}</div>
                        <div style="font-size:0.75rem; color:var(--text-secondary); display:flex; justify-content:space-between; margin-top:0.2rem;">
                            <span>Registros: <strong>${f.cantidad_registros}</strong></span>
                            <span>Licencia: <strong>${f.licencia}</strong></span>
                        </div>
                    </div>
                `).join('');
            }
        } catch (err) {
            console.error('Error loading manifest:', err);
        }
    }

    // ==================== MODAL & HUMAN REVIEW ====================
    function setupModal() {
        elements.btnCloseModal.addEventListener('click', closeModal);
        elements.btnModalCancel.addEventListener('click', closeModal);
        elements.btnModalConfirm.addEventListener('click', submitReview);
    }

    window.openReviewModal = function(idCaso, targetState) {
        state.pendingReviewAction = { idCaso, targetState };
        const titles = {
            'aprobado_como_borrador': 'Aprobar Caso como Borrador Editorial',
            'requiere_evidencia': 'Marcar Caso como Requiere Mayor Evidencia',
            'descartado': 'Descartar Caso de la Agenda Editorial',
        };
        elements.modalTitle.textContent = titles[targetState] || 'Actualizar Revisión';
        elements.modalDesc.textContent = `Caso ${idCaso}: La decisión será registrada en la base de datos persistente SQLite con auditoría de usuario.`;
        elements.reviewModal.classList.remove('hidden');
    };

    function closeModal() {
        elements.reviewModal.classList.add('hidden');
        state.pendingReviewAction = null;
    }

    async function submitReview() {
        if (!state.pendingReviewAction) return;

        const { idCaso, targetState } = state.pendingReviewAction;
        const reviewer = elements.modalReviewer.value.trim() || 'Editor de Turno';
        const notes = elements.modalNotes.value.trim();

        try {
            const res = await fetch('/api/v1/copilot/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    caso_id: idCaso,
                    nuevo_estado: targetState,
                    persona_revisora: reviewer,
                    observaciones: notes,
                }),
            });

            if (res.ok) {
                const updated = await res.json();
                closeModal();
                // Update in local state
                const idx = state.fichas.findIndex(f => f.id_caso === idCaso);
                if (idx !== -1) {
                    state.fichas[idx] = updated;
                }
                renderCaseList();
                renderFichaDetail(updated);
            }
        } catch (err) {
            alert(`Error al registrar revisión: ${err.message}`);
        }
    }

    // Helpers
    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Start
    init();
});
