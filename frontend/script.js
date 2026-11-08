async function compareDocuments() {
    const oldText = document.getElementById('oldText').value;
    const newText = document.getElementById('newText').value;

    if (!oldText.trim() || !newText.trim()) {
        alert("Please enter text in both boxes.");
        return;
    }

    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('resultsContainer').innerHTML = '';

    try {
        const response = await fetch('https://your-render-url.onrender.com/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_text: oldText, new_text: newText })
        });

        const data = await response.json();
        
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('resultsSection').classList.remove('hidden');

        const container = document.getElementById('resultsContainer');

        if (data.comparison.length === 0) {
            container.innerHTML = '<p>No changes detected between documents.</p>';
            return;
        }

        data.comparison.forEach(item => {
            const card = document.createElement('div');
            card.className = `result-card ${item.status.toLowerCase()}`;

            let html = `<span class="status-badge status-${item.status.toLowerCase()}">${item.status}</span>`;

            if (item.status === 'Modified' || item.status === 'Unchanged') {
                // FIX: This safely trims leading spaces/colons that caused the extra ":"
                const cleanOld = item.old_sentence.replace(/^[\s:]+/, '');
                const cleanNew = item.new_sentence.replace(/^[\s:]+/, '');
                
                html += `
                    <div class="sentence-compare">
                        <div class="old-sent"><strong>Old:</strong> ${cleanOld}</div>
                        <div class="new-sent"><strong>New:</strong> ${cleanNew}</div>
                    </div>
                `;
                
                if (item.status === 'Modified') {
                    item.changes_detected.forEach(change => {
                        html += `
                            <div class="change-detail">
                                <strong>${change.type}:</strong><br>
                                <strong>Old:</strong> ${change.old} <br>
                                <strong>New:</strong> ${change.new} <br>
                                <em>Impact:</em> ${change.impact}
                            </div>
                        `;
                    });
                } else {
                    html += `<p style="color: #27ae60; margin-top: 10px;"><strong>✔ Status: Unchanged</strong> - No semantic changes detected.</p>`;
                }
            } 
            else if (item.status === 'Deleted') {
                html += `<p><strong>Deleted Sentence:</strong> ${item.old_sentence}</p>`;
            } 
            else if (item.status === 'Added') {
                html += `<p><strong>Added Sentence:</strong> ${item.new_sentence}</p>`;
            }

            card.innerHTML = html;
            container.appendChild(card);
        });

    } catch (error) {
        document.getElementById('loading').classList.add('hidden');
        alert("Error connecting to backend. Make sure the server is running.");
        console.error(error);
    }
}