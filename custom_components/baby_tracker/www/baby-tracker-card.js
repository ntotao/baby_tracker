class BabyTrackerCard extends HTMLElement {
    set hass(hass) {
        this._hass = hass;
        
        // Check if configuration exists
        if (!this.content) {
            this.innerHTML = `
                <ha-card header="Baby Tracker">
                    <div style="padding: 16px;">
                        Caricamento... assicurati di aver configurato l'integrazione.
                    </div>
                </ha-card>
            `;
            this.content = this.querySelector('div');
        }
        
        const entityId = this.config.entity;
        const state = hass.states[entityId];
        // We can access attributes from the coordinator entity if we exposed one, 
        // OR we can just rely on the standard entities we already have.
        // For v2.0, let's build a UI that aggregates the separate entities efficiently.
        
        this.render();
    }

    setConfig(config) {
        this.config = config;
    }

    render() {
        if (!this._hass) return;
        
        // Define entities to watch (hardcoded or from config)
        const feedingTimer = this._hass.states['input_boolean.baby_feeding_timer_active'];
        const feedingState = feedingTimer ? feedingTimer.state : 'off';
        
        const pooCount = this._hass.states['counter.baby_diaper_poo_daily']?.state || 0;
        const peeCount = this._hass.states['counter.baby_diaper_pee_daily']?.state || 0;
        const feedingCount = this._hass.states['counter.baby_feeding_daily']?.state || 0;
        
        const cardHtml = `
            <ha-card>
                <div class="card-header">
                    <div class="name">Baby Tracker 2.0</div>
                </div>
                <div class="card-content">
                    <div class="stats-grid">
                        <div class="stat-box" style="background: var(--info-color, #2196F3);">
                            <ha-icon icon="mdi:baby-bottle"></ha-icon>
                            <span class="value">${feedingCount}</span>
                        </div>
                        <div class="stat-box" style="background: var(--warning-color, #FF9800);">
                            <ha-icon icon="mdi:emoticon-poop"></ha-icon>
                            <span class="value">${pooCount}</span>
                        </div>
                        <div class="stat-box" style="background: var(--primary-color, #03A9F4);">
                            <ha-icon icon="mdi:water"></ha-icon>
                            <span class="value">${peeCount}</span>
                        </div>
                    </div>
                    
                    <div class="actions">
                        ${feedingState === 'on' 
                            ? `<button class="btn stop-btn">⏹️ STOP Rilevamento</button>` 
                            : `<button class="btn start-btn">▶️ AVVIA Poppata</button>`
                        }
                    </div>
                    
                    <div class="timeline">
                        <!-- Placeholder for visual timeline -->
                        <div class="timeline-item">
                            <span class="time">Adesso</span>
                            <span class="desc">Status: ${feedingState === 'on' ? 'In Corso...' : 'In Attesa'}</span>
                        </div>
                    </div>
                </div>
                <style>
                    ha-card {
                        background: var(--card-background-color);
                        border-radius: 12px;
                        overflow: hidden;
                    }
                    .card-header {
                        padding: 16px;
                        font-size: 20px;
                        font-weight: bold;
                    }
                    .stats-grid {
                        display: grid;
                        grid-template-columns: repeat(3, 1fr);
                        gap: 12px;
                        margin-bottom: 24px;
                    }
                    .stat-box {
                        border-radius: 12px;
                        padding: 16px;
                        color: white;
                        text-align: center;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }
                    .stat-box ha-icon {
                        margin-bottom: 8px;
                    }
                    .stat-box .value {
                        font-size: 24px;
                        font-weight: bold;
                    }
                    .btn {
                        width: 100%;
                        padding: 16px;
                        border: none;
                        border-radius: 12px;
                        font-size: 18px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: opacity 0.2s;
                    }
                    .start-btn {
                        background: #4CAF50;
                        color: white;
                    }
                    .stop-btn {
                        background: #F44336;
                        color: white;
                    }
                    .timeline {
                        margin-top: 24px;
                        border-top: 1px solid var(--divider-color);
                        padding-top: 16px;
                    }
                </style>
            </ha-card>
        `;
        
        this.innerHTML = cardHtml;
        
        // Add listeners (Proof of concept - real logic needs hass.callService)
        // Note: In a real card, we shouldn't re-render fully on every state change 
        // causing lost listeners, but for this V1 simple card it works.
        const btn = this.querySelector('button');
        if (btn) {
            btn.onclick = () => {
                const service = feedingState === 'on' ? 'turn_off' : 'turn_on';
                this._hass.callService('input_boolean', service, {
                    entity_id: 'input_boolean.baby_feeding_timer_active'
                });
            };
        }
    }

    getCardSize() {
        return 3;
    }
}

customElements.define('baby-tracker-card', BabyTrackerCard);
console.info("Baby Tracker Card loaded");
window.customCards = window.customCards || [];
window.customCards.push({
    type: "baby-tracker-card",
    name: "Baby Tracker Card",
    description: "A custom card for Baby Tracker integration"
});
