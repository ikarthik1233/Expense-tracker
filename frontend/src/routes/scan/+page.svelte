<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { goto } from '$app/navigation';

  let dragging = false;
  let loading = false;
  let imagePreview = null;
  let imageBase64 = null;

  let dropdownOpen = false;
  let dropdownEl;

  function handleClickOutside(e) {
    if (dropdownEl && !dropdownEl.contains(e.target)) dropdownOpen = false;
  }

  onMount(() => {
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  });

  let formData = {
    merchant: '',
    date: new Date().toISOString().slice(0, 10),
    total: 0,
    category: 'Food',
    items: []
  };

  const categories = ['Food', 'Shopping', 'Transport', 'Entertainment', 'Health', 'Utilities', 'Other'];

  function handleFileSelect(file) {
    if (!file || !file.type.startsWith('image/')) {
      alert('SYSTEM ALERT: INVALID IMAGE FORMAT');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview = e.target.result;
      imageBase64 = e.target.result;
      scanImage(imageBase64);
    };
    reader.readAsDataURL(file);
  }

  function handleDrop(e) {
    e.preventDefault();
    dragging = false;
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }

  function handleFileInputChange(e) {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  }

  async function scanImage(base64) {
    loading = true;
    try {
      const parsed = await api.scanReceipt(base64);

      // Format date to YYYY-MM-DD
      let cleanDate = parsed.date;
      if (cleanDate && /^\d{2}[-/]\d{2}[-/]\d{4}$/.test(cleanDate)) {
        const parts = cleanDate.split(/[-/]/);
        cleanDate = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
      }
      if (!cleanDate || !/^\d{4}-\d{2}-\d{2}$/.test(cleanDate)) {
        cleanDate = new Date().toISOString().slice(0, 10);
      }

      formData = {
        merchant: parsed.merchant || 'UNKNOWN VENDOR',
        date: cleanDate,
        total: parseFloat(parsed.total) || 0,
        category: parsed.category || 'Other',
        items: (parsed.items || []).map(i => ({
          name: String(i.name || 'Item').trim(),
          price: parseFloat(i.price) || 0
        }))
      };
    } catch (err) {
      alert('OCR ANALYSIS ERROR: ' + err.message);
    } finally {
      loading = false;
    }
  }

  function addItem() {
    formData.items = [...formData.items, { name: '', price: 0 }];
  }

  function removeItem(index) {
    formData.items = formData.items.filter((_, i) => i !== index);
    calculateTotal();
  }

  function calculateTotal() {
    const sum = formData.items.reduce((acc, item) => acc + (parseFloat(item.price) || 0), 0);
    if (sum > 0) {
      formData.total = parseFloat(sum.toFixed(2));
    }
  }

  async function saveReceipt(redirectToSplits = false) {
    if (!formData.merchant) {
      alert('SYSTEM ALERT: ENTER VENDOR NAME');
      return;
    }

    try {
      // Ensure date strictly follows YYYY-MM-DD format
      let formattedDate = formData.date;
      if (formattedDate && /^\d{2}[-/]\d{2}[-/]\d{4}$/.test(formattedDate)) {
        const parts = formattedDate.split(/[-/]/);
        formattedDate = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
      }
      if (!formattedDate || !/^\d{4}-\d{2}-\d{2}$/.test(formattedDate)) {
        formattedDate = new Date().toISOString().slice(0, 10);
      }

      const payload = {
        merchant: String(formData.merchant).trim(),
        date: formattedDate,
        total: parseFloat(formData.total) || 0,
        category: formData.category || 'Other',
        items: (formData.items || []).map(i => ({
          name: String(i.name || 'Item').trim(),
          price: parseFloat(i.price) || 0
        })),
        image_base64: imageBase64
      };

      const created = await api.createReceipt(payload);
      if (redirectToSplits) {
        goto(`/splits?receipt_id=${created.id}&total=${created.total}`);
      } else {
        goto('/');
      }
    } catch (err) {
      alert('SYSTEM ALERT: SAVE FAILED - ' + err.message);
    }
  }
</script>

<div class="scan-page">
  <header class="header">
    <h1 class="page-title">OCR TARGETING SCANNER</h1>
    <p class="page-subtitle">> INITIATE OPTICAL RECOGNITION SEQUENCE</p>
  </header>

  <!-- Upload Target Reticle -->
  {#if !imagePreview}
    <div
      class="target-reticle"
      class:dragging
      on:dragover|preventDefault={() => (dragging = true)}
      on:dragleave={() => (dragging = false)}
      on:drop={handleDrop}
    >
      <input
        type="file"
        id="fileInput"
        accept="image/*"
        on:change={handleFileInputChange}
        class="file-input"
      />
      <label for="fileInput" class="upload-label">
        <span class="reticle-icon">🎯</span>
        <span class="upload-title">INITIATE SCAN SEQUENCE</span>
        <span class="upload-subtitle">DROP RECEIPT MATRIX TO ANALYZE</span>
      </label>
    </div>
  {:else}
    <!-- Loading Radar Sweep State -->
    {#if loading}
      <div class="loading-container cyber-glass">
        <div class="sweep-scanner">
          <div class="sweep-line"></div>
        </div>
        <h2 class="loading-text">ANALYZING RECEIPT... 84%</h2>
        <div class="progress-bar-track">
          <div class="progress-bar-fill"></div>
        </div>
        <p class="loading-sub">> PARSING OCR DATA BLOCKS VIA CLAUDE 3.5 SONNET</p>
      </div>
    {:else}
      <!-- Extracted Terminal Results -->
      <div class="scanner-results">
        <div class="preview-column cyber-glass">
          <h3 class="section-title">> RECEIPT MATRIX ARTIFACT</h3>
          <div class="image-wrapper">
            <img src={imagePreview} alt="Receipt preview" class="receipt-img" />
          </div>
          <button class="cyber-btn-sec w-full mt-3" on:click={() => { imagePreview = null; imageBase64 = null; }}>
            RE-INITIATE SCANNER
          </button>
        </div>

        <!-- Terminal Feed Form -->
        <div class="form-column cyber-glass">
          <h3 class="section-title">> TERMINAL DATA FEED</h3>

          <div class="form-group">
            <label for="merchant">> MERCHANT IDENTIFIER</label>
            <input type="text" id="merchant" bind:value={formData.merchant} placeholder="VENDOR CODE" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="date">> TIMESTAMP</label>
              <input type="date" id="date" bind:value={formData.date} />
            </div>

            <div class="form-group">
              <label for="category">> CLASSIFICATION</label>
              <div class="custom-select" bind:this={dropdownEl}>
                <button type="button" class="select-trigger" on:click={() => dropdownOpen = !dropdownOpen}>
                  <span>{formData.category}</span>
                  <span class="arrow" class:open={dropdownOpen}>▼</span>
                </button>
                {#if dropdownOpen}
                <div class="select-options">
                  {#each ['Food','Shopping','Transport','Entertainment','Health','Utilities','Other'] as opt}
                  <div class="option" class:selected={formData.category === opt} on:click={() => { formData.category = opt; dropdownOpen = false; }}>
                    {opt}
                  </div>
                  {/each}
                </div>
                {/if}
              </div>
            </div>
          </div>

          <div class="form-group">
            <label for="total">> TOTAL VALUATION (₹)</label>
            <input type="number" step="0.01" id="total" bind:value={formData.total} class="amount-input" />
          </div>

          <!-- Items Terminal Feed -->
          <div class="items-section">
            <div class="items-header">
              <span class="items-title">> PARSED LINE ITEMS</span>
              <button class="add-item-btn" on:click={addItem}>+ ADD ITEM</button>
            </div>

            {#each formData.items as item, index}
              <div class="item-row">
                <span class="term-prefix">></span>
                <input
                  type="text"
                  placeholder="ITEM NAME"
                  bind:value={item.name}
                  class="item-name"
                />
                <input
                  type="number"
                  step="0.01"
                  placeholder="PRICE"
                  bind:value={item.price}
                  on:input={calculateTotal}
                  class="item-price"
                />
                <button class="remove-item-btn" on:click={() => removeItem(index)}>✕</button>
              </div>
            {/each}
          </div>

          <!-- Action Buttons -->
          <div class="action-buttons">
            <button class="cyber-btn-pri flex-1" on:click={() => saveReceipt(false)}>
              COMMIT TO GRAVEYARD
            </button>
            <button class="cyber-btn-sec flex-1" on:click={() => saveReceipt(true)}>
              SPLIT CREDITS
            </button>
          </div>
        </div>
      </div>
    {/if}
  {/if}
</div>

<style>
  .scan-page {
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
    backdrop-filter: blur(24px);
  }

  .target-reticle {
    background: rgba(255, 255, 255, 0.02);
    border: 2px dashed #39FF14;
    border-radius: 8px;
    padding: 5rem 2rem;
    text-align: center;
    transition: all 0.3s ease;
    cursor: crosshair;
    position: relative;
  }

  .target-reticle.dragging, .target-reticle:hover {
    box-shadow: 0 0 30px rgba(57, 255, 20, 0.4);
    background: rgba(57, 255, 20, 0.05);
  }

  .file-input {
    display: none;
  }

  .upload-label {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    cursor: crosshair;
  }

  .reticle-icon {
    font-size: 4rem;
  }

  .upload-title {
    font-size: 1.5rem;
    font-weight: 900;
    color: #FFFFFF;
    font-family: 'Orbitron', sans-serif;
    letter-spacing: 1px;
  }

  .upload-subtitle {
    color: rgba(255, 255, 255, 0.4);
  }

  .loading-container {
    padding: 4rem 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
  }

  .sweep-scanner {
    height: 120px;
    background: rgba(57, 255, 20, 0.05);
    border: 1px solid #39FF14;
    position: relative;
    margin-bottom: 1.5rem;
    overflow: hidden;
  }

  @keyframes sweep {
    0% { top: 0; }
    100% { top: 100%; }
  }

  .sweep-line {
    width: 100%;
    height: 3px;
    background: #39FF14;
    box-shadow: 0 0 15px #39FF14;
    position: absolute;
    animation: sweep 1.5s infinite linear;
  }

  .loading-text {
    font-size: 1.8rem;
    color: #39FF14;
    text-shadow: 0 0 10px #39FF14;
  }

  .loading-sub {
    color: rgba(255, 255, 255, 0.4);
    margin-top: 0.5rem;
    font-size: 0.85rem;
  }

  .progress-bar-track {
    height: 8px;
    background: rgba(180, 100, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
    margin: 1rem auto;
    max-width: 400px;
  }

  .progress-bar-fill {
    height: 100%;
    width: 84%;
    background: linear-gradient(90deg, #39FF14, #FF6B00);
    box-shadow: 0 0 10px #39FF14;
  }

  .scanner-results {
    display: grid;
    grid-template-columns: 1fr 1.5fr;
    gap: 1.5rem;
  }

  @media (max-width: 850px) {
    .scanner-results {
      grid-template-columns: 1fr;
    }
  }

  .section-title {
    font-size: 1.1rem;
    margin-bottom: 1.25rem;
    color: #FFFFFF;
  }

  .image-wrapper {
    max-height: 450px;
    overflow: hidden;
    border: 1px solid rgba(180, 100, 255, 0.2);
  }

  .receipt-img {
    width: 100%;
    object-fit: contain;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin-bottom: 1.25rem;
  }

  .form-group label {
    font-size: 0.75rem;
    color: #FF6B00;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .amount-input {
    color: #FFE600 !important;
    font-size: 1.2rem !important;
    font-weight: 700;
  }

  .items-section {
    background: rgba(57, 255, 20, 0.03);
    border: 1px solid rgba(180, 100, 255, 0.2);
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }

  .items-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .items-title {
    font-size: 0.8rem;
    color: #FF6B00;
  }

  .add-item-btn {
    background: transparent;
    border: none;
    color: #39FF14;
    font-weight: 700;
    cursor: crosshair;
    font-size: 0.8rem;
    font-family: 'Orbitron', sans-serif;
    padding: 0;
  }

  .item-row {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    align-items: center;
  }

  .term-prefix {
    color: #39FF14;
  }

  .item-name { flex: 2; }
  .item-price { flex: 1; color: #FFE600 !important; }

  .remove-item-btn {
    background: transparent;
    border: none;
    color: #FF2D78;
    cursor: crosshair;
    font-size: 1.1rem;
    padding: 0 0.4rem;
  }

  .action-buttons {
    display: flex;
    gap: 1rem;
  }

  .cyber-btn-pri {
    background: linear-gradient(135deg, #39FF14, #B44CFF);
    color: #0D0015;
    font-weight: 900;
    padding: 12px 24px;
    border: none;
    font-family: 'Orbitron', sans-serif;
    cursor: crosshair;
  }

  .cyber-btn-sec {
    background: transparent;
    border: 1px solid #FF2D78;
    color: #FF2D78;
    font-weight: 700;
    padding: 12px 24px;
    font-family: 'Orbitron', sans-serif;
    cursor: crosshair;
  }

  .w-full { width: 100%; }
  .mt-3 { margin-top: 0.75rem; }
  .flex-1 { flex: 1; text-align: center; justify-content: center; }

  .custom-select { position: relative; width: 100%; }

  .select-trigger {
    width: 100%;
    background: rgba(57,255,20,0.05);
    border: 1px solid rgba(180,100,255,0.3);
    color: white;
    padding: 10px 16px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: crosshair;
    clip-path: none;
    background-image: none;
  }

  .select-trigger:hover { border-color: #39FF14; }

  .arrow { color: #B44CFF; transition: transform 0.2s; font-size: 10px; }
  .arrow.open { transform: rotate(180deg); }

  .select-options {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: #0D0015;
    border: 1px solid rgba(180,100,255,0.4);
    backdrop-filter: blur(20px);
    z-index: 1000;
    max-height: 280px;
    overflow-y: auto;
  }

  .option {
    padding: 12px 16px;
    color: rgba(255,255,255,0.7);
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    cursor: crosshair;
    border-left: 3px solid transparent;
    transition: all 0.15s;
  }

  .option:hover { background: rgba(57,255,20,0.08); color: #39FF14; border-left-color: #39FF14; }
  .option.selected { color: #39FF14; border-left-color: #39FF14; background: rgba(57,255,20,0.05); }
</style>
