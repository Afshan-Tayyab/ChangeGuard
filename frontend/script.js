// Show selected filename
document.getElementById('oldFile').addEventListener('change', function(e) {
    document.getElementById('oldFileName').textContent = e.target.files[0] ? e.target.files[0].name : "No file selected";
});
document.getElementById('newFile').addEventListener('change', function(e) {
    document.getElementById('newFileName').textContent = e.target.files[0] ? e.target.files[0].name : "No file selected";
});

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
        // NOTE: Change this URL to your Render URL later (e.g. https://changeguard.onrender.com/compare-files)
        const response = await fetch('http://127.0.0.1:8000/compare-files', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Server error");
        }

        const data = await response.json();
        
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('resultsSection').classList.remove('hidden');

        const container = document.getElementById('resultsContainer');
        
        let headerHtml = `
            <div style="margin-bottom: 15px; padding: 10px; background: #e8f8f5; border-radius: 5px;">
                <strong>Old File:</strong> ${data.old_filename} &nbsp;|&nbsp; <strong>New File:</strong> ${data.new_filename}
            </div>
        `;
        container.innerHTML = headerHtml;

        if (data.comparison.length === 0) {
            container.innerHTML += '<p>No changes detected between documents.</p>';
            return;
        }

        data.comparison.forEach(item => {
            const card = document.createElement('div');
            card.className = `result-card ${item.status.toLowerCase()}`;

            let html = `<span class="status-badge status-${item.status.toLowerCase()}">${item.status}</span>`;

            if (item.status === 'Modified' || item.status === 'Unchanged') {
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
            } else if (item.status === 'Deleted') {
                html += `<p><strong>Deleted Sentence:</strong> ${item.old_sentence}</p>`;
            } else if (item.status === 'Added') {
                html += `<p><strong>Added Sentence:</strong> ${item.new_sentence}</p>`;
            }

            card.innerHTML = html;
            container.appendChild(card);
        });

    } catch (error) {
        document.getElementById('loading').classList.add('hidden');
        alert("Error: " + error.message);
        console.error(error);
    }
}