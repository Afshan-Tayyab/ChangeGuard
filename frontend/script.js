// Check if user is logged in
const user = localStorage.getItem('user');
if (!user) {
    window.location.href = '/login';
} else {
    const welcomeEl = document.getElementById('welcomeUser');
    if (welcomeEl) welcomeEl.innerText = user;
}

// Navigation
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
    document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove('active'));
    
    document.getElementById('page-' + pageId).style.display = 'block';
    const navId = 'nav-' + (pageId === 'dashboard' ? 'dash' : pageId);
    const activeLink = document.getElementById(navId);
    if (activeLink) activeLink.classList.add('active');

    if (pageId === 'dashboard') fetchStats();
    if (pageId === 'history') fetchHistory();
}

function logout() {
    localStorage.removeItem('user');
    window.location.href = '/login';
}

async function fetchStats() {
    try {
        const res = await fetch('/dashboard-stats');
        const data = await res.json();
        document.getElementById('totalComparisons').innerText = data.total_comparisons;
    } catch (e) { console.error(e); }
}

async function fetchHistory() {
    const container = document.getElementById('historyContainer');
    try {
        const res = await fetch('/history');
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<p>No history yet. Start a comparison!</p>';
            return;
        }
        let html = '<table style="width:100%; border-collapse: collapse; text-align:left;">';
        html += '<tr style="background:#2c3e50; color:white;"><th style="padding:12px;">ID</th><th>Old Document</th><th>New Document</th><th>Date</th></tr>';
        data.forEach(item => {
            html += `<tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">${item.id}</td><td>${item.old_filename}</td><td>${item.new_filename}</td><td>${new Date(item.timestamp).toLocaleString()}</td></tr>`;
        });
        html += '</table>';
        container.innerHTML = html;
    } catch (e) { container.innerHTML = 'Error loading history.'; }
}

async function compareDocuments() {
    const oldFile = document.getElementById('oldFile').files[0];
    const newFile = document.getElementById('newFile').files[0];

    if (!oldFile || !newFile) {
        alert("Please upload both Old and New documents.");
        return;
    }

    const formData = new FormData();
    formData.append("old_file", oldFile);
    formData.append("new_file", newFile);

    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('resultsContainer').innerHTML = '';

    try {
        const response = await fetch('/compare-files', { method: 'POST', body: formData });
        const data = await response.json();
        
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('resultsSection').classList.remove('hidden');

        const container = document.getElementById('resultsContainer');
        container.innerHTML = `<div style="margin-bottom: 15px; padding: 12px; background: #e8f8f5; border-radius: 5px; border-left: 4px solid #27ae60;"><strong>Old:</strong> ${data.old_filename} &nbsp;|&nbsp; <strong>New:</strong> ${data.new_filename}</div>`;

        data.comparison.forEach(item => {
            const card = document.createElement('div');
            card.className = `result-card ${item.status.toLowerCase()}`;
            let html = `<span class="status-badge status-${item.status.toLowerCase()}">${item.status}</span>`;

            if (item.status === 'Modified' || item.status === 'Unchanged') {
                const cleanOld = item.old_sentence.replace(/^[\s:]+/, '');
                const cleanNew = item.new_sentence.replace(/^[\s:]+/, '');
                html += `<div class="sentence-compare"><div class="old-sent"><strong>Old:</strong> ${cleanOld}</div><div class="new-sent"><strong>New:</strong> ${cleanNew}</div></div>`;
                
                if (item.status === 'Modified') {
                    item.changes_detected.forEach(change => {
                        html += `<div class="change-detail"><strong>${change.type}:</strong><br><strong>Old:</strong> ${change.old} | <strong>New:</strong> ${change.new}<br><em>Impact:</em> ${change.impact}</div>`;
                    });
                } else {
                    html += `<p style="color: #27ae60; margin-top: 10px; font-weight: bold;">✔ Status: Unchanged</p>`;
                }
            } else if (item.status === 'Deleted') {
                html += `<p><strong>Deleted:</strong> ${item.old_sentence}</p>`;
            } else if (item.status === 'Added') {
                html += `<p><strong>Added:</strong> ${item.new_sentence}</p>`;
            }
            card.innerHTML = html;
            container.appendChild(card);
        });
        
        // Refresh dashboard stats after a comparison
        fetchStats();

    } catch (error) {
        document.getElementById('loading').classList.add('hidden');
        alert("Error comparing documents.");
    }
}

// Initialize dashboard on load
fetchStats();