// Configuration de l'API
const API_BASE = '/api';

// Variables globales
let currentHotels = [];
let currentCharts = {};

// Initialisation de l'application
document.addEventListener('DOMContentLoaded', function() {
    loadHotels();
    showSection('dashboard');
});

// Gestion de la navigation
function showSection(sectionName) {
    // Masquer toutes les sections
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Afficher la section demandée
    document.getElementById(sectionName + '-section').style.display = 'block';
    
    // Mettre à jour la navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Charger les données spécifiques à la section
    switch(sectionName) {
        case 'hotels':
            loadHotelsTable();
            break;
        case 'reports':
            populateReportSelectors();
            break;
        case 'automation':
            populateAutomationSelectors();
            break;
    }
}

// Gestion des hôtels
async function loadHotels() {
    try {
        const response = await fetch(`${API_BASE}/hotels`);
        const hotels = await response.json();
        currentHotels = hotels;
        
        // Mettre à jour tous les sélecteurs d'hôtels
        updateHotelSelectors(hotels);
        
    } catch (error) {
        console.error('Erreur lors du chargement des hôtels:', error);
        showAlert('Erreur lors du chargement des hôtels', 'danger');
    }
}

function updateHotelSelectors(hotels) {
    const selectors = [
        'hotel-selector',
        'responses-hotel-selector',
        'analytics-hotel-selector',
        'export-hotel-selector',
        'automation-hotel',
        'test-hotel-selector'
    ];
    
    selectors.forEach(selectorId => {
        const selector = document.getElementById(selectorId);
        if (selector) {
            // Garder la première option
            const firstOption = selector.querySelector('option');
            selector.innerHTML = '';
            selector.appendChild(firstOption);
            
            // Ajouter les hôtels
            hotels.forEach(hotel => {
                const option = document.createElement('option');
                option.value = hotel.id;
                option.textContent = hotel.name;
                selector.appendChild(option);
            });
        }
    });
}

async function loadHotelsTable() {
    try {
        const tbody = document.getElementById('hotels-table-body');
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">Chargement...</td></tr>';
        
        const hotels = currentHotels;
        tbody.innerHTML = '';
        
        if (hotels.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Aucun hôtel trouvé</td></tr>';
            return;
        }
        
        hotels.forEach(hotel => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${hotel.name}</strong></td>
                <td>${hotel.location || '-'}</td>
                <td>
                    ${hotel.tally_form_url ? 
                        `<a href="${hotel.tally_form_url}" target="_blank" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-external-link-alt"></i>
                        </a>` : 
                        '<span class="text-muted">Non configuré</span>'
                    }
                </td>
                <td>
                    ${hotel.google_sheet_url ? 
                        `<a href="${hotel.google_sheet_url}" target="_blank" class="btn btn-sm btn-outline-success">
                            <i class="fas fa-table"></i>
                        </a>` : 
                        '<span class="text-muted">Non créé</span>'
                    }
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteHotel(${hotel.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Erreur lors du chargement du tableau des hôtels:', error);
        showAlert('Erreur lors du chargement du tableau', 'danger');
    }
}

function showAddHotelModal() {
    const modal = new bootstrap.Modal(document.getElementById('addHotelModal'));
    modal.show();
}

async function addHotel() {
    try {
        const name = document.getElementById('hotel-name').value;
        const location = document.getElementById('hotel-location').value;
        const tallyUrl = document.getElementById('hotel-tally-url').value;
        
        if (!name) {
            showAlert('Le nom de l\'hôtel est requis', 'warning');
            return;
        }
        
        const response = await fetch(`${API_BASE}/hotels`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                location: location,
                tally_form_url: tallyUrl
            })
        });
        
        if (response.ok) {
            const hotel = await response.json();
            showAlert(`Hôtel "${hotel.name}" créé avec succès!`, 'success');
            
            // Fermer le modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addHotelModal'));
            modal.hide();
            
            // Réinitialiser le formulaire
            document.getElementById('add-hotel-form').reset();
            
            // Recharger les données
            await loadHotels();
            loadHotelsTable();
            
        } else {
            const error = await response.json();
            showAlert(error.error || 'Erreur lors de la création de l\'hôtel', 'danger');
        }
        
    } catch (error) {
        console.error('Erreur lors de l\'ajout de l\'hôtel:', error);
        showAlert('Erreur lors de l\'ajout de l\'hôtel', 'danger');
    }
}

async function deleteHotel(hotelId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cet hôtel ? Toutes les données associées seront perdues.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/hotels/${hotelId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showAlert('Hôtel supprimé avec succès', 'success');
            await loadHotels();
            loadHotelsTable();
        } else {
            const error = await response.json();
            showAlert(error.error || 'Erreur lors de la suppression', 'danger');
        }
        
    } catch (error) {
        console.error('Erreur lors de la suppression:', error);
        showAlert('Erreur lors de la suppression', 'danger');
    }
}

// Dashboard
async function loadDashboard() {
    const hotelId = document.getElementById('hotel-selector').value;
    const dashboardContent = document.getElementById('dashboard-content');
    
    if (!hotelId) {
        dashboardContent.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-hotel fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">Sélectionnez un hôtel pour voir les statistiques</h4>
            </div>
        `;
        return;
    }
    
    try {
        dashboardContent.innerHTML = '<div class="text-center py-5"><div class="spinner-border"></div></div>';
        
        // Charger les statistiques
        const statsResponse = await fetch(`${API_BASE}/hotels/${hotelId}/statistics`);
        const stats = await statsResponse.json();
        
        // Charger les insights
        const insightsResponse = await fetch(`${API_BASE}/hotels/${hotelId}/insights`);
        const insightsData = await insightsResponse.json();
        
        // Afficher le dashboard
        dashboardContent.innerHTML = `
            <div class="row mb-4">
                <div class="col-md-3 mb-3">
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <div class="metric-value">${stats.average_overall_rating}</div>
                            <div class="text-muted">Note Moyenne Globale</div>
                            <small class="text-muted">Basé sur ${stats.total_responses} réponses</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <div class="metric-value">${stats.recommendation_rate}%</div>
                            <div class="text-muted">Taux de Recommandation</div>
                            <small class="text-muted">Pourcentage de clients qui recommandent</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <div class="metric-value">${stats.monthly_responses}</div>
                            <div class="text-muted">Réponses Mensuelles</div>
                            <small class="text-muted">Nouvelles réponses ce mois-ci</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <div class="metric-value">${stats.total_responses}</div>
                            <div class="text-muted">Total Réponses</div>
                            <small class="text-muted">Depuis le début</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Notes par Catégorie</h5>
                            <canvas id="categories-chart"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Insights Automatiques</h5>
                            <div id="insights-container">
                                ${insightsData.insights.map(insight => `
                                    <div class="insight-card insight-${insight.type} card mb-2">
                                        <div class="card-body py-2">
                                            <h6 class="card-title mb-1">${insight.title}</h6>
                                            <p class="card-text small mb-0">${insight.description}</p>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Créer le graphique des catégories
        createCategoriesChart(stats.category_averages);
        
    } catch (error) {
        console.error('Erreur lors du chargement du dashboard:', error);
        dashboardContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Erreur lors du chargement des données
            </div>
        `;
    }
}

function createCategoriesChart(categoryAverages) {
    const ctx = document.getElementById('categories-chart');
    if (!ctx) return;
    
    const labels = {
        'accommodation_rating': 'Hébergement',
        'service_rating': 'Service',
        'cleanliness_rating': 'Propreté',
        'food_rating': 'Restauration',
        'location_rating': 'Emplacement',
        'value_rating': 'Qualité-prix'
    };
    
    const data = Object.keys(categoryAverages).map(key => categoryAverages[key]);
    const chartLabels = Object.keys(categoryAverages).map(key => labels[key] || key);
    
    if (currentCharts.categories) {
        currentCharts.categories.destroy();
    }
    
    currentCharts.categories = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartLabels,
            datasets: [{
                label: 'Note moyenne',
                data: data,
                backgroundColor: 'rgba(37, 99, 235, 0.8)',
                borderColor: 'rgba(37, 99, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 5
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Réponses
async function loadResponses() {
    const hotelId = document.getElementById('responses-hotel-selector').value;
    const responsesContent = document.getElementById('responses-content');
    
    if (!hotelId) {
        responsesContent.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-users fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">Sélectionnez un hôtel pour voir les réponses</h4>
            </div>
        `;
        return;
    }
    
    try {
        responsesContent.innerHTML = '<div class="text-center py-5"><div class="spinner-border"></div></div>';
        
        const response = await fetch(`${API_BASE}/hotels/${hotelId}/responses`);
        const data = await response.json();
        
        if (data.responses.length === 0) {
            responsesContent.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">Aucune réponse trouvée</h4>
                    <p class="text-muted">Les réponses apparaîtront ici une fois que les clients auront rempli le formulaire.</p>
                </div>
            `;
            return;
        }
        
        responsesContent.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Client</th>
                            <th>Email</th>
                            <th>Note</th>
                            <th>Recommandation</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.responses.map(response => `
                            <tr>
                                <td>${new Date(response.submission_date).toLocaleDateString('fr-FR')}</td>
                                <td>${response.client_name || '-'}</td>
                                <td>${response.client_email || '-'}</td>
                                <td>
                                    <span class="badge bg-primary">${response.overall_rating || '-'}/5</span>
                                </td>
                                <td>
                                    ${response.would_recommend === true ? 
                                        '<span class="badge bg-success">Oui</span>' : 
                                        response.would_recommend === false ? 
                                        '<span class="badge bg-danger">Non</span>' : 
                                        '<span class="badge bg-secondary">-</span>'
                                    }
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" onclick="viewResponseDetails(${response.id})">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="d-flex justify-content-between align-items-center mt-3">
                <small class="text-muted">
                    Affichage de ${data.responses.length} réponses sur ${data.total}
                </small>
                ${data.pages > 1 ? `
                    <nav>
                        <ul class="pagination pagination-sm">
                            ${Array.from({length: data.pages}, (_, i) => i + 1).map(page => `
                                <li class="page-item ${page === data.current_page ? 'active' : ''}">
                                    <a class="page-link" href="#" onclick="loadResponses(${page})">${page}</a>
                                </li>
                            `).join('')}
                        </ul>
                    </nav>
                ` : ''}
            </div>
        `;
        
    } catch (error) {
        console.error('Erreur lors du chargement des réponses:', error);
        responsesContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Erreur lors du chargement des réponses
            </div>
        `;
    }
}

// Analytics
async function loadAnalytics() {
    const hotelId = document.getElementById('analytics-hotel-selector').value;
    const analyticsContent = document.getElementById('analytics-content');
    
    if (!hotelId) {
        analyticsContent.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-chart-bar fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">Sélectionnez un hôtel pour voir les analyses</h4>
            </div>
        `;
        return;
    }
    
    try {
        analyticsContent.innerHTML = '<div class="text-center py-5"><div class="spinner-border"></div></div>';
        
        // Charger les graphiques
        const chartsResponse = await fetch(`${API_BASE}/reports/hotel/${hotelId}/charts`);
        const chartsData = await chartsResponse.json();
        
        analyticsContent.innerHTML = `
            <div class="row">
                <div class="col-12 mb-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Notes par Catégorie</h5>
                            <img src="data:image/png;base64,${chartsData.charts.categories}" class="img-fluid" alt="Graphique des catégories">
                        </div>
                    </div>
                </div>
                
                ${chartsData.charts.distribution ? `
                    <div class="col-md-6 mb-4">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Distribution des Notes</h5>
                                <img src="data:image/png;base64,${chartsData.charts.distribution}" class="img-fluid" alt="Distribution des notes">
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                ${chartsData.charts.temporal ? `
                    <div class="col-md-6 mb-4">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Évolution Temporelle</h5>
                                <img src="data:image/png;base64,${chartsData.charts.temporal}" class="img-fluid" alt="Évolution temporelle">
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
    } catch (error) {
        console.error('Erreur lors du chargement des analyses:', error);
        analyticsContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Erreur lors du chargement des analyses
            </div>
        `;
    }
}

// Reports
function populateReportSelectors() {
    // Les sélecteurs sont déjà mis à jour par updateHotelSelectors
}

async function exportHotelExcel() {
    const hotelId = document.getElementById('export-hotel-selector').value;
    
    if (!hotelId) {
        showAlert('Veuillez sélectionner un hôtel', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/reports/hotel/${hotelId}/excel`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `HotelSat_Export_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showAlert('Export Excel téléchargé avec succès', 'success');
        } else {
            const error = await response.json();
            showAlert(error.error || 'Erreur lors de l\'export', 'danger');
        }
        
    } catch (error) {
        console.error('Erreur lors de l\'export Excel:', error);
        showAlert('Erreur lors de l\'export Excel', 'danger');
    }
}

async function exportGlobalExcel() {
    try {
        const response = await fetch(`${API_BASE}/reports/global/excel`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `HotelSat_Rapport_Global_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showAlert('Rapport global téléchargé avec succès', 'success');
        } else {
            const error = await response.json();
            showAlert(error.error || 'Erreur lors de l\'export', 'danger');
        }
        
    } catch (error) {
        console.error('Erreur lors de l\'export global:', error);
        showAlert('Erreur lors de l\'export global', 'danger');
    }
}

// Automation
function populateAutomationSelectors() {
    // Les sélecteurs sont déjà mis à jour par updateHotelSelectors
}

document.getElementById('automation-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const hotelId = document.getElementById('automation-hotel').value;
    const tallyUrl = document.getElementById('tally-url').value;
    
    if (!hotelId || !tallyUrl) {
        showAlert('Veuillez remplir tous les champs requis', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/hotels/${hotelId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tally_form_url: tallyUrl
            })
        });
        
        if (response.ok) {
            showAlert('Automatisation configurée avec succès!', 'success');
            this.reset();
            await loadHotels();
        } else {
            const error = await response.json();
            showAlert(error.error || 'Erreur lors de la configuration', 'danger');
        }
        
    } catch (error) {
        console.error('Erreur lors de la configuration:', error);
        showAlert('Erreur lors de la configuration', 'danger');
    }
});

async function testWebhook() {
    const hotelId = document.getElementById('test-hotel-selector').value;
    
    if (!hotelId) {
        showAlert('Veuillez sélectionner un hôtel', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/webhooks/test?hotel_id=${hotelId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            showAlert('Test d\'intégration réussi! Réponse de test créée.', 'success');
        } else {
            const error = await response.json();
            showAlert(error.error || 'Erreur lors du test', 'danger');
        }
        
    } catch (error) {
        console.error('Erreur lors du test:', error);
        showAlert('Erreur lors du test d\'intégration', 'danger');
    }
}

// Utilitaires
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

function viewResponseDetails(responseId) {
    // Cette fonction pourrait ouvrir un modal avec les détails complets de la réponse
    showAlert('Fonctionnalité de détail des réponses à implémenter', 'info');
}

