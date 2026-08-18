<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { page } from '$app/stores';

  let friends = [];
  let balances = { owed_to_you: [], you_owe: [] };
  let receipts = [];
  let settledSplits = [];
  let loading = true;
  let successFlash = '';

  let netStats = {
    totalSpent: 0,
    recovered: 0,
    actualLoss: 0
  };

  // Add friend form
  let newFriendName = '';

  // Split Modal state
  let showSplitModal = false;
  let selectedReceipt = null;
  let splitMode = 'equal'; // 'equal', 'custom', 'item'
  let payerType = 'you'; // 'you' or friend.id

  // Split state per friend
  let selectedFriendIds = [];
  let customAmounts = {}; // friend_id -> amount
  let itemAssignments = {}; // itemIndex -> friend_id or 'you'

  // Payment Proof Modal state
  let showProofModal = false;
  let pendingSplitId = null;
  let proofPreview = null;
  let proofBase64 = null;
  let proofInput;

  // Lightbox Modal state
  let showLightbox = false;
  let lightboxImage = null;

  async function refreshAll() {
    loading = true;
    try {
      const currentMonth = new Date().toISOString().slice(0, 7);
      const [fData, bData, rData, sData, settledData] = await Promise.all([
        api.getFriends(),
        api.getBalances(),
        api.getReceipts(),
        api.getSummary(currentMonth),
        api.getSettledSplits()
      ]);
      friends = fData;
      balances = bData;
      receipts = rData;
      settledSplits = settledData || [];

      const totalSpent = sData.total_this_month || 0;
      const recovered = bData.recovered || 0;
      const actualLoss = Math.max(0, totalSpent - recovered);

      netStats = {
        totalSpent,
        recovered,
        actualLoss
      };
    } catch (err) {
      console.error('Failed to load splits data:', err);
    } finally {
      loading = false;
    }
  }

  function resetSplitState() {
    selectedReceipt = null;
    splitMode = 'equal';
    payerType = 'you';
    selectedFriendIds = [];
    customAmounts = {};
    itemAssignments = {};
  }

  async function handleAddFriend() {
    if (!newFriendName.trim()) return;
    try {
      await api.createFriend(newFriendName.trim());
      newFriendName = '';
      await refreshAll();
    } catch (err) {
      alert('SYSTEM ALERT: FAILED TO REGISTER COMPANION');
    }
  }

  async function handleDeleteFriend(id) {
    if (!confirm('DISCONNECT COMPANION FROM NETWORK?')) return;
    try {
      await api.deleteFriend(id);
      await refreshAll();
    } catch (err) {
      alert('SYSTEM ALERT: DISCONNECT FAILED');
    }
  }

  function openSplitModal(receipt) {
    selectedReceipt = receipt;
    splitMode = 'equal';
    payerType = 'you';
    selectedFriendIds = friends.map(f => f.id);

    customAmounts = {};
    friends.forEach(f => { customAmounts[f.id] = 0; });

    itemAssignments = {};
    if (receipt.items) {
      receipt.items.forEach((_, idx) => {
        itemAssignments[idx] = 'you';
      });
    }

    showSplitModal = true;
  }

  function openProofModal(splitId) {
    if (!splitId) return;
    pendingSplitId = splitId;
    proofPreview = null;
    proofBase64 = null;
    showProofModal = true;
  }

  function handleProofFile(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      proofPreview = ev.target.result;
      const res = ev.target.result;
      proofBase64 = res.includes(',') ? res.split(',')[1] : res;
    };
    reader.readAsDataURL(file);
  }

  function handleProofDrop(e) {
    e.preventDefault();
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      proofPreview = ev.target.result;
      const res = ev.target.result;
      proofBase64 = res.includes(',') ? res.split(',')[1] : res;
    };
    reader.readAsDataURL(file);
  }

  async function confirmSettlement() {
    if (!pendingSplitId || !proofBase64) return;

    try {
      await api.toggleSplitPaid(pendingSplitId, proofBase64);
      showProofModal = false;
      proofPreview = null;
      proofBase64 = null;
      pendingSplitId = null;
      await refreshAll();
    } catch (err) {
      alert('SYSTEM ALERT: SETTLEMENT FAILED - ' + err.message);
    }
  }

  function openLightbox(imgUrl) {
    lightboxImage = imgUrl;
    showLightbox = true;
  }

  function toggleFriendSelection(id) {
    if (selectedFriendIds.includes(id)) {
      selectedFriendIds = selectedFriendIds.filter(fId => fId !== id);
    } else {
      selectedFriendIds = [...selectedFriendIds, id];
    }
  }

  async function handleSaveSplit() {
    if (!selectedReceipt) return;

    let splitPayload = [];
    const total = selectedReceipt.total;
    const isYouPayer = payerType === 'you';

    if (splitMode === 'equal') {
      const numPeople = selectedFriendIds.length + 1;
      const perPerson = parseFloat((total / numPeople).toFixed(2));

      selectedFriendIds.forEach(fId => {
        splitPayload.push({
          friend_id: fId,
          amount: perPerson,
          you_owe: !isYouPayer
        });
      });
    } else if (splitMode === 'custom') {
      selectedFriendIds.forEach(fId => {
        const amt = parseFloat(customAmounts[fId]) || 0;
        if (amt > 0) {
          splitPayload.push({
            friend_id: fId,
            amount: amt,
            you_owe: !isYouPayer
          });
        }
      });
    } else if (splitMode === 'item') {
      const friendTotals = {};
      selectedReceipt.items.forEach((item, idx) => {
        const assigned = itemAssignments[idx];
        if (assigned && assigned !== 'you') {
          friendTotals[assigned] = (friendTotals[assigned] || 0) + (parseFloat(item.price) || 0);
        }
      });

      Object.keys(friendTotals).forEach(fId => {
        splitPayload.push({
          friend_id: parseInt(fId),
          amount: parseFloat(friendTotals[fId].toFixed(2)),
          you_owe: !isYouPayer
        });
      });
    }

    if (splitPayload.length === 0) {
      alert('SYSTEM ALERT: SELECT COMPANIONS OR ASSIGN ITEMS');
      return;
    }

    try {
      await api.createSplits({
        receipt_id: selectedReceipt.id,
        split_type: splitMode,
        splits: splitPayload
      });

      // Fix 1: Close split modal, reset state, refresh all, show flash
      showSplitModal = false;
      resetSplitState();
      await refreshAll();

      successFlash = '> SPLIT COMMITTED SUCCESSFULLY';
      setTimeout(() => {
        successFlash = '';
      }, 2000);
    } catch (err) {
      alert('SYSTEM ALERT: SAVE SPLIT FAILED - ' + err.message);
    }
  }

  onMount(async () => {
    await refreshAll();
    const receiptIdParam = $page.url.searchParams.get('receipt_id');
    if (receiptIdParam) {
      const found = receipts.find(r => r.id === parseInt(receiptIdParam));
      if (found) {
        openSplitModal(found);
      }
    }
  });
</script>

<div class="splits-page">
  <header class="header">
    <h1 class="page-title">CREDITS & SPLITS MATRIX</h1>
    <p class="page-subtitle">> DISTRIBUTE FINANCIAL OBLIGATIONS</p>
  </header>

  <!-- Success Flash Notification -->
  {#if successFlash}
    <div class="success-flash cyber-glass">
      {successFlash}
    </div>
  {/if}

  <!-- Net Financial Position Full Width Banner -->
  <div class="net-position-card cyber-glass">
    <div class="net-title">> NET FINANCIAL POSITION</div>
    <div class="net-stats">
      <div class="net-stat-item">
        <span class="net-label">TOTAL SPENT</span>
        <span class="net-value val-white">₹{netStats.totalSpent.toLocaleString('en-IN')}</span>
      </div>
      <div class="net-stat-item">
        <span class="net-label">RECOVERED</span>
        <span class="net-value val-green">₹{netStats.recovered.toLocaleString('en-IN')}</span>
      </div>
      <div class="net-stat-item">
        <span class="net-label">ACTUAL LOSS</span>
        <span class="net-value val-red-pulse">₹{netStats.actualLoss.toLocaleString('en-IN')}</span>
      </div>
    </div>
  </div>

  <!-- Dual Credits Header Panels -->
  <div class="balances-banner">
    <div class="balance-card owed cyber-glass">
      <h3 class="balance-title">> CREDITS INCOMING (YOU ARE OWED)</h3>
      {#if balances.owed_to_you.length === 0}
        <p class="empty-bal">NO OUTSTANDING INCOMING CREDITS_</p>
      {:else}
        <ul class="balance-list">
          {#each balances.owed_to_you as b}
            <li class="balance-item">
              <span class="emoji">{b.friend_emoji}</span>
              <span class="text">{b.friend_name} OWES YOU <strong class="green-text">₹{b.amount.toLocaleString('en-IN')}</strong></span>
              {#if b.split_id}
                <button class="clear-debt-btn" on:click={() => openProofModal(b.split_id)}>
                  CLEAR DEBT
                </button>
              {/if}
            </li>
          {/each}
        </ul>
      {/if}
    </div>

    <div class="balance-card owing cyber-glass">
      <h3 class="balance-title">> CREDITS OUTGOING (YOU OWE)</h3>
      {#if balances.you_owe.length === 0}
        <p class="empty-bal">ZERO OUTGOING DEBT DETECTED_</p>
      {:else}
        <ul class="balance-list">
          {#each balances.you_owe as b}
            <li class="balance-item">
              <span class="emoji">{b.friend_emoji}</span>
              <span class="text">YOU OWE {b.friend_name} <strong class="red-text">₹{b.amount.toLocaleString('en-IN')}</strong></span>
              {#if b.split_id}
                <button class="clear-debt-btn" on:click={() => openProofModal(b.split_id)}>
                  CLEAR DEBT
                </button>
              {/if}
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  </div>

  <!-- Settled Transactions Section -->
  <div class="settled-section cyber-glass">
    <h3 class="section-title">> SETTLED TRANSACTIONS</h3>
    {#if settledSplits.length === 0}
      <p class="empty-bal">NO SETTLED TRANSACTIONS RECORDED YET_</p>
    {:else}
      <div class="settled-list">
        {#each settledSplits as s}
          <div class="settled-item">
            <div class="settled-info">
              <span class="emoji">{s.friend_emoji}</span>
              <span class="name">{s.friend_name}</span>
              <span class="amount amount-glow">₹{s.amount.toLocaleString('en-IN')}</span>
              <span class="type-badge">{s.you_owe ? 'YOU PAID' : 'RECEIVED'}</span>
            </div>
            {#if s.payment_proof}
              <button class="proof-thumb-btn" on:click={() => openLightbox(s.payment_proof)} title="View Proof Screenshot">
                <img src={s.payment_proof} alt="Payment Proof" class="proof-thumb" />
              </button>
            {:else}
              <span class="no-proof-tag">[NO PROOF]</span>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <div class="splits-grid">
    <!-- Companions Card -->
    <div class="friends-card cyber-glass">
      <h3 class="section-title">> NETWORK COMPANIONS</h3>

      <div class="add-friend-row">
        <input
          type="text"
          placeholder="COMPANION NAME"
          bind:value={newFriendName}
          on:keydown={(e) => e.key === 'Enter' && handleAddFriend()}
        />
        <button class="cyber-btn" on:click={handleAddFriend}>+ ADD</button>
      </div>

      {#if friends.length === 0}
        <p class="empty-sub">NO COMPANIONS CONNECTED TO NETWORK_</p>
      {:else}
        <div class="friends-list">
          {#each friends as f}
            <div class="friend-chip">
              <span class="friend-emoji">{f.emoji}</span>
              <span class="friend-name">{f.name}</span>
              <button class="remove-btn" on:click={() => handleDeleteFriend(f.id)}>
                REMOVE
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Receipts & Active Splits Card -->
    <div class="receipts-splits-card cyber-glass">
      <h3 class="section-title">> DATA POD SPLIT MATRIX</h3>

      {#if loading}
        <p class="loading-text">LOADING SPLIT MATRIX...</p>
      {:else if receipts.length === 0}
        <p class="empty-sub">NO RECEIPT DATA PODS FOUND FOR SPLITTING_</p>
      {:else}
        <div class="receipts-list">
          {#each receipts as r}
            <div class="receipt-split-item">
              <div class="r-info">
                <span class="r-merchant">{r.merchant}</span>
                <span class="r-date">{r.date} • TOTAL: <strong class="amount-glow">₹{r.total}</strong></span>
              </div>
              <button class="cyber-btn-sec" on:click={() => openSplitModal(r)}>
                SPLIT RECEIPT
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <!-- Glass Split Modal -->
  {#if showSplitModal && selectedReceipt}
    <div class="modal-backdrop" on:click|self={() => { showSplitModal = false; resetSplitState(); }}>
      <div class="modal-content cyber-glass">
        <div class="modal-header">
          <h2>SPLIT MATRIX: "{selectedReceipt.merchant}"</h2>
          <button class="close-btn" on:click={() => { showSplitModal = false; resetSplitState(); }}>✕</button>
        </div>

        <p class="receipt-total-badge">POD TOTAL: <strong class="amount-glow">₹{selectedReceipt.total}</strong></p>

        <!-- Mode Selector -->
        <div class="mode-tabs">
          <button class="mode-tab" class:active={splitMode === 'equal'} on:click={() => (splitMode = 'equal')}>
            EQUAL
          </button>
          <button class="mode-tab" class:active={splitMode === 'custom'} on:click={() => (splitMode = 'custom')}>
            CUSTOM
          </button>
          <button class="mode-tab" class:active={splitMode === 'item'} on:click={() => (splitMode = 'item')}>
            BY ITEM
          </button>
        </div>

        {#if splitMode === 'equal'}
          <div class="split-section">
            <p class="help-text">> SELECT COMPANIONS TO DIVIDE ₹{selectedReceipt.total} EQUALLY:</p>
            <div class="friend-check-list">
              {#each friends as f}
                <label class="check-label">
                  <input
                    type="checkbox"
                    checked={selectedFriendIds.includes(f.id)}
                    on:change={() => toggleFriendSelection(f.id)}
                  />
                  <span>{f.emoji} {f.name}</span>
                </label>
              {/each}
            </div>
          </div>
        {/if}

        {#if splitMode === 'custom'}
          <div class="split-section">
            <p class="help-text">> ENTER CUSTOM AMOUNT OWE PER COMPANION:</p>
            {#each friends as f}
              <div class="custom-row">
                <span>{f.emoji} {f.name}</span>
                <input
                  type="number"
                  step="0.01"
                  placeholder="₹ AMOUNT"
                  bind:value={customAmounts[f.id]}
                  on:input={() => {
                    if (!selectedFriendIds.includes(f.id)) {
                      selectedFriendIds = [...selectedFriendIds, f.id];
                    }
                  }}
                />
              </div>
            {/each}
          </div>
        {/if}

        {#if splitMode === 'item'}
          <div class="split-section">
            <p class="help-text">> ASSIGN LINE ITEMS TO COMPANIONS:</p>
            {#if !selectedReceipt.items || selectedReceipt.items.length === 0}
              <p class="empty-sub">NO PARSED LINE ITEMS FOUND IN POD_</p>
            {:else}
              {#each selectedReceipt.items as item, idx}
                <div class="item-assign-row">
                  <div class="item-info">
                    <span class="item-name">{item.name}</span>
                    <span class="item-price">₹{item.price}</span>
                  </div>
                  <select bind:value={itemAssignments[idx]}>
                    <option value="you">You</option>
                    {#each friends as f}
                      <option value={f.id}>{f.emoji} {f.name}</option>
                    {/each}
                  </select>
                </div>
              {/each}
            {/if}
          </div>
        {/if}

        <div class="modal-footer">
          <button class="cyber-btn-sec" on:click={() => { showSplitModal = false; resetSplitState(); }}>CANCEL</button>
          <button class="cyber-btn" on:click={handleSaveSplit}>COMMIT SPLIT</button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Payment Proof Modal -->
  {#if showProofModal}
    <div class="modal-overlay" on:click|self={() => { showProofModal = false; proofPreview = null; proofBase64 = null; pendingSplitId = null; }}>
      <div class="modal-panel">
        <h3>> PAYMENT VERIFICATION PROTOCOL</h3>
        <p class="modal-sub">UPLOAD PROOF OF TRANSACTION TO CONFIRM SETTLEMENT</p>
        <div class="proof-dropzone" on:dragover|preventDefault on:drop={handleProofDrop} on:click={() => proofInput.click()}>
          {#if proofPreview}
            <img src={proofPreview} alt="proof" style="max-width:100%;max-height:200px;object-fit:contain"/>
          {:else}
            <div>📸 DROP PAYMENT SCREENSHOT HERE</div>
            <div class="proof-sub">GPay / PhonePe / Bank Transfer / UPI</div>
          {/if}
        </div>
        <input type="file" accept="image/*" bind:this={proofInput} style="display:none" on:change={handleProofFile}/>
        <div class="modal-actions">
          <button class="abort-btn" on:click={() => { showProofModal = false; proofPreview = null; proofBase64 = null; pendingSplitId = null; }}>ABORT</button>
          <button class="confirm-btn" on:click={confirmSettlement} disabled={!proofBase64}>CONFIRM SETTLEMENT</button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Lightbox Modal for Proof Image -->
  {#if showLightbox && lightboxImage}
    <div class="lightbox-backdrop" on:click|self={() => (showLightbox = false)}>
      <div class="lightbox-content">
        <img src={lightboxImage} alt="Full Payment Proof" class="lightbox-img" />
        <button class="lightbox-close" on:click={() => (showLightbox = false)}>CLOSE [✕]</button>
      </div>
    </div>
  {/if}
</div>

<style>
  .splits-page {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .success-flash {
    color: #39FF14;
    font-family: 'Orbitron', sans-serif;
    font-weight: 700;
    text-shadow: 0 0 10px #39FF14;
    border-color: #39FF14 !important;
    padding: 1rem 1.5rem;
  }

  .net-position-card {
    width: 100%;
    padding: 1.25rem 1.5rem;
  }

  .net-title {
    font-size: 0.8rem;
    color: #FF6B00;
    font-family: 'Share Tech Mono', monospace;
    letter-spacing: 1px;
    margin-bottom: 0.75rem;
  }

  .net-stats {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1.5rem;
    flex-wrap: wrap;
  }

  .net-stat-item {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .net-label {
    font-size: 0.75rem;
    color: #FF6B00;
    font-family: 'Share Tech Mono', monospace;
  }

  .net-value {
    font-size: 1.8rem;
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
  }

  .val-white {
    color: #FFFFFF;
  }

  .val-green {
    color: #39FF14;
    text-shadow: 0 0 10px #39FF14;
  }

  @keyframes pulse-loss {
    0%, 100% { color: #FF2D78; text-shadow: 0 0 20px #FF2D78, 0 0 40px rgba(255, 45, 120, 0.6); }
    50% { color: #FF2D78; text-shadow: 0 0 5px #FF2D78; }
  }

  .val-red-pulse {
    color: #FF2D78;
    animation: pulse-loss 2s infinite ease-in-out;
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

  .balances-banner {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  @media (max-width: 768px) {
    .balances-banner { grid-template-columns: 1fr; }
  }

  .balance-card.owed { border-left: 4px solid #39FF14; }
  .balance-card.owing { border-left: 4px solid #FF2D78; }

  .balance-title {
    font-size: 1rem;
    margin-bottom: 0.75rem;
    color: #FFFFFF;
  }

  .empty-bal { color: rgba(255, 255, 255, 0.4); font-size: 0.85rem; }

  .balance-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }

  .balance-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }

  .green-text { color: #39FF14; text-shadow: 0 0 10px #39FF14; }
  .red-text { color: #FF2D78; text-shadow: 0 0 10px #FF2D78; }

  .clear-debt-btn {
    margin-left: auto;
    background: transparent;
    border: 1px solid #39FF14;
    color: #39FF14;
    padding: 4px 8px;
    font-size: 10px;
    font-family: 'Share Tech Mono', monospace;
    cursor: crosshair;
  }

  .clear-debt-btn:hover {
    background: rgba(57, 255, 20, 0.15);
    box-shadow: 0 0 10px rgba(57, 255, 20, 0.3);
  }

  .settled-section {
    width: 100%;
  }

  .settled-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .settled-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(180, 100, 255, 0.15);
    padding: 0.75rem 1rem;
    border-radius: 4px;
  }

  .settled-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .type-badge {
    font-size: 0.75rem;
    color: #39FF14;
    background: rgba(57, 255, 20, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .proof-thumb-btn {
    background: transparent;
    border: 1px solid rgba(180, 100, 255, 0.3);
    padding: 2px;
    cursor: crosshair;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .proof-thumb-btn:hover {
    border-color: #39FF14;
    box-shadow: 0 0 10px rgba(57, 255, 20, 0.4);
  }

  .proof-thumb {
    width: 44px;
    height: 44px;
    object-fit: cover;
    border-radius: 2px;
  }

  .no-proof-tag {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.3);
  }

  .splits-grid {
    display: grid;
    grid-template-columns: 1fr 1.5fr;
    gap: 1.5rem;
  }

  @media (max-width: 850px) {
    .splits-grid { grid-template-columns: 1fr; }
  }

  .section-title { font-size: 1.1rem; margin-bottom: 1.25rem; color: #FFFFFF; }

  .add-friend-row {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.25rem;
  }

  .friends-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
  }

  .friend-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(180,100,255,0.1);
    border: 1px solid rgba(180,100,255,0.3);
    padding: 8px 12px;
    margin: 4px;
  }

  .friend-name {
    font-family: 'Share Tech Mono', monospace;
    color: white;
    font-size: 13px;
    text-transform: uppercase;
  }

  .remove-btn {
    background: transparent;
    border: 1px solid #FF2D78;
    color: #FF2D78;
    padding: 2px 8px;
    font-size: 10px;
    font-family: 'Share Tech Mono', monospace;
    cursor: crosshair;
    clip-path: none;
    background-image: none;
    letter-spacing: 0.1em;
  }

  .remove-btn:hover {
    background: rgba(255,45,120,0.15);
    box-shadow: 0 0 10px rgba(255,45,120,0.3);
    transform: none;
  }

  .receipts-list { display: flex; flex-direction: column; gap: 0.75rem; }

  .receipt-split-item {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(180, 100, 255, 0.15);
    border-radius: 4px;
    padding: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .r-merchant { font-weight: 700; display: block; color: #FFFFFF; }
  .r-date { font-size: 0.8rem; color: rgba(255, 255, 255, 0.4); }

  .amount-glow { color: #FFE600; text-shadow: 0 0 20px #FFE600; }

  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(13, 0, 21, 0.85);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 200;
    padding: 1rem;
    backdrop-filter: blur(24px);
  }

  .modal-content {
    max-width: 500px;
    width: 100%;
    position: relative;
    border-color: #39FF14 !important;
  }

  .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
  .close-btn { background: transparent; border: none; color: rgba(255, 255, 255, 0.4); font-size: 1.2rem; cursor: crosshair; padding: 0; }
  .close-btn:hover { color: #FF2D78; box-shadow: none; transform: none; }

  .receipt-total-badge { color: #39FF14; font-weight: 700; margin-bottom: 1rem; }

  .mode-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.25rem;
    background: rgba(180, 100, 255, 0.1);
    padding: 0.3rem;
    border-radius: 4px;
  }

  .mode-tab {
    flex: 1;
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.4);
    padding: 0.5rem;
    cursor: crosshair;
    font-weight: 700;
    font-family: 'Orbitron', sans-serif;
  }

  .mode-tab.active {
    background: #39FF14;
    color: #0D0015;
    box-shadow: 0 0 10px #39FF14;
  }

  .help-text { font-size: 0.8rem; color: #FF6B00; margin-bottom: 1rem; }
  .friend-check-list { display: flex; flex-direction: column; gap: 0.6rem; }
  .check-label { display: flex; align-items: center; gap: 0.5rem; cursor: crosshair; }
  .custom-row { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: 0.6rem; }
  .custom-row input { width: 120px; }

  .item-assign-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.6rem;
    background: rgba(57, 255, 20, 0.03);
    padding: 0.6rem;
    border-radius: 4px;
  }

  .item-name { font-weight: 700; display: block; color: #FFFFFF; }
  .item-price { font-size: 0.8rem; color: #FFE600; }
  .item-assign-row select { width: 140px; }

  .modal-footer { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }
  .cyber-btn { background: linear-gradient(135deg, #39FF14, #B44CFF); color: #0D0015; font-weight: 900; }
  .cyber-btn-sec { background: transparent; border: 1px solid #FF2D78; color: #FF2D78; font-weight: 700; }
  .empty-sub { color: rgba(255, 255, 255, 0.4); font-size: 0.85rem; }
  .loading-text { color: #39FF14; }

  /* Payment Proof Modal Specific Styles */
  .modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.85); backdrop-filter:blur(10px); z-index:9999; display:flex; align-items:center; justify-content:center; }
  .modal-panel { background:#0D0015; border:1px solid rgba(180,100,255,0.4); padding:40px; max-width:500px; width:90%; }
  .modal-panel h3 { font-family:'Orbitron',sans-serif; color:#39FF14; margin-bottom:8px; }
  .modal-sub { color:rgba(255,255,255,0.4); font-size:11px; margin-bottom:24px; }
  .proof-dropzone { border:2px dashed #39FF14; padding:40px; text-align:center; cursor:crosshair; color:rgba(255,255,255,0.5); margin-bottom:24px; min-height:150px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; }
  .proof-dropzone:hover { background:rgba(57,255,20,0.05); }
  .proof-sub { font-size:11px; color:rgba(255,255,255,0.3); }
  .modal-actions { display:flex; gap:12px; }
  .abort-btn { flex:1; background:transparent; border:1px solid #FF2D78; color:#FF2D78; padding:12px; font-family:'Orbitron',sans-serif; font-size:12px; cursor:crosshair; clip-path:none; }
  .confirm-btn { flex:2; background:linear-gradient(135deg,#39FF14,#B44CFF); color:black; padding:12px; font-family:'Orbitron',sans-serif; font-size:12px; font-weight:900; cursor:crosshair; clip-path:none; }
  .confirm-btn:disabled { opacity:0.3; cursor:not-allowed; }

  /* Lightbox Styles */
  .lightbox-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.9);
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    cursor: crosshair;
  }

  .lightbox-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .lightbox-img {
    max-width: 90vw;
    max-height: 80vh;
    object-fit: contain;
    border: 2px solid #39FF14;
    box-shadow: 0 0 30px rgba(57, 255, 20, 0.4);
  }

  .lightbox-close {
    background: transparent;
    border: 1px solid #FF2D78;
    color: #FF2D78;
    font-family: 'Share Tech Mono', monospace;
  }
</style>
