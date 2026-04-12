document.addEventListener('DOMContentLoaded', () => {
    const taskBtns = document.querySelectorAll('.task-btn');
    const runBtn = document.getElementById('run-task-btn');
    const apiKeyInput = document.getElementById('api-key');
    const transcript = document.getElementById('transcript');
    const inspectorLoader = document.getElementById('inspector-loader');
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;
    
    const scoreVal = document.getElementById('current-score');
    const stepsVal = document.getElementById('steps-taken');
    const rewardVal = document.getElementById('avg-reward');

    let currentTask = 'easy';
    let currentProvider = 'openai';
    let totalRewards = [];

    // Provider Selection
    const providerBtns = document.querySelectorAll('.provider-btn');
    providerBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            providerBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentProvider = btn.dataset.provider;
            apiKeyInput.placeholder = currentProvider === 'openai' ? 'OpenAI API Key' : 'Groq API Key';
        });
    });

    // Theme Toggle Logic
    themeToggle.addEventListener('click', () => {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', newTheme);
        
        // Switch Icons
        document.getElementById('sun-icon').style.display = newTheme === 'light' ? 'block' : 'none';
        document.getElementById('moon-icon').style.display = newTheme === 'dark' ? 'block' : 'none';
    });

    // Task Selection
    taskBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            taskBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentTask = btn.dataset.task;
            
            if (currentTask === 'interactive') {
                document.getElementById('interactive-input-area').style.display = 'flex';
                runBtn.textContent = 'ANALYZE REVIEW';
                // Clear the default filler text to make it look clean
                if (totalRewards.length === 0) transcript.innerHTML = '';
            } else {
                document.getElementById('interactive-input-area').style.display = 'none';
                runBtn.textContent = 'RUN INSPECTION';
            }
        });
    });

    function resetUI() {
        transcript.innerHTML = '';
        totalRewards = [];
        scoreVal.textContent = '0.00';
        stepsVal.textContent = '0 / 0';
        rewardVal.textContent = '0.00';
        inspectorLoader.style.display = 'block';
        runBtn.disabled = true;
    }

    function addEntry(data) {
        const step = data.step;
        const reward = data.reward;
        const review = data.review;
        const action = data.action;

        if (step !== 'MANUAL') {
            totalRewards.push(reward);
        }
        
        const entry = document.createElement('div');
        entry.className = 'entry';
        
        const showReward = step !== 'MANUAL' || data.hasExpected;
        
        const category = data.action.category || "Safe";
        const categoryClass = category.toLowerCase();
        
        entry.innerHTML = `
            <div class="entry-header">
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    <span>${step === 'MANUAL' ? 'CUSTOM INPUT' : 'STEP ' + step}</span>
                    <span class="category-badge ${categoryClass}">${category.toUpperCase()}</span>
                </div>
                ${step === 'MANUAL' ? '' : `<span class="reward-pill">+${reward.toFixed(2)} pts</span>`}
            </div>
            <div class="entry-review">"${review}"</div>
            <div class="reason-box">
                <span class="reason-label">POLICY REASONING</span>
                <p class="reason-text">${data.action.reason || "Analyzing policy compliance..."}</p>
            </div>
            <div class="entry-tags">
                <div class="tag">
                    <span class="tag-label">SENTIMENT</span>
                    <span class="sentiment-val ${action.sentiment}">${action.sentiment.toUpperCase()}</span>
                </div>
                <div class="tag">
                    <span class="tag-label">DECISION</span>
                    <span class="decision-val ${action.decision}">${action.decision.toUpperCase()}</span>
                </div>
            </div>
            ${step === 'MANUAL' ? '' : `
            <div class="reward-bar-container">
                <div class="reward-bar-fill" style="width: ${reward * 100}%"></div>
            </div>`}
        `;

        transcript.prepend(entry);
        
        // Update stats
        if (step !== 'MANUAL' && totalRewards.length > 0) {
            const avg = totalRewards.reduce((a, b) => a + b, 0) / totalRewards.length;
            rewardVal.textContent = avg.toFixed(2);
            stepsVal.textContent = `${totalRewards.length} / ${data.total_steps || '?'}`;
        }
    }

    runBtn.addEventListener('click', async () => {
        const apiKey = apiKeyInput.value.trim();
        if (!apiKey) {
            alert('API Key required for moderation simulation.');
            return;
        }

        if (currentTask === 'interactive') {
            const reviewText = document.getElementById('custom-review-text').value.trim();
            if (!reviewText) {
                alert('Please type a review to analyze.');
                return;
            }
            
            const expectedSentiment = document.getElementById('expected-sentiment').value;
            const expectedDecision = document.getElementById('expected-decision').value;
            
            inspectorLoader.style.display = 'block';
            runBtn.disabled = true;

            fetch('/analyze-custom-review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    api_key: apiKey,
                    provider: currentProvider,
                    review: reviewText,
                    expected_sentiment: expectedSentiment || null,
                    expected_decision: expectedDecision || null
                })
            })
            .then(res => {
                if (!res.ok) return res.json().then(err => { throw new Error(err.detail || 'Analysis error'); });
                return res.json();
            })
            .then(action => {
                const entryData = {
                    step: 'MANUAL',
                    reward: action.reward || 0.0,
                    hasExpected: !!(expectedSentiment && expectedDecision),
                    review: reviewText,
                    action: action,
                    total_steps: 'N/A'
                };
                addEntry(entryData);
                document.getElementById('custom-review-text').value = '';
                document.getElementById('expected-sentiment').value = '';
                document.getElementById('expected-decision').value = '';
            })
            .catch(err => {
                alert('System Error: ' + err.message);
            })
            .finally(() => {
                inspectorLoader.style.display = 'none';
                runBtn.disabled = false;
            });
            return;
        }

        resetUI();

        // Connect to SSE endpoint
        const eventSource = new EventSource(`/run-task?task=${currentTask}&api_key=${encodeURIComponent(apiKey)}&provider=${currentProvider}`);

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'start') {
                console.log('Inspection started');
            } else if (data.type === 'step') {
                addEntry(data);
            } else if (data.type === 'end') {
                scoreVal.textContent = data.score.toFixed(2);
                inspectorLoader.style.display = 'none';
                runBtn.disabled = false;
                eventSource.close();
            } else if (data.type === 'error') {
                alert('System Error: ' + data.message);
                inspectorLoader.style.display = 'none';
                runBtn.disabled = false;
                eventSource.close();
            }
        };

        eventSource.onerror = (err) => {
            inspectorLoader.style.display = 'none';
            runBtn.disabled = false;
            eventSource.close();
        };
    });
});
