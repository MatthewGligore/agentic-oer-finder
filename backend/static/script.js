document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const resultsSection = document.getElementById('resultsSection');
    const loadingSection = document.getElementById('loadingSection');
    const errorSection = document.getElementById('errorSection');
    const resultsContainer = document.getElementById('resultsContainer');
    const searchBtn = document.getElementById('searchBtn');

    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const courseCode = document.getElementById('courseCode').value.trim().toUpperCase();
        const term = document.getElementById('term').value.trim();
        
        // Hide previous results/errors
        resultsSection.style.display = 'none';
        errorSection.style.display = 'none';
        
        // Show loading
        loadingSection.style.display = 'block';
        searchBtn.disabled = true;
        searchBtn.textContent = 'Searching...';
        
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    course_code: courseCode,
                    term: term
                })
            });
            
            const data = await response.json();
            
            // Hide loading
            loadingSection.style.display = 'none';
            searchBtn.disabled = false;
            searchBtn.textContent = 'Search OER Resources';
            
            if (!response.ok) {
                throw new Error(data.error || 'Search failed');
            }
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            // Debug logging
            console.log('Search results:', data);
            console.log('Evaluated resources count:', data.evaluated_resources ? data.evaluated_resources.length : 0);
            console.log('Resources found:', data.resources_found || 0);
            console.log('Resources evaluated:', data.resources_evaluated || 0);
            
            displayResults(data);
            
        } catch (error) {
            loadingSection.style.display = 'none';
            searchBtn.disabled = false;
            searchBtn.textContent = 'Search OER Resources';
            showError(error.message || 'An error occurred while searching for OER resources.');
        }
    });
    
    function showError(message) {
        errorSection.style.display = 'block';
        document.getElementById('errorMessage').textContent = message;
    }
    
    function displayResults(data) {
        resultsSection.style.display = 'block';
        
        let html = '';
        
        // Debug
        console.log('Displaying results. evaluated_resources:', data.evaluated_resources);
        console.log('Type of evaluated_resources:', typeof data.evaluated_resources);
        console.log('Is array?', Array.isArray(data.evaluated_resources));
        
        // Summary
        if (data.summary) {
            html += `<div class="summary-box">
                <h3>Search Summary</h3>
                <p>${data.summary.replace(/\n/g, '<br>')}</p>
                <p><small>Processing time: ${data.processing_time_seconds?.toFixed(2)} seconds</small></p>
            </div>`;
        }
        
        // Resources - check multiple ways
        const evaluatedResources = data.evaluated_resources || [];
        const hasResources = Array.isArray(evaluatedResources) && evaluatedResources.length > 0;
        
        console.log('Has resources?', hasResources, 'Count:', evaluatedResources.length);
        
        if (hasResources) {
            evaluatedResources.forEach((item, index) => {
                const resource = item.resource || {};
                const rubricEval = item.rubric_evaluation || {};
                const licenseCheck = item.license_check || {};
                const overallScore = rubricEval.overall_score || 0;
                
                html += `<div class="resource-card">
                    <div class="resource-header">
                        <div>
                            <div class="resource-title">
                                <a href="${resource.url || '#'}" target="_blank">
                                    ${resource.title || 'Untitled Resource'}
                                </a>
                            </div>
                        </div>
                        <div class="quality-score">${overallScore.toFixed(1)}/5.0</div>
                    </div>
                    
                    ${resource.description ? `<div class="resource-description">${resource.description}</div>` : ''}
                    
                    <div class="resource-meta">
                        ${resource.author ? `<div class="meta-item"><strong>Author:</strong> ${resource.author}</div>` : ''}
                        <div class="meta-item">
                            <strong>License:</strong> 
                            <span class="license-badge ${getLicenseClass(licenseCheck.has_open_license)}">
                                ${licenseCheck.license_type || 'Unknown'}
                            </span>
                        </div>
                        ${resource.source ? `<div class="meta-item"><strong>Source:</strong> ${resource.source}</div>` : ''}
                    </div>
                    
                    ${item.integration_guidance ? `
                    <div class="integration-guidance">
                        <h4>Integration Guidance</h4>
                        <p>${item.integration_guidance.replace(/\n/g, '<br>')}</p>
                    </div>
                    ` : ''}
                    
                    ${item.relevance_explanation ? `
                    <div class="integration-guidance">
                        <h4>Relevance to Course</h4>
                        <p>${item.relevance_explanation}</p>
                    </div>
                    ` : ''}
                    
                    ${rubricEval.criteria_evaluations ? `
                    <div class="criteria-scores">
                        <h4>Quality Evaluation</h4>
                        ${Object.entries(rubricEval.criteria_evaluations).map(([criterion, evalData]) => `
                            <div class="criteria-item">
                                <span>${criterion}:</span>
                                <span><strong>${evalData.score || 0}/5</strong></span>
                            </div>
                        `).join('')}
                    </div>
                    ` : ''}
                </div>`;
            });
        } else {
            // Show more helpful message
            html += `<div class="resource-card">
                <p><strong>No OER resources found for this course.</strong></p>
                <p>Resources found: ${data.resources_found || 0}</p>
                <p>Resources evaluated: ${data.resources_evaluated || 0}</p>
                <p>This may be because:</p>
                <ul>
                    <li>The web scrapers need to be customized for the actual website structures</li>
                    <li>The LLM API quota has been exceeded (check your OpenAI account)</li>
                    <li>No matching resources were found in the Open ALG Library</li>
                </ul>
                <p>Check the browser console (F12) for detailed logs.</p>
            </div>`;
        }
        
        resultsContainer.innerHTML = html;
    }
    
    function getLicenseClass(hasOpenLicense) {
        if (hasOpenLicense === true) return 'license-open';
        if (hasOpenLicense === false) return 'license-restrictive';
        return 'license-unknown';
    }
});
