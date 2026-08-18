<script>
  import '../app.css';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '⚡' },
    { path: '/scan', label: 'Scan', icon: '📷' },
    { path: '/splits', label: 'Splits', icon: '👻' },
    { path: '/report', label: 'Report', icon: '📊' }
  ];

  let currentTime = '';

  function updateClock() {
    const now = new Date();
    currentTime = now.toTimeString().split(' ')[0] + '.' + String(now.getMilliseconds()).padStart(3, '0').slice(0, 2);
  }

  onMount(() => {
    updateClock();
    const interval = setInterval(updateClock, 100);
    return () => clearInterval(interval);
  });
</script>

<div class="layout-container">
  <!-- Top HUD Header Navbar -->
  <header class="top-hud-bar">
    <div class="brand">
      <span class="brand-icon">⚡</span>
      <h1 class="brand-title">
        <span class="glitch-text" data-text="RCPT_GRVYRD">RECEIPT GRAVEYARD</span>
      </h1>
    </div>

    <nav class="hud-nav">
      {#each navItems as item}
        <a
          href={item.path}
          class="hud-nav-item"
          class:active={$page.url.pathname === item.path}
        >
          <span class="nav-icon">{item.icon}</span>
          <span class="nav-label">{item.label}</span>
        </a>
      {/each}
    </nav>

    <div class="hud-right">
      <span class="hud-status-dot"></span>
      <span class="hud-clock">{currentTime}</span>
    </div>
  </header>

  <!-- Main Content Area -->
  <main class="main-content">
    <slot />
  </main>

  <!-- Mobile Bottom Navigation -->
  <nav class="bottom-nav">
    {#each navItems as item}
      <a
        href={item.path}
        class="bottom-nav-item"
        class:active={$page.url.pathname === item.path}
      >
        <span class="bottom-icon">{item.icon}</span>
        <span class="bottom-label">{item.label}</span>
      </a>
    {/each}
  </nav>
</div>

<style>
  .layout-container {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  .top-hud-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 2rem;
    background: rgba(13, 0, 21, 0.85);
    border-bottom: 1px solid rgba(180, 100, 255, 0.2);
    backdrop-filter: blur(24px);
    position: sticky;
    top: 0;
    z-index: 100;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .brand-icon {
    font-size: 1.5rem;
    color: #39FF14;
    text-shadow: 0 0 10px #39FF14;
  }

  .brand-title {
    font-size: 1.2rem;
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
  }

  .glitch-text {
    background: linear-gradient(135deg, #39FF14, #B44CFF);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    display: inline-block;
  }

  .hud-nav {
    display: flex;
    gap: 1.5rem;
  }

  .hud-nav-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: rgba(255, 255, 255, 0.4);
    text-decoration: none;
    font-family: 'Orbitron', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    transition: all 0.2s ease;
    border: 1px solid transparent;
  }

  .hud-nav-item:hover {
    color: #FFFFFF;
    border-color: rgba(180, 100, 255, 0.3);
    background: rgba(255, 255, 255, 0.04);
  }

  .hud-nav-item.active {
    color: #39FF14;
    text-shadow: 0 0 10px #39FF14;
    border-bottom: 2px solid #39FF14;
    background: rgba(57, 255, 20, 0.08);
  }

  .hud-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .hud-status-dot {
    width: 8px;
    height: 8px;
    background-color: #39FF14;
    border-radius: 50%;
    box-shadow: 0 0 10px #39FF14;
  }

  .hud-clock {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1rem;
    color: #B44CFF;
    letter-spacing: 1px;
  }

  .main-content {
    flex: 1;
    padding: 2rem;
    max-width: 1300px;
    width: 100%;
    margin: 0 auto;
  }

  .bottom-nav {
    display: none;
  }

  @media (max-width: 768px) {
    .hud-nav {
      display: none;
    }

    .main-content {
      padding: 1rem;
      padding-bottom: 5.5rem;
    }

    .bottom-nav {
      display: flex;
      justify-content: space-around;
      align-items: center;
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(13, 0, 21, 0.95);
      border-top: 1px solid rgba(180, 100, 255, 0.2);
      padding: 0.6rem 0;
      z-index: 100;
      backdrop-filter: blur(24px);
    }

    .bottom-nav-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.2rem;
      color: rgba(255, 255, 255, 0.4);
      text-decoration: none;
      font-size: 0.7rem;
      font-family: 'Orbitron', sans-serif;
      font-weight: 700;
    }

    .bottom-nav-item.active {
      color: #39FF14;
      text-shadow: 0 0 10px #39FF14;
    }
  }
</style>
