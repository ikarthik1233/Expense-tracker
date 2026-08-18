<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';

  let receipts = [];
  let summary = { total_this_month: 0, by_category: {}, top_merchants: [] };
  let loading = true;

  let budget = null;
  let budgetInput = '';
  let totalSpent = 0;
  let recovered = 0;

  $: effectiveSpent = totalSpent - recovered;
  $: spentPercent = budget ? (effectiveSpent / budget.amount) * 100 : 0;
  $: remaining = budget ? Math.max(budget.amount - effectiveSpent, 0) : 0;
  $: currentMonthLabel = new Date().toLocaleString('default', { month: 'long', year: 'numeric' }).toUpperCase();

  async function loadData() {
    loading = true;
    try {
      const currentMonth = new Date().toISOString().slice(0, 7);
      const [rData, sData, bData, bgtData] = await Promise.all([
        api.getReceipts(currentMonth),
        api.getSummary(currentMonth),
        api.getBalances(),
        api.getBudget().catch(() => null)
      ]);
      receipts = rData;
      summary = sData;
      budget = bgtData;
      totalSpent = summary.total_this_month || 0;
      recovered = bData.recovered || 0;
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      loading = false;
    }
  }

  async function lockBudget() {
    if (!budgetInput || budgetInput <= 0) return;
    try {
      budget = await api.setBudget(Number(budgetInput));
      await loadData();
    } catch (err) {
      alert('SYSTEM ALERT: ' + err.message);
    }
  }

  async function handleDelete(id) {
    if (!confirm('TERMINATE AND ERASE DATA POD?')) return;
    try {
      await api.deleteReceipt(id);
      await loadData();
    } catch (err) {
      alert('FAILED TO ERASE DATA POD');
    }
  }

  onMount(async () => {
    await loadData();
  });
</script>

<div class="dashboard-page">
  <header class="header">
    <h1 class="page-title">SYSTEM DASHBOARD</h1>
    <p class="page-subtitle">> MONITORING FINANCIAL DESTRUCTION</p>
  </header>

  <!-- Two-Panel HUD Section -->
  <div class="hud-two-panel">
    <!-- Left 65% Panel: Giant Readout -->
    <div class="main-damage-panel cyber-glass">
      <span class="hud-subhead">> FINANCIAL DAMAGE / CURRENT CYCLE</span>
      <h2 class="giant-amount">₹{summary.total_this_month.toLocaleString('en-IN')}</h2>

      <div class="budget-bar-wrapper">
        <div class="budget-bar-header">
          <span>BUDGET CONSUMPTION</span>
          <span>CAPACITY: {budget ? Math.round(spentPercent) + '%' : 'UNLOCKED'}</span>
        </div>
        <div class="budget-bar-track">
          <div class="budget-bar-fill" style="width: {Math.min(spentPercent, 100)}%;"></div>
        </div>
      </div>
    </div>

    <!-- Right 35% Panel: HUD Stat Stack -->
    <div class="stat-stack">
      <div class="stat-card cyber-glass">
        <span class="stat-label">> ACTIVE PODS</span>
        <h3 class="stat-val">{receipts.length}</h3>
      </div>
      <div class="stat-card cyber-glass">
        <span class="stat-label">> PRIMARY KILLER</span>
        <h3 class="stat-val">{summary.top_merchants[0] ? summary.top_merchants[0].merchant : 'N/A'}</h3>
      </div>
    </div>
  </div>

  <div class="dashboard-grid">
    <!-- Monthly Budget Protocol Panel -->
    <div class="budget-panel card cyber-glass">
      {#if budget}
        <div class="budget-label">> MONTHLY BUDGET PROTOCOL</div>
        <div class="budget-cycle">CYCLE: {currentMonthLabel}</div>
        <div class="budget-locked">BUDGET LOCKED: <span class="amount amount-glow">₹{budget.amount.toLocaleString('en-IN')}</span></div>

        <div class="budget-breakdown-row">
          <span>TOTAL SPENT: ₹{totalSpent.toLocaleString('en-IN')}</span>
          <span class="recovered-text">↩ RECOVERED: ₹{recovered.toLocaleString('en-IN')}</span>
          <span>EFFECTIVE SPEND: ₹{effectiveSpent.toLocaleString('en-IN')}</span>
        </div>

        <div class="budget-bar-wrap">
          <div class="budget-bar" style="width:{Math.min(spentPercent,100)}%; background:{spentPercent>80?'#FF2D78':spentPercent>60?'#FFE600':'#39FF14'}"></div>
        </div>
        <div class="budget-stats">
          <span>REMAINING: <b style="color:#39FF14">₹{remaining.toLocaleString('en-IN')}</b></span>
          <span class="status-badge" class:nominal={spentPercent<=60} class:warning={spentPercent>60&&spentPercent<=80} class:critical={spentPercent>80}>
            {spentPercent<=60?'[NOMINAL]':spentPercent<=80?'[WARNING]':'[CRITICAL]'}
          </span>
        </div>
      {:else}
        <div class="budget-label">> MONTHLY BUDGET PROTOCOL</div>
        <div class="no-budget">NO BUDGET SET FOR THIS CYCLE</div>
        <input class="budget-input" type="number" bind:value={budgetInput} placeholder="ENTER BUDGET AMOUNT"/>
        <button class="lock-btn" on:click={lockBudget}>⚡ LOCK IN BUDGET</button>
        <div class="budget-warning">⚠ THIS ACTION IS IRREVERSIBLE FOR CURRENT CYCLE</div>
      {/if}
    </div>

    <!-- Data Pods Section -->
    <div class="tombstones-section cyber-glass">
      <h3 class="card-title">> ARCHIVED DATA PODS</h3>

      {#if loading}
        <div class="loading-state">SCANNING MEMORY SECTORS...</div>
      {:else if receipts.length === 0}
        <div class="empty-state">
          <span class="empty-code">[0x00] NO DATA DETECTED_</span>
          <a href="/scan" class="cyber-btn mt-4">INITIATE FIRST SCAN</a>
        </div>
      {:else}
        <div class="pods-scroll-strip">
          {#each receipts as r}
            <div class="data-pod">
              <button
                class="delete-btn"
                on:click={() => handleDelete(r.id)}
                title="PURGE POD"
              >
                ✕
              </button>
              <div class="pod-header">
                <span class="pod-tag">POD #{r.id}</span>
                <h4 class="pod-merchant">{r.merchant}</h4>
              </div>
              <div class="pod-body">
                <div class="hud-row">
                  <span class="hud-k">> AMOUNT:</span>
                  <span class="hud-v amount-glow">₹{r.total.toLocaleString('en-IN')}</span>
                </div>
                <div class="hud-row">
                  <span class="hud-k">> DATE:</span>
                  <span class="hud-v">{r.date}</span>
                </div>
                <div class="hud-row">
                  <span class="hud-k">> CLASS:</span>
                  <span class="category-badge">{r.category}</span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .dashboard-page {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .page-title {
    font-size: 2.2rem;
    color: #FFFFFF;
  }

  .page-subtitle {
    color: #FF6B00;
    font-size: 0.9rem;
  }

  .cyber-glass {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(180, 100, 255, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
    position: relative;
    backdrop-filter: blur(24px);
  }

  .hud-two-panel {
    display: grid;
    grid-template-columns: 1.8fr 1fr;
    gap: 1.5rem;
  }

  @media (max-width: 900px) {
    .hud-two-panel {
      grid-template-columns: 1fr;
    }
  }

  .main-damage-panel {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .hud-subhead {
    font-size: 0.8rem;
    color: #FF6B00;
    letter-spacing: 1.5px;
  }

  .giant-amount {
    font-size: 4rem;
    font-family: 'Orbitron', sans-serif;
    color: #FFE600;
    text-shadow: 0 0 20px #FFE600;
    margin: 0.5rem 0;
  }

  .budget-bar-wrapper {
    margin-top: 1rem;
  }

  .budget-bar-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.4);
    margin-bottom: 0.4rem;
  }

  .budget-bar-track {
    height: 8px;
    background: rgba(180, 100, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }

  .budget-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #39FF14, #B44CFF);
    box-shadow: 0 0 10px #39FF14;
  }

  .stat-stack {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .stat-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .stat-label {
    font-size: 0.75rem;
    color: #FF2D78;
    letter-spacing: 1px;
  }

  .stat-val {
    font-size: 2rem;
    color: #39FF14;
    text-shadow: 0 0 10px #39FF14;
    margin-top: 0.25rem;
  }

  .dashboard-grid {
    display: grid;
    grid-template-columns: 1fr 1.5fr;
    gap: 1.5rem;
  }

  @media (max-width: 900px) {
    .dashboard-grid {
      grid-template-columns: 1fr;
    }
  }

  .card-title {
    font-size: 1.1rem;
    margin-bottom: 1.25rem;
    color: #FFFFFF;
  }

  .budget-panel { padding: 24px; }
  .budget-label { color: #FF6B00; font-size: 11px; letter-spacing: 0.15em; margin-bottom: 12px; }
  .budget-cycle { color: rgba(255,255,255,0.4); font-size: 11px; margin-bottom: 8px; }
  .budget-locked { color: white; font-size: 14px; margin-bottom: 12px; }

  .budget-breakdown-row {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 12px;
    flex-wrap: wrap;
    font-family: 'Share Tech Mono', monospace;
  }

  .recovered-text {
    color: #39FF14;
    text-shadow: 0 0 8px #39FF14;
  }

  .budget-bar-wrap { background: rgba(255,255,255,0.05); height: 6px; margin-bottom: 12px; }
  .budget-bar { height: 6px; transition: width 0.5s; }
  .budget-stats { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: rgba(255,255,255,0.6); }
  .status-badge { font-family: 'Share Tech Mono', monospace; font-size: 11px; padding: 2px 8px; border: 1px solid; }
  .nominal { color: #39FF14; border-color: #39FF14; }
  .warning { color: #FFE600; border-color: #FFE600; }
  .critical { color: #FF2D78; border-color: #FF2D78; animation: blink 1s infinite; }
  .no-budget { color: rgba(255,255,255,0.3); font-size: 12px; margin-bottom: 16px; }
  .budget-input { width: 100%; background: rgba(57,255,20,0.05); border: 1px solid rgba(180,100,255,0.3); color: white; padding: 12px 16px; font-family: 'Share Tech Mono', monospace; margin-bottom: 12px; font-size: 16px; }
  .lock-btn { width: 100%; background: linear-gradient(135deg,#39FF14,#B44CFF); color: black; padding: 12px; font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 13px; border: none; cursor: crosshair; margin-bottom: 8px; clip-path: none; }
  .budget-warning { color: #FFE600; font-size: 10px; text-align: center; opacity: 0.7; }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  .pods-scroll-strip {
    display: flex;
    gap: 1.25rem;
    overflow-x: auto;
    padding-bottom: 0.5rem;
    scroll-snap-type: x mandatory;
  }

  .data-pod {
    min-width: 200px;
    height: 250px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(180, 100, 255, 0.2);
    border-radius: 4px;
    padding: 1rem;
    position: relative;
    scroll-snap-align: start;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.2s ease;
  }

  .data-pod:hover {
    box-shadow: 0 0 30px rgba(180, 100, 255, 0.3);
    border-color: rgba(57, 255, 20, 0.4);
  }

  /* Corner Bracket Pseudo Elements */
  .data-pod::before {
    content: "⌐";
    position: absolute;
    top: 4px;
    left: 6px;
    color: #B44CFF;
    font-size: 0.9rem;
  }

  .data-pod::after {
    content: "¬";
    position: absolute;
    top: 4px;
    right: 6px;
    color: #B44CFF;
    font-size: 0.9rem;
  }

  .delete-btn {
    position: absolute;
    bottom: 8px;
    right: 8px;
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.4);
    cursor: pointer;
    font-size: 0.9rem;
    padding: 2px 6px;
  }

  .delete-btn:hover {
    color: #FF2D78;
    box-shadow: none;
    transform: none;
  }

  .pod-tag {
    font-size: 0.7rem;
    color: #FF6B00;
  }

  .pod-merchant {
    font-family: 'Orbitron', sans-serif;
    font-size: 1rem;
    color: #FFFFFF;
    margin-top: 0.2rem;
    word-break: break-word;
  }

  .hud-row {
    display: flex;
    flex-direction: column;
    margin-top: 0.5rem;
  }

  .hud-k {
    font-size: 0.7rem;
    color: #FF6B00;
  }

  .hud-v {
    font-size: 0.9rem;
    color: #FFFFFF;
  }

  .amount-glow {
    color: #FFE600;
    text-shadow: 0 0 20px #FFE600;
    font-size: 1.2rem;
    font-weight: 700;
  }

  .category-badge {
    display: inline-block;
    background: rgba(180, 100, 255, 0.2);
    color: #B44CFF;
    font-size: 0.75rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    margin-top: 0.2rem;
  }

  .cyber-btn {
    display: inline-block;
    background: linear-gradient(135deg, #39FF14, #B44CFF);
    color: #0D0015;
    font-weight: 900;
    padding: 10px 20px;
    text-decoration: none;
    font-family: 'Orbitron', sans-serif;
    border-radius: 4px;
  }

  .empty-state {
    text-align: center;
    padding: 2rem;
    color: #B44CFF;
  }

  .empty-code {
    display: block;
    font-size: 1.1rem;
  }

  .mt-4 { margin-top: 1rem; }
  .loading-state { text-align: center; padding: 2rem; color: #39FF14; }
</style>
