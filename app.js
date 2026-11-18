(() => {
  'use strict';

  const LISTENING_TOTAL_SEC = 45 * 60;
  const READING_TOTAL_SEC = 75 * 60;

  // Standard ETS-style TOEIC raw-to-scaled conversion tables (0..100 correct -> 5..495 in 5-pt steps)
  const LISTENING_SCALE = [
    5, 5, 5, 5, 5, 5, 5, 10, 15, 20,
    25, 30, 35, 40, 45, 50, 55, 60, 65, 70,
    75, 80, 85, 90, 95, 100, 105, 110, 115, 120,
    125, 135, 140, 145, 150, 155, 165, 170, 175, 180,
    185, 195, 200, 205, 210, 215, 225, 230, 235, 240,
    245, 255, 260, 265, 270, 275, 285, 290, 295, 300,
    305, 315, 320, 325, 330, 335, 345, 350, 355, 360,
    365, 375, 380, 385, 390, 395, 405, 410, 415, 420,
    425, 435, 440, 445, 450, 455, 465, 470, 475, 480,
    485, 490, 490, 495, 495, 495, 495, 495, 495, 495,
    495
  ];

  const READING_SCALE = [
    5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
    10, 15, 20, 25, 30, 35, 40, 45, 50, 55,
    60, 65, 70, 75, 80, 85, 90, 95, 100, 105,
    110, 115, 120, 125, 130, 135, 140, 145, 150, 155,
    160, 165, 170, 175, 180, 185, 190, 195, 205, 210,
    215, 220, 225, 230, 235, 240, 245, 255, 260, 265,
    270, 275, 280, 285, 295, 300, 305, 310, 315, 320,
    325, 335, 340, 345, 350, 355, 360, 370, 375, 380,
    385, 390, 395, 405, 410, 415, 420, 425, 435, 440,
    445, 455, 460, 465, 475, 480, 490, 495, 495, 495,
    495
  ];

  const PART_META = {
    1: { title: 'Part 1: Photographs', subtitle: 'Listen to four statements and choose the one that best describes the picture (Q1-6).', section: 'listening', range: [1, 6] },
    2: { title: 'Part 2: Question-Response', subtitle: 'Listen to a question or statement and choose the best response (Q7-31).', section: 'listening', range: [7, 31] },
    3: { title: 'Part 3: Conversations', subtitle: 'Listen to conversations and answer three questions per conversation (Q32-70).', section: 'listening', range: [32, 70] },
    4: { title: 'Part 4: Talks', subtitle: 'Listen to short talks and answer three questions per talk (Q71-100).', section: 'listening', range: [71, 100] },
    5: { title: 'Part 5: Incomplete Sentences', subtitle: 'Select the best word or phrase to complete each sentence (Q101-130).', section: 'reading', range: [101, 130] },
    6: { title: 'Part 6: Text Completion', subtitle: 'Read each passage and choose the best word, phrase, or sentence for each blank (Q131-146).', section: 'reading', range: [131, 146] },
    7: { title: 'Part 7: Reading Comprehension', subtitle: 'Read single, double, and triple passages and answer the questions (Q147-200).', section: 'reading', range: [147, 200] },
  };

  const STORAGE = {
    active: 'toeic_active_test',
    history: 'toeic_history',
    attempt: (id) => `toeic_attempt_test_${String(id).padStart(2, '0')}`,
    scripts: (id) => `toeic_scripts_test_${String(id).padStart(2, '0')}`,
  };

  const state = {
    index: [],
    testCache: new Map(),
    activeTestId: null,
    activePart: 1,
    mode: 'official',
    showScript: false,
    blindListening: false,
    filter: 'all',
    reviewMode: false,
    timerPaused: false,
    timerInterval: null,
    openScripts: new Set(),
    revealedKeys: new Set(),
    attempt: null,
    scripts: {},
    lastAudioSave: 0,
  };

  const els = {
    homeBtn: document.getElementById('home-btn'),
    testSelect: document.getElementById('test-select'),
    testControls: document.getElementById('test-controls'),
    modeSelect: document.getElementById('mode-select'),
    timerPill: document.querySelector('.timer-pill'),
    timerSection: document.getElementById('timer-section'),
    timerDisplay: document.getElementById('timer-display'),
    timerToggleBtn: document.getElementById('timer-toggle-btn'),
    scriptToggle: document.getElementById('script-toggle'),
    blindToggle: document.getElementById('blind-toggle'),
    paletteOpenBtn: document.getElementById('palette-open-btn'),
    mobilePaletteBtn: document.getElementById('mobile-palette-btn'),
    answeredCount: document.getElementById('answered-count'),
    submitBtn: document.getElementById('submit-btn'),
    sidebarSubmitBtn: document.getElementById('sidebar-submit-btn'),
    resetBtn: document.getElementById('reset-btn'),
    partNav: document.getElementById('part-nav'),
    partPills: Array.from(document.querySelectorAll('.pill-btn')),
    filterSelect: document.getElementById('filter-select'),
    overviewView: document.getElementById('overview-view'),
    testGrid: document.getElementById('test-grid'),
    historyContainer: document.getElementById('history-container'),
    clearHistoryBtn: document.getElementById('clear-history-btn'),
    exportBtn: document.getElementById('export-btn'),
    importInput: document.getElementById('import-input'),
    testView: document.getElementById('test-view'),
    missingBanner: document.getElementById('missing-banner'),
    reviewBanner: document.getElementById('review-banner'),
    partTitle: document.getElementById('part-title'),
    partSubtitle: document.getElementById('part-subtitle'),
    questionsContainer: document.getElementById('questions-container'),
    prevPartBtn: document.getElementById('prev-part-btn'),
    nextPartBtn: document.getElementById('next-part-btn'),
    prevPartFooterBtn: document.getElementById('prev-part-footer-btn'),
    nextPartFooterBtn: document.getElementById('next-part-footer-btn'),
    sidebarProgress: document.getElementById('sidebar-progress'),
    desktopPalette: document.getElementById('desktop-palette'),
    modalPalette: document.getElementById('modal-palette'),
    paletteDialog: document.getElementById('palette-dialog'),
    paletteCloseBtn: document.getElementById('palette-close-btn'),
    scoreDialog: document.getElementById('score-dialog'),
    scoreCloseBtn: document.getElementById('score-close-btn'),
    scoreBody: document.getElementById('score-body'),
    reviewModeBtn: document.getElementById('review-mode-btn'),
    scoreOverviewBtn: document.getElementById('score-overview-btn'),
    resetDialog: document.getElementById('reset-dialog'),
    audioBar: document.getElementById('audio-bar'),
    audioEl: document.getElementById('test-audio'),
    audioLabel: document.getElementById('audio-label'),
    audioTime: document.getElementById('audio-time'),
    audioPlayBtn: document.getElementById('audio-play-btn'),
    audioBackBtn: document.getElementById('audio-back-btn'),
    audioFwdBtn: document.getElementById('audio-fwd-btn'),
    audioSeek: document.getElementById('audio-seek'),
    audioRate: document.getElementById('audio-rate'),
  };

  function setupProgressiveFallbacks() {
    const header = document.querySelector('.site-header');
    if (header) {
      const updateHeaderHeight = () => {
        document.documentElement.style.setProperty('--header-height', `${Math.ceil(header.getBoundingClientRect().height)}px`);
      };
      updateHeaderHeight();
      if ('ResizeObserver' in window) {
        new ResizeObserver(updateHeaderHeight).observe(header);
      } else {
        window.addEventListener('resize', updateHeaderHeight);
      }
    }

    if (!('switch' in HTMLInputElement.prototype)) {
      document.documentElement.classList.add('no-native-switch');
      for (const sw of document.querySelectorAll('input[type="checkbox"][switch]')) {
        sw.setAttribute('role', 'switch');
        sw.setAttribute('aria-checked', String(sw.checked));
      }
    }

    if (!('closedBy' in HTMLDialogElement.prototype)) {
      const outside = (e, dialog) => {
        const r = dialog.getBoundingClientRect();
        return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
      };
      for (const dialog of document.querySelectorAll('dialog[closedby="any"]')) {
        let pressedOutside = false;
        dialog.addEventListener('pointerdown', (e) => {
          pressedOutside = outside(e, dialog);
        });
        dialog.addEventListener('pointerup', (e) => {
          if (pressedOutside && outside(e, dialog)) dialog.close();
        });
      }
    }
  }

  function escapeHtml(str) {
    return String(str ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function isMissing(val) {
    return typeof val === 'string' && val.trim().startsWith('[missing');
  }

  function formatSec(totalSec) {
    const clamped = Math.max(0, Math.floor(totalSec));
    const h = Math.floor(clamped / 3600);
    const m = Math.floor((clamped % 3600) / 60);
    const s = clamped % 60;
    if (h > 0) {
      return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    }
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  function readJsonStorage(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  }

  function writeJsonStorage(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Ignore quota errors gracefully
    }
  }

  function defaultAttempt() {
    return {
      answers: {},
      flags: [],
      listeningSeconds: LISTENING_TOTAL_SEC,
      readingSeconds: READING_TOTAL_SEC,
      audioTime: 0,
      submitted: false,
      scoreReport: null,
      updatedAt: null,
    };
  }

  function savePreferences() {
    writeJsonStorage(STORAGE.active, {
      activeTestId: state.activeTestId,
      activePart: state.activePart,
      mode: state.mode,
      showScript: state.showScript,
      blindListening: state.blindListening,
    });
  }

  function saveAttempt() {
    if (!state.activeTestId || !state.attempt) return;
    state.attempt.updatedAt = new Date().toISOString();
    writeJsonStorage(STORAGE.attempt(state.activeTestId), state.attempt);
  }

  function saveScripts() {
    if (!state.activeTestId) return;
    writeJsonStorage(STORAGE.scripts(state.activeTestId), state.scripts);
  }

  function getTestDir(testId) {
    return `extracted/test-${String(testId).padStart(2, '0')}`;
  }

  function resolveImagePath(testId, relPath) {
    return `${getTestDir(testId)}/${relPath}`;
  }

  function formatPassageContent(raw) {
    const lines = String(raw || '').split('\n');
    const chunks = [];
    let i = 0;

    const inlineFormat = (text) =>
      escapeHtml(text)
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\[(\d{3})\]/g, '<mark class="blank-token">[$1]</mark>');

    while (i < lines.length) {
      const line = lines[i].trimEnd();
      if (line.trim().startsWith('|') && i + 1 < lines.length && lines[i + 1].includes('---')) {
        const tableLines = [];
        while (i < lines.length && lines[i].trim().startsWith('|')) {
          tableLines.push(lines[i].trim());
          i += 1;
        }
        const rows = tableLines
          .filter((l, idx) => !(idx === 1 && /^[\s|:-]+$/.test(l)))
          .map((l) =>
            l
              .replace(/^\|/, '')
              .replace(/\|$/, '')
              .split('|')
              .map((cell) => cell.trim())
          );
        if (rows.length > 0) {
          const head = rows[0].map((c) => `<th>${inlineFormat(c)}</th>`).join('');
          const body = rows
            .slice(1)
            .map((r) => `<tr>${r.map((c) => `<td>${inlineFormat(c)}</td>`).join('')}</tr>`)
            .join('');
          chunks.push(`<table class="passage-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`);
        }
        continue;
      }

      if (line.trim() === '') {
        i += 1;
        continue;
      }

      const paraLines = [];
      while (i < lines.length && lines[i].trim() !== '' && !lines[i].trim().startsWith('|')) {
        paraLines.push(inlineFormat(lines[i]));
        i += 1;
      }
      chunks.push(`<p>${paraLines.join('<br>')}</p>`);
    }

    return chunks.join('');
  }

  function collectAllQuestions(testData) {
    const items = [];
    for (const q of testData.listening.part1) {
      items.push({ part: 1, number: q.number, answer: q.answer, options: q.options, question: `Question ${q.number}` });
    }
    for (const q of testData.listening.part2) {
      items.push({ part: 2, number: q.number, answer: q.answer, options: q.options, question: `Question ${q.number}` });
    }
    for (const g of testData.listening.part3) {
      for (const q of g.questions) {
        items.push({ part: 3, number: q.number, answer: q.answer, options: q.options, question: q.question });
      }
    }
    for (const g of testData.listening.part4) {
      for (const q of g.questions) {
        items.push({ part: 4, number: q.number, answer: q.answer, options: q.options, question: q.question });
      }
    }
    for (const q of testData.reading.part5) {
      items.push({ part: 5, number: q.number, answer: q.answer, options: q.options, question: q.question });
    }
    for (const g of testData.reading.part6) {
      for (const q of g.questions) {
        items.push({ part: 6, number: q.number, answer: q.answer, options: q.options, question: q.question });
      }
    }
    for (const g of testData.reading.part7) {
      for (const q of g.questions) {
        items.push({ part: 7, number: q.number, answer: q.answer, options: q.options, question: q.question });
      }
    }
    return items;
  }

  function computeScoreReport(testData, attempt) {
    const all = collectAllQuestions(testData);
    const partTotals = { 1: 6, 2: 25, 3: 39, 4: 30, 5: 30, 6: 16, 7: 54 };
    const partCorrect = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0 };
    let listeningRaw = 0;
    let readingRaw = 0;
    let answered = 0;

    for (const item of all) {
      const chosen = attempt.answers[String(item.number)];
      if (chosen) answered += 1;
      if (chosen && chosen === item.answer) {
        partCorrect[item.part] += 1;
        if (item.part <= 4) listeningRaw += 1;
        else readingRaw += 1;
      }
    }

    const listeningScaled = LISTENING_SCALE[listeningRaw] ?? 5;
    const readingScaled = READING_SCALE[readingRaw] ?? 5;
    const totalScaled = listeningScaled + readingScaled;

    const listeningUsed = Math.max(0, LISTENING_TOTAL_SEC - attempt.listeningSeconds);
    const readingUsed = Math.max(0, READING_TOTAL_SEC - attempt.readingSeconds);

    return {
      testId: testData.test_id,
      title: testData.title,
      mode: state.mode,
      answered,
      listeningRaw,
      readingRaw,
      listeningScaled,
      readingScaled,
      totalScaled,
      partBreakdown: Object.keys(partTotals).map((p) => ({
        part: Number(p),
        correct: partCorrect[p],
        total: partTotals[p],
      })),
      elapsedSec: listeningUsed + readingUsed,
      submittedAt: new Date().toISOString(),
    };
  }

  async function loadTestData(testId) {
    if (state.testCache.has(testId)) return state.testCache.get(testId);
    const res = await fetch(`${getTestDir(testId)}/test.json`);
    if (!res.ok) throw new Error(`Failed to load Test ${testId}`);
    const data = await res.json();
    state.testCache.set(testId, data);
    return data;
  }

  function stopTimer() {
    if (state.timerInterval) {
      clearInterval(state.timerInterval);
      state.timerInterval = null;
    }
  }

  function updateTimerDisplay() {
    if (!state.attempt) return;
    const section = PART_META[state.activePart].section;
    const sec = section === 'listening' ? state.attempt.listeningSeconds : state.attempt.readingSeconds;

    els.timerSection.textContent = section === 'listening' ? 'Listening' : 'Reading';
    if (state.mode === 'practice') {
      els.timerDisplay.textContent = 'Untimed';
      els.timerToggleBtn.hidden = true;
      els.timerPill.classList.remove('is-warning');
    } else {
      els.timerDisplay.textContent = formatSec(sec);
      els.timerToggleBtn.hidden = state.attempt.submitted;
      els.timerToggleBtn.textContent = state.timerPaused ? 'Resume' : 'Pause';
      els.timerPill.classList.toggle('is-warning', sec <= 300 && !state.attempt.submitted);
    }
  }

  function startTimer() {
    stopTimer();
    updateTimerDisplay();
    if (!state.activeTestId || !state.attempt || state.attempt.submitted || state.mode !== 'official') {
      return;
    }

    state.timerInterval = setInterval(() => {
      if (state.timerPaused || !state.attempt || state.attempt.submitted || state.mode !== 'official') return;

      const section = PART_META[state.activePart].section;
      if (section === 'listening') {
        if (state.attempt.listeningSeconds > 0) {
          state.attempt.listeningSeconds -= 1;
          saveAttempt();
          updateTimerDisplay();
        }
        if (state.attempt.listeningSeconds <= 0) {
          els.audioEl.pause();
          switchPart(5);
        }
      } else {
        if (state.attempt.readingSeconds > 0) {
          state.attempt.readingSeconds -= 1;
          saveAttempt();
          updateTimerDisplay();
        }
        if (state.attempt.readingSeconds <= 0) {
          submitCurrentTest(true);
        }
      }
    }, 1000);
  }

  function syncAudioForTest(testData) {
    const src = encodeURI(testData.audio_file);
    if (els.audioEl.getAttribute('src') !== src) {
      els.audioEl.setAttribute('src', src);
      els.audioEl.load();
    }
    els.audioLabel.textContent = `Test ${String(testData.test_id).padStart(2, '0')} Audio`;
    els.audioPlayBtn.textContent = els.audioEl.paused ? 'Play' : 'Pause';
    updateAudioBarVisibility();
  }

  function updateAudioBarVisibility() {
    const show = Boolean(state.activeTestId) && PART_META[state.activePart].section === 'listening';
    els.audioBar.hidden = !show;
  }

  function updateAnsweredBadge() {
    const count = state.attempt ? Object.keys(state.attempt.answers).length : 0;
    els.answeredCount.textContent = String(count);
    els.sidebarProgress.textContent = `${count}/200`;
  }

  function renderOverview() {
    stopTimer();
    els.audioEl.pause();
    state.activeTestId = null;
    savePreferences();

    els.testSelect.value = 'overview';
    els.testControls.hidden = true;
    els.partNav.hidden = true;
    els.audioBar.hidden = true;
    els.testView.hidden = true;
    els.overviewView.hidden = false;

    const history = readJsonStorage(STORAGE.history, []);

    els.testGrid.innerHTML = state.index
      .map((meta) => {
        const attempt = readJsonStorage(STORAGE.attempt(meta.test_id), null);
        const answered = attempt ? Object.keys(attempt.answers || {}).length : 0;
        const testHist = history.filter((h) => h.testId === meta.test_id);
        const best = testHist.length ? Math.max(...testHist.map((h) => h.totalScaled)) : null;
        const last = testHist.length ? testHist[0].totalScaled : null;

        const statusBadge = meta.complete
          ? '<span class="badge badge-success">Complete</span>'
          : '<span class="badge badge-warn">Partial PDF</span>';

        const missingHtml = meta.missing_notes && meta.missing_notes.length
          ? `<div class="muted-text" style="font-size:0.78rem;">Note: Source PDF omits Listening Q1-2, Q65-70, Q71-82 (answers preserved).</div>`
          : '';

        const primaryLabel = attempt && attempt.submitted
          ? 'Review Test'
          : answered > 0
            ? 'Resume Test'
            : 'Start Test';

        return `
          <article class="test-card">
            <div class="test-card-head">
              <h2>Test ${String(meta.test_id).padStart(2, '0')}</h2>
              ${statusBadge}
            </div>
            <div class="test-card-meta">
              <div><span class="muted-text">Progress</span><strong>${answered} / 200</strong></div>
              <div><span class="muted-text">Best Score</span><strong>${best !== null ? `${best} / 990` : '--'}</strong></div>
              <div><span class="muted-text">Last Score</span><strong>${last !== null ? `${last} / 990` : '--'}</strong></div>
              <div><span class="muted-text">Images</span><strong>${meta.image_count}</strong></div>
            </div>
            ${missingHtml}
            <div class="test-card-actions">
              <button type="button" class="btn btn-primary btn-sm" data-open-test="${meta.test_id}">${primaryLabel}</button>
              ${answered > 0 ? `<button type="button" class="btn btn-outline btn-sm" data-clear-test="${meta.test_id}">Reset</button>` : ''}
            </div>
          </article>
        `;
      })
      .join('');

    if (history.length === 0) {
      els.historyContainer.innerHTML = '<p class="muted-text">No submitted tests yet. Open any test and click Submit &amp; Score to record a score.</p>';
    } else {
      const rows = history
        .slice(0, 30)
        .map((h) => {
          const dt = new Date(h.submittedAt).toLocaleString();
          return `
            <tr>
              <td>Test ${String(h.testId).padStart(2, '0')}</td>
              <td>${h.mode === 'official' ? 'Official Timed' : 'Practice'}</td>
              <td>${h.listeningScaled} (${h.listeningRaw}/100)</td>
              <td>${h.readingScaled} (${h.readingRaw}/100)</td>
              <td><strong>${h.totalScaled} / 990</strong></td>
              <td>${formatSec(h.elapsedSec)}</td>
              <td>${escapeHtml(dt)}</td>
            </tr>
          `;
        })
        .join('');
      els.historyContainer.innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th>Test</th>
              <th>Mode</th>
              <th>Listening</th>
              <th>Reading</th>
              <th>Total</th>
              <th>Time</th>
              <th>Submitted</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    }
  }

  function renderPalette() {
    if (!state.activeTestId) return;
    const testData = state.testCache.get(state.activeTestId);
    if (!testData) return;

    const all = collectAllQuestions(testData);
    const flaggedSet = new Set(state.attempt.flags || []);
    const showGrades = state.reviewMode || state.attempt.submitted;

    const partsHtml = Object.entries(PART_META)
      .map(([pKey, meta]) => {
        const pNum = Number(pKey);
        const cells = all
          .filter((q) => q.part === pNum)
          .map((q) => {
            const chosen = state.attempt.answers[String(q.number)];
            const classes = ['palette-cell'];
            if (showGrades && chosen) {
              classes.push(chosen === q.answer ? 'is-correct' : 'is-wrong');
            } else if (chosen) {
              classes.push('is-answered');
            }
            if (flaggedSet.has(q.number)) classes.push('is-flagged');
            return `<button type="button" class="${classes.join(' ')}" data-jump-part="${pNum}" data-jump-q="${q.number}">${q.number}</button>`;
          })
          .join('');

        return `
          <div>
            <h3 class="palette-part-title">Part ${pNum} (${meta.range[0]}-${meta.range[1]})</h3>
            <div class="palette-grid">${cells}</div>
          </div>
        `;
      })
      .join('');

    els.desktopPalette.innerHTML = partsHtml;
    els.modalPalette.innerHTML = partsHtml;
  }

  function shouldShowQuestion(qObj) {
    const num = qObj.number;
    const chosen = state.attempt.answers[String(num)];
    const flagged = (state.attempt.flags || []).includes(num);

    if (state.filter === 'unanswered') return !chosen;
    if (state.filter === 'flagged') return flagged;
    if (state.filter === 'incorrect') return Boolean(chosen && chosen !== qObj.answer);
    return true;
  }

  function renderOptionButtons(qObj, hideText = false) {
    const num = qObj.number;
    const chosen = state.attempt.answers[String(num)];
    const showGrades = state.reviewMode || state.attempt.submitted;
    const disabled = state.attempt.submitted;

    return Object.entries(qObj.options)
      .map(([key, text]) => {
        const classes = ['option-btn'];
        if (chosen === key) classes.push('is-selected');
        if (showGrades) {
          if (key === qObj.answer) classes.push('is-correct');
          else if (chosen === key && chosen !== qObj.answer) classes.push('is-wrong');
        }
        const label = hideText ? `(${key})` : isMissing(text) ? `(${key}) [missing in source PDF]` : escapeHtml(text);
        return `
          <button type="button" class="${classes.join(' ')}" data-q="${num}" data-opt="${key}" ${disabled ? 'disabled' : ''}>
            <span class="option-key">${key}</span>
            <span>${label}</span>
          </button>
        `;
      })
      .join('');
  }

  function renderScriptPanel(scriptKey, title, breakdownItems, answerSummary, extraTranscript) {
    const isOpen = state.showScript || state.openScripts.has(scriptKey);
    if (!isOpen) return '';

    const noteVal = state.scripts[scriptKey] || '';
    const keyVisible = state.attempt.submitted || state.reviewMode || state.revealedKeys.has(scriptKey);
    const itemsHtml = breakdownItems.map((line) => `<li>${line}</li>`).join('');
    const jsonTranscript = extraTranscript
      ? `<p class="muted-text" style="margin:0;">${escapeHtml(extraTranscript)}</p>`
      : '';

    return `
      <div class="script-panel">
        <div class="script-panel-head">
          <h3>Script &amp; Study Notes — ${escapeHtml(title)}</h3>
          <div style="display:flex;gap:0.4rem;align-items:center;">
            ${keyVisible ? `<span class="badge badge-accent">${escapeHtml(answerSummary)}</span>` : `<button type="button" class="btn btn-outline btn-xs" data-reveal-key="${escapeHtml(scriptKey)}">Reveal Answer Key</button>`}
          </div>
        </div>
        ${jsonTranscript}
        <ul class="script-breakdown">${itemsHtml}</ul>
        <label style="font-size:0.78rem;color:var(--text-muted);" for="note-${escapeHtml(scriptKey)}">
          Transcript / Personal Audio Notes (auto-saved to localStorage):
        </label>
        <textarea id="note-${escapeHtml(scriptKey)}" class="script-textarea" data-script-note="${escapeHtml(scriptKey)}" placeholder="Type or paste spoken script lines or vocabulary notes for ${escapeHtml(title)}...">${escapeHtml(noteVal)}</textarea>
      </div>
    `;
  }

  function renderQuestionHeader(qNum, promptHtml, scriptKey = null) {
    const isFlagged = (state.attempt.flags || []).includes(qNum);
    const scriptBtn = scriptKey
      ? `<button type="button" class="btn btn-outline btn-xs" data-toggle-script="${escapeHtml(scriptKey)}">${state.showScript || state.openScripts.has(scriptKey) ? 'Hide Script' : 'Show Script'}</button>`
      : '';
    return `
      <div class="q-head">
        <p class="q-prompt"><span class="q-num">${qNum}.</span> ${promptHtml}</p>
        <div class="q-actions">
          ${scriptBtn}
          <button type="button" class="flag-btn ${isFlagged ? 'is-flagged' : ''}" data-flag="${qNum}">
            ${isFlagged ? 'Flagged' : 'Flag'}
          </button>
        </div>
      </div>
    `;
  }

  function renderActivePart() {
    const testData = state.testCache.get(state.activeTestId);
    if (!testData) return;

    const meta = PART_META[state.activePart];
    els.partTitle.textContent = meta.title;
    els.partSubtitle.textContent = meta.subtitle;

    for (const pill of els.partPills) {
      const pNum = Number(pill.dataset.part);
      pill.classList.toggle('is-active', pNum === state.activePart);
    }

    const disablePrev = state.activePart === 1;
    const disableNext = state.activePart === 7;
    els.prevPartBtn.disabled = disablePrev;
    els.prevPartFooterBtn.disabled = disablePrev;
    els.nextPartBtn.disabled = disableNext;
    els.nextPartFooterBtn.disabled = disableNext;

    if (testData.missing_notes && testData.missing_notes.length > 0 && state.activePart <= 4) {
      els.missingBanner.hidden = false;
      els.missingBanner.innerHTML = `<strong>Source PDF Notice:</strong> ${escapeHtml(testData.missing_notes.join(' '))}`;
    } else {
      els.missingBanner.hidden = true;
    }

    if (state.attempt.submitted && state.attempt.scoreReport) {
      const sr = state.attempt.scoreReport;
      els.reviewBanner.hidden = false;
      els.reviewBanner.innerHTML = `
        <span><strong>Review Mode:</strong> Score ${sr.totalScaled}/990 (Listening ${sr.listeningScaled}, Reading ${sr.readingScaled})</span>
        <button type="button" class="btn btn-outline btn-sm" id="open-score-banner-btn">View Score Report</button>
      `;
    } else {
      els.reviewBanner.hidden = true;
    }

    const incorrectOpt = els.filterSelect.querySelector('option[value="incorrect"]');
    incorrectOpt.disabled = !(state.attempt.submitted || state.reviewMode);
    if (incorrectOpt.disabled && state.filter === 'incorrect') {
      state.filter = 'all';
      els.filterSelect.value = 'all';
    }

    let html = '';

    if (state.activePart === 1) {
      const cards = testData.listening.part1
        .filter(shouldShowQuestion)
        .map((q) => {
          const key = `q${q.number}`;
          const imgHtml = isMissing(q.image)
            ? `<div class="missing-box">Photograph ${escapeHtml(q.image)} — official answer key preserved. Select an option to grade.</div>`
            : `<img class="part1-image" src="${escapeHtml(resolveImagePath(testData.test_id, q.image))}" alt="Part 1 Question ${q.number}">`;

          const scriptHtml = renderScriptPanel(
            key,
            `Question ${q.number}`,
            ['Audio-only photograph description. Listen carefully for subjects, actions, and spatial details in statements (A)-(D).'],
            `Answer: ${q.answer}`,
            q.script || q.transcript || ''
          );

          return `
            <article class="question-card" id="question-${q.number}">
              ${renderQuestionHeader(q.number, 'Listen to the four statements for this photograph.', key)}
              ${imgHtml}
              <div class="options-list">${renderOptionButtons(q, false)}</div>
              ${scriptHtml}
            </article>
          `;
        });
      html = cards.join('');
    } else if (state.activePart === 2) {
      const cards = testData.listening.part2
        .filter(shouldShowQuestion)
        .map((q) => {
          const key = `q${q.number}`;
          const scriptHtml = renderScriptPanel(
            key,
            `Question ${q.number}`,
            ['Audio-only Question-Response item. Listen for WH-words, yes/no cues, or indirect answers across (A)-(C).'],
            `Answer: ${q.answer}`,
            q.script || q.transcript || ''
          );
          return `
            <article class="question-card" id="question-${q.number}">
              ${renderQuestionHeader(q.number, 'Listen to the question or statement and select the best response.', key)}
              <div class="options-list">${renderOptionButtons(q, false)}</div>
              ${scriptHtml}
            </article>
          `;
        });
      html = cards.join('');
    } else if (state.activePart === 3 || state.activePart === 4) {
      const groups = state.activePart === 3 ? testData.listening.part3 : testData.listening.part4;
      const cards = groups
        .filter((g) => g.questions.some(shouldShowQuestion))
        .map((g) => {
          const scriptKey = g.group_id;
          const groupScriptVisible = state.showScript || state.openScripts.has(scriptKey);
          const hideText = state.blindListening && !groupScriptVisible;
          const visibleQs = g.questions.filter(shouldShowQuestion);

          let leftPane = '';
          if (g.image) {
            leftPane = isMissing(g.image)
              ? `<div class="passage-pane"><div class="missing-box">Graphic ${escapeHtml(g.image)} — official answers preserved.</div></div>`
              : `<div class="passage-pane"><div class="graphic-frame"><img src="${escapeHtml(resolveImagePath(testData.test_id, g.image))}" alt="Listening ${escapeHtml(g.group_id)} graphic"></div></div>`;
          }

          const qHtml = visibleQs
            .map((q) => {
              const prompt = hideText
                ? '<span class="muted-text">[Blind mode active — enable Listening Script or Show Script to view prompt]</span>'
                : isMissing(q.question)
                  ? `<span class="muted-text">${escapeHtml(q.question)}</span>`
                  : escapeHtml(q.question);
              return `
                <div class="q-item" id="question-${q.number}">
                  ${renderQuestionHeader(q.number, prompt, null)}
                  <div class="options-list">${renderOptionButtons(q, hideText)}</div>
                </div>
              `;
            })
            .join('');

          const breakdown = g.questions.map((q) => {
            const qText = isMissing(q.question) ? '[missing in source PDF]' : escapeHtml(q.question);
            const optsText = Object.entries(q.options)
              .map(([k, v]) => `(${k}) ${escapeHtml(v)}`)
              .join(' | ');
            return `<strong>Q${q.number}:</strong> ${qText}<br><span class="muted-text">${optsText}</span>`;
          });
          const ansSummary = g.questions.map((q) => `${q.number}:${q.answer}`).join(' ');
          const scriptHtml = renderScriptPanel(scriptKey, g.group_id.toUpperCase(), breakdown, ansSummary, g.script || g.transcript || '');

          return `
            <article class="group-card">
              <div class="group-directions">
                <span>Questions ${escapeHtml(g.group_id.replace('q', ''))}</span>
                <button type="button" class="btn btn-outline btn-xs" data-toggle-script="${escapeHtml(scriptKey)}">
                  ${groupScriptVisible ? 'Hide Script' : 'Show Script'}
                </button>
              </div>
              <div class="split-pane ${leftPane ? 'has-left' : ''}">
                ${leftPane}
                <div class="questions-pane">${qHtml}</div>
              </div>
              ${scriptHtml}
            </article>
          `;
        });
      html = cards.join('');
    } else if (state.activePart === 5) {
      const cards = testData.reading.part5
        .filter(shouldShowQuestion)
        .map((q) => `
          <article class="question-card" id="question-${q.number}">
            ${renderQuestionHeader(q.number, escapeHtml(q.question))}
            <div class="options-list">${renderOptionButtons(q, false)}</div>
          </article>
        `);
      html = cards.join('');
    } else if (state.activePart === 6) {
      const cards = testData.reading.part6
        .filter((g) => g.questions.some(shouldShowQuestion))
        .map((g) => {
          const passageHtml = isMissing(g.passage)
            ? `<div class="missing-box">${escapeHtml(g.passage)}</div>`
            : `<div class="passage-box"><div class="passage-body">${formatPassageContent(g.passage)}</div></div>`;
          const qsHtml = g.questions
            .filter(shouldShowQuestion)
            .map((q) => `
              <div class="q-item" id="question-${q.number}">
                ${renderQuestionHeader(q.number, `Blank ${escapeHtml(q.question)}`)}
                <div class="options-list">${renderOptionButtons(q, false)}</div>
              </div>
            `)
            .join('');
          return `
            <article class="group-card">
              <div class="group-directions"><span>${escapeHtml(g.directions)}</span></div>
              <div class="split-pane has-left">
                <div class="passage-pane is-scrollable">${passageHtml}</div>
                <div class="questions-pane">${qsHtml}</div>
              </div>
            </article>
          `;
        });
      html = cards.join('');
    } else if (state.activePart === 7) {
      const cards = testData.reading.part7
        .filter((g) => g.questions.some(shouldShowQuestion))
        .map((g) => {
          const passagesHtml = g.passages
            .map((p) => `
              <div class="passage-box">
                <div class="passage-box-header">
                  <h3 class="passage-title">${escapeHtml(p.title || p.type)}</h3>
                  <span class="badge">${escapeHtml(p.type)}</span>
                </div>
                <div class="passage-body">${formatPassageContent(p.content)}</div>
              </div>
            `)
            .join('');
          const qsHtml = g.questions
            .filter(shouldShowQuestion)
            .map((q) => `
              <div class="q-item" id="question-${q.number}">
                ${renderQuestionHeader(q.number, escapeHtml(q.question))}
                <div class="options-list">${renderOptionButtons(q, false)}</div>
              </div>
            `)
            .join('');
          return `
            <article class="group-card">
              <div class="group-directions"><span>${escapeHtml(g.directions)}</span></div>
              <div class="split-pane has-left">
                <div class="passage-pane is-scrollable">${passagesHtml}</div>
                <div class="questions-pane">${qsHtml}</div>
              </div>
            </article>
          `;
        });
      html = cards.join('');
    }

    if (!html) {
      html = `<div class="question-card"><p class="muted-text" style="margin:0;">No questions in Part ${state.activePart} match the current filter (${escapeHtml(state.filter)}).</p></div>`;
    }

    els.questionsContainer.innerHTML = html;

    const bannerBtn = document.getElementById('open-score-banner-btn');
    if (bannerBtn) {
      bannerBtn.addEventListener('click', () => openScoreReport(state.attempt.scoreReport));
    }
  }

  async function openTest(testId, part = 1) {
    try {
      const testData = await loadTestData(testId);
      state.activeTestId = testId;
      state.activePart = part;
      state.attempt = readJsonStorage(STORAGE.attempt(testId), defaultAttempt());
      state.scripts = readJsonStorage(STORAGE.scripts(testId), {});
      state.reviewMode = Boolean(state.attempt.submitted);
      state.timerPaused = false;
      state.openScripts.clear();
      state.revealedKeys.clear();
      savePreferences();

      els.testSelect.value = String(testId);
      els.modeSelect.value = state.mode;
      els.scriptToggle.checked = state.showScript;
      els.blindToggle.checked = state.blindListening;

      els.overviewView.hidden = true;
      els.testView.hidden = false;
      els.testControls.hidden = false;
      els.partNav.hidden = false;

      syncAudioForTest(testData);
      updateAnsweredBadge();
      renderPalette();
      renderActivePart();
      startTimer();
    } catch (err) {
      alert(`Could not load Test ${testId}: ${err.message}`);
    }
  }

  function switchPart(partNum, scrollQuestion = null) {
    if (!state.activeTestId || partNum < 1 || partNum > 7) return;
    state.activePart = partNum;
    savePreferences();
    updateAudioBarVisibility();
    updateTimerDisplay();
    renderActivePart();

    if (scrollQuestion) {
      const target = document.getElementById(`question-${scrollQuestion}`);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function openScoreReport(report) {
    if (!report) return;
    const partRows = report.partBreakdown
      .map((row) => {
        const pct = Math.round((row.correct / row.total) * 100);
        return `
          <tr>
            <td>Part ${row.part}</td>
            <td>${row.correct} / ${row.total}</td>
            <td>${pct}%</td>
          </tr>
        `;
      })
      .join('');

    els.scoreBody.innerHTML = `
      <div class="score-summary-grid">
        <div class="score-tile is-total">
          <div class="score-tile-label">Total Score</div>
          <div class="score-tile-value">${report.totalScaled} <span style="font-size:0.9rem;font-weight:500;">/ 990</span></div>
          <div class="score-tile-sub">Answered ${report.answered} / 200</div>
        </div>
        <div class="score-tile">
          <div class="score-tile-label">Listening</div>
          <div class="score-tile-value">${report.listeningScaled} <span style="font-size:0.9rem;font-weight:500;">/ 495</span></div>
          <div class="score-tile-sub">${report.listeningRaw} / 100 correct</div>
        </div>
        <div class="score-tile">
          <div class="score-tile-label">Reading</div>
          <div class="score-tile-value">${report.readingScaled} <span style="font-size:0.9rem;font-weight:500;">/ 495</span></div>
          <div class="score-tile-sub">${report.readingRaw} / 100 correct</div>
        </div>
      </div>
      <p class="muted-text" style="margin:0 0 0.75rem;font-size:0.85rem;">
        Mode: ${report.mode === 'official' ? 'Official Timed' : 'Practice'} | Time recorded: ${formatSec(report.elapsedSec)}
      </p>
      <table class="data-table">
        <thead>
          <tr><th>Section Part</th><th>Correct</th><th>Accuracy</th></tr>
        </thead>
        <tbody>${partRows}</tbody>
      </table>
    `;
    els.scoreDialog.showModal();
  }

  function submitCurrentTest(autoSubmitted = false) {
    if (!state.activeTestId || !state.attempt) return;
    const testData = state.testCache.get(state.activeTestId);
    if (!testData) return;

    stopTimer();
    els.audioEl.pause();
    const report = computeScoreReport(testData, state.attempt);
    state.attempt.submitted = true;
    state.attempt.scoreReport = report;
    state.reviewMode = true;
    saveAttempt();

    const history = readJsonStorage(STORAGE.history, []);
    history.unshift({ ...report, autoSubmitted });
    writeJsonStorage(STORAGE.history, history.slice(0, 100));

    updateTimerDisplay();
    renderPalette();
    renderActivePart();
    openScoreReport(report);
  }

  function bindEvents() {
    els.homeBtn.addEventListener('click', renderOverview);

    els.testSelect.addEventListener('change', (e) => {
      const val = e.target.value;
      if (val === 'overview') renderOverview();
      else openTest(Number(val), 1);
    });

    els.modeSelect.addEventListener('change', (e) => {
      state.mode = e.target.value;
      savePreferences();
      startTimer();
    });

    els.timerToggleBtn.addEventListener('click', () => {
      state.timerPaused = !state.timerPaused;
      updateTimerDisplay();
    });

    els.scriptToggle.addEventListener('change', (e) => {
      state.showScript = Boolean(e.target.checked);
      if (e.target.hasAttribute('role')) {
        e.target.setAttribute('aria-checked', String(state.showScript));
      }
      savePreferences();
      renderActivePart();
    });

    els.blindToggle.addEventListener('change', (e) => {
      state.blindListening = Boolean(e.target.checked);
      savePreferences();
      renderActivePart();
    });

    els.filterSelect.addEventListener('change', (e) => {
      state.filter = e.target.value;
      renderActivePart();
    });

    for (const pill of els.partPills) {
      pill.addEventListener('click', () => switchPart(Number(pill.dataset.part)));
    }

    const goPrev = () => switchPart(state.activePart - 1);
    const goNext = () => switchPart(state.activePart + 1);
    els.prevPartBtn.addEventListener('click', goPrev);
    els.prevPartFooterBtn.addEventListener('click', goPrev);
    els.nextPartBtn.addEventListener('click', goNext);
    els.nextPartFooterBtn.addEventListener('click', goNext);

    els.questionsContainer.addEventListener('click', (e) => {
      const optBtn = e.target.closest('[data-opt]');
      if (optBtn && !state.attempt.submitted) {
        const qNum = String(optBtn.dataset.q);
        const opt = optBtn.dataset.opt;
        if (state.attempt.answers[qNum] === opt) {
          delete state.attempt.answers[qNum];
        } else {
          state.attempt.answers[qNum] = opt;
        }
        saveAttempt();
        updateAnsweredBadge();
        renderPalette();
        renderActivePart();
        return;
      }

      const flagBtn = e.target.closest('[data-flag]');
      if (flagBtn) {
        const qNum = Number(flagBtn.dataset.flag);
        const flags = new Set(state.attempt.flags || []);
        if (flags.has(qNum)) flags.delete(qNum);
        else flags.add(qNum);
        state.attempt.flags = Array.from(flags).sort((a, b) => a - b);
        saveAttempt();
        renderPalette();
        renderActivePart();
        return;
      }

      const scriptBtn = e.target.closest('[data-toggle-script]');
      if (scriptBtn) {
        const key = scriptBtn.dataset.toggleScript;
        if (state.openScripts.has(key)) state.openScripts.delete(key);
        else state.openScripts.add(key);
        renderActivePart();
        return;
      }

      const revealBtn = e.target.closest('[data-reveal-key]');
      if (revealBtn) {
        state.revealedKeys.add(revealBtn.dataset.revealKey);
        renderActivePart();
      }
    });

    els.questionsContainer.addEventListener('input', (e) => {
      const ta = e.target.closest('[data-script-note]');
      if (!ta) return;
      state.scripts[ta.dataset.scriptNote] = ta.value;
      saveScripts();
    });

    const handlePaletteJump = (e) => {
      const cell = e.target.closest('[data-jump-part]');
      if (!cell) return;
      const part = Number(cell.dataset.jumpPart);
      const qNum = Number(cell.dataset.jumpQ);
      if (els.paletteDialog.open) els.paletteDialog.close();
      switchPart(part, qNum);
    };
    els.desktopPalette.addEventListener('click', handlePaletteJump);
    els.modalPalette.addEventListener('click', handlePaletteJump);

    els.paletteOpenBtn.addEventListener('click', () => els.paletteDialog.showModal());
    els.mobilePaletteBtn.addEventListener('click', () => els.paletteDialog.showModal());
    els.paletteCloseBtn.addEventListener('click', () => els.paletteDialog.close());

    els.submitBtn.addEventListener('click', () => submitCurrentTest(false));
    els.sidebarSubmitBtn.addEventListener('click', () => submitCurrentTest(false));
    els.scoreCloseBtn.addEventListener('click', () => els.scoreDialog.close());
    els.reviewModeBtn.addEventListener('click', () => {
      state.reviewMode = true;
      els.scoreDialog.close();
      renderActivePart();
    });
    els.scoreOverviewBtn.addEventListener('click', () => {
      els.scoreDialog.close();
      renderOverview();
    });

    els.resetBtn.addEventListener('click', () => els.resetDialog.showModal());
    els.resetDialog.addEventListener('close', () => {
      const choice = els.resetDialog.returnValue;
      els.resetDialog.returnValue = '';
      if (choice === 'confirm' && state.activeTestId) {
        state.attempt = defaultAttempt();
        state.reviewMode = false;
        saveAttempt();
        els.audioEl.pause();
        els.audioEl.currentTime = 0;
        updateAnsweredBadge();
        renderPalette();
        renderActivePart();
        startTimer();
      }
    });

    els.testGrid.addEventListener('click', (e) => {
      const openBtn = e.target.closest('[data-open-test]');
      if (openBtn) {
        openTest(Number(openBtn.dataset.openTest), 1);
        return;
      }
      const clearBtn = e.target.closest('[data-clear-test]');
      if (clearBtn) {
        const id = Number(clearBtn.dataset.clearTest);
        localStorage.removeItem(STORAGE.attempt(id));
        renderOverview();
      }
    });

    els.clearHistoryBtn.addEventListener('click', () => {
      localStorage.removeItem(STORAGE.history);
      renderOverview();
    });

    els.exportBtn.addEventListener('click', () => {
      const payload = { exportedAt: new Date().toISOString(), data: {} };
      for (let i = 0; i < localStorage.length; i += 1) {
        const k = localStorage.key(i);
        if (k && k.startsWith('toeic_')) {
          payload.data[k] = localStorage.getItem(k);
        }
      }
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `toeic-progress-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    });

    els.importInput.addEventListener('change', async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      try {
        const parsed = JSON.parse(await file.text());
        if (parsed && typeof parsed.data === 'object') {
          for (const [k, v] of Object.entries(parsed.data)) {
            if (k.startsWith('toeic_') && typeof v === 'string') {
              localStorage.setItem(k, v);
            }
          }
          renderOverview();
        }
      } catch {
        alert('Invalid progress backup JSON file.');
      } finally {
        els.importInput.value = '';
      }
    });

    // Audio controls
    els.audioPlayBtn.addEventListener('click', () => {
      if (els.audioEl.paused) {
        els.audioEl.play().catch(() => {});
      } else {
        els.audioEl.pause();
      }
    });

    els.audioBackBtn.addEventListener('click', () => {
      els.audioEl.currentTime = Math.max(0, els.audioEl.currentTime - 5);
    });

    els.audioFwdBtn.addEventListener('click', () => {
      const dur = Number.isFinite(els.audioEl.duration) ? els.audioEl.duration : els.audioEl.currentTime + 5;
      els.audioEl.currentTime = Math.min(dur, els.audioEl.currentTime + 5);
    });

    els.audioRate.addEventListener('change', (e) => {
      els.audioEl.playbackRate = Number(e.target.value);
    });

    els.audioSeek.addEventListener('input', (e) => {
      const dur = els.audioEl.duration;
      if (Number.isFinite(dur) && dur > 0) {
        els.audioEl.currentTime = (Number(e.target.value) / 100) * dur;
      }
    });

    els.audioEl.addEventListener('play', () => {
      els.audioPlayBtn.textContent = 'Pause';
    });

    els.audioEl.addEventListener('pause', () => {
      els.audioPlayBtn.textContent = 'Play';
    });

    els.audioEl.addEventListener('loadedmetadata', () => {
      if (state.attempt && state.attempt.audioTime > 0 && state.attempt.audioTime < els.audioEl.duration) {
        els.audioEl.currentTime = state.attempt.audioTime;
      }
      els.audioTime.textContent = `${formatSec(els.audioEl.currentTime)} / ${formatSec(els.audioEl.duration || 0)}`;
    });

    els.audioEl.addEventListener('timeupdate', () => {
      const cur = els.audioEl.currentTime || 0;
      const dur = els.audioEl.duration || 0;
      els.audioTime.textContent = `${formatSec(cur)} / ${formatSec(dur)}`;
      if (dur > 0) {
        els.audioSeek.value = String((cur / dur) * 100);
      }
      const now = Date.now();
      if (state.attempt && now - state.lastAudioSave > 1500) {
        state.lastAudioSave = now;
        state.attempt.audioTime = cur;
        saveAttempt();
      }
    });
  }

  async function init() {
    setupProgressiveFallbacks();
    bindEvents();

    const res = await fetch('extracted/index.json');
    const catalog = await res.json();
    state.index = catalog.tests || [];

    for (const t of state.index) {
      const opt = document.createElement('option');
      opt.value = String(t.test_id);
      opt.textContent = `Test ${String(t.test_id).padStart(2, '0')}${t.complete ? '' : ' (Partial)'}`;
      els.testSelect.appendChild(opt);
    }

    const prefs = readJsonStorage(STORAGE.active, null);
    if (prefs) {
      state.mode = prefs.mode || 'official';
      state.showScript = Boolean(prefs.showScript);
      state.blindListening = Boolean(prefs.blindListening);
      els.modeSelect.value = state.mode;
      els.scriptToggle.checked = state.showScript;
      els.blindToggle.checked = state.blindListening;
      if (prefs.activeTestId) {
        await openTest(prefs.activeTestId, prefs.activePart || 1);
        return;
      }
    }

    renderOverview();
  }

  init();
})();
