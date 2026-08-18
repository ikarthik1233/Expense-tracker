<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import Chart from 'chart.js/auto';

  let selectedMonth = new Date().toISOString().slice(0, 7); // YYYY-MM
  let receipts = [];
  let summary = { total_this_month: 0, by_category: {}, top_merchants: [] };
  let fatalBlow = null;
  let loading = true;
  let chartCanvas;
  let chartInstance;

  function getAvailableMonths() {
    const months = [];
    const date = new Date();
    for (let i = 0; i < 12; i++) {
      const yr = date.getFullYear();
      const mo = String(date.getMonth() + 1).padStart(2, '0');
      months.push(`${yr}-${mo}`);
      date.setMonth(date.getMonth() - 1);
    }
    return months;
  }

  const availableMonths = getAvailableMonths();

  async function loadReportData() {
    loading = true;
    try {
      const [rData, sData] = await Promise.all([
        api.getReceipts(selectedMonth),
        api.getSummary(selectedMonth)
      ]);
      receipts = rData;
      summary = sData;

      if (receipts.length > 0) {
        fatalBlow = receipts.reduce((max, r) => (r.total > max.total ? r : max), receipts[0]);
      } else {
        fatalBlow = null;
      }

      renderWeeklyChart();
    } catch (err) {
      console.error('Failed to load report data:', err);
    } finally {
      loading = false;
    }
  }

  function renderWeeklyChart() {
    if (!chartCanvas) return;
    if (chartInstance) chartInstance.destroy();

    const weekTotals = [0, 0, 0, 0];
    receipts.forEach(r => {
      const day = parseInt(r.date.split('-')[2]) || 1;
      if (day <= 7) weekTotals[0] += r.total;
      else if (day <= 14) weekTotals[1] += r.total;
      else if (day <= 21) weekTotals[2] += r.total;
      else weekTotals[3] += r.total;
    });

    const ctx = chartCanvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, '#39FF14');
    gradient.addColorStop(1, '#B44CFF');

    chartInstance = new Chart(chartCanvas, {
      type: 'bar',
      data: {
        labels: ['WEEK 1', 'WEEK 2', 'WEEK 3', 'WEEK 4+'],
        datasets: [
          {
            label: 'SACRIFICES (₹)',
            data: weekTotals,
            backgroundColor: gradient,
            borderRadius: 4,
            borderColor: '#39FF14',
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: {
            ticks: { color: 'rgba(255, 255, 255, 0.8)', font: { family: 'Share Tech Mono' } },
            grid: { color: 'rgba(180, 100, 255, 0.15)' }
          },
          y: {
            ticks: { color: 'rgba(255, 255, 255, 0.8)', font: { family: 'Share Tech Mono' } },
            grid: { color: 'rgba(180, 100, 255, 0.15)' }
          }
        }
      }
    });
  }

  onMount(() => {
    loadReportData();
  });
</script>

<div class="report-page">
  <header class="header-row">
    <div>
      <h1 class="page-title">AUTOPSY & ANALYTICS REPORT</h1>
      <p class="page-subtitle">> SYSTEM FINANCIAL MORTALITY BREAKDOWN</p>
    </div>

    <!-- HUD Month Dial -->
    <div class="month-selector">
      <label for="monthSelect">> PERIOD:</label>
      <select id="monthSelect" bind:value={selectedMonth} on:change={loadReportData}>
        {#each availableMonths as m}
          <option value={m}>{m}</option>
        {/each}
      </select>
    </div>
  </header>

  <!-- Fatal Blow & Summary Grid -->
  <div class="top-cards-grid">
    <!-- Pulsing Fatal Blow Card -->
    <div class="fatal-card cyber-glass">
      <div class="fatal-badge">💀 THE FATAL BLOW</div>
      {#if fatalBlow}
        <h2 class="fatal-merchant">{fatalBlow.merchant}</h2>
        <p class="fatal-amount">₹{fatalBlow.total.toLocaleString('en-IN')}</p>
        <p class="fatal-date">STRUCK DOWN ON {fatalBlow.date} • {fatalBlow.category}</p>
      {:else}
        <p class="empty-fatal">NO FATAL BLOWS RECORDED IN THIS CYCLE_</p>
      {/if}
    </div>

    <!-- Total Monthly Casualties -->
    <div class="summary-stat-card cyber-glass">
      <span class="stat-label">> TOTAL MONTHLY LOSSES</span>
      <h2 class="stat-value">₹{summary.total_this_month.toLocaleString('en-IN')}</h2>
      <p class="stat-sub">{receipts.length} TOTAL DATA PODS BURIED</p>
    </div>
  </div>

  <div class="report-grid">
    <!-- Weekly Bar Chart -->
    <div class="chart-card cyber-glass">
      <h3 class="card-title">> WEEKLY FINANCIAL CARNAGE</h3>
      <div class="chart-container">
        <canvas bind:this={chartCanvas}></canvas>
      </div>
    </div>

    <!-- Top 5 Merchants "Your Biggest Killers" -->
    <div class="killers-card cyber-glass">
      <h3 class="card-title">🔪 YOUR BIGGEST KILLERS</h3>
      {#if summary.top_merchants.length === 0}
        <p class="empty-sub">NO KILLERS DETECTED_</p>
      {:else}
        <ol class="killers-list">
          {#each summary.top_merchants as m, index}
            <li class="killer-item">
              <span class="rank-num">#0{index + 1}</span>
              <span class="killer-name">{m.merchant}</span>
              <span class="killer-total">₹{m.total.toLocaleString('en-IN')}</span>
            </li>
          {/each}
        </ol>
      {/if}
    </div>
  </div>
</div>

<style>
  .report-page {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .page-title { font-size: 2.2rem; color: #FFFFFF; }
  .page-subtitle { color: #FF6B00; font-size: 0.9rem; }

  .cyber-glass {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(180, 100, 255, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
    backdrop-filter: blur(24px);
  }

  .month-selector {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .month-selector label {
    font-weight: 700;
    color: #FF6B00;
    font-size: 0.85rem;
  }

  .month-selector select {
    width: auto;
    background: rgba(57, 255, 20, 0.05);
    border: 1px solid #39FF14;
    color: #FFFFFF;
    font-weight: 700;
  }

  .top-cards-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  @media (max-width: 768px) {
    .top-cards-grid { grid-template-columns: 1fr; }
  }

  @keyframes pulse-red {
    0%, 100% { border-color: #FF2D78; box-shadow: 0 0 15px rgba(255, 45, 120, 0.4); }
    50% { border-color: rgba(255, 45, 120, 0.3); box-shadow: none; }
  }

  .fatal-card {
    border: 2px solid #FF2D78;
    animation: pulse-red 2s infinite ease-in-out;
  }

  .fatal-badge {
    color: #FF2D78;
    font-weight: 900;
    font-size: 0.8rem;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
    font-family: 'Orbitron', sans-serif;
  }

  .fatal-merchant {
    font-size: 1.8rem;
    color: #FFFFFF;
  }

  .fatal-amount {
    font-size: 2.5rem;
    color: #FFE600;
    text-shadow: 0 0 20px #FFE600;
    font-weight: 900;
    margin: 0.25rem 0;
  }

  .fatal-date {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.4);
  }

  .empty-fatal {
    color: rgba(255, 255, 255, 0.4);
    padding: 1rem 0;
  }

  .summary-stat-card {
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .stat-label {
    font-size: 0.75rem;
    letter-spacing: 1px;
    color: #FF6B00;
  }

  .stat-value {
    font-size: 2.8rem;
    color: #FFE600;
    text-shadow: 0 0 20px #FFE600;
    margin: 0.25rem 0;
  }

  .stat-sub {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.4);
  }

  .report-grid {
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: 1.5rem;
  }

  @media (max-width: 850px) {
    .report-grid { grid-template-columns: 1fr; }
  }

  .card-title {
    font-size: 1.1rem;
    margin-bottom: 1.25rem;
    color: #FFFFFF;
  }

  .chart-container {
    height: 280px;
    position: relative;
  }

  .killers-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .killer-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(180, 100, 255, 0.15);
    padding: 0.75rem 1rem;
    border-radius: 4px;
    position: relative;
  }

  .rank-num {
    font-weight: 900;
    color: #B44CFF;
    font-size: 1.1rem;
    font-family: 'Orbitron', sans-serif;
  }

  .killer-name {
    flex: 1;
    font-weight: 700;
    color: #FFFFFF;
  }

  .killer-total {
    font-weight: 700;
    color: #FFE600;
    text-shadow: 0 0 10px #FFE600;
  }

  .empty-sub { color: rgba(255, 255, 255, 0.4); font-size: 0.85rem; }
</style>
