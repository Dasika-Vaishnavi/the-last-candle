(() => {
  const audio = new Audio('/static/audio/background.mp3');
  audio.loop = true;
  audio.preload = 'none';

  let volume = Number(localStorage.getItem('tlc:music-volume') ?? 25);
  volume = Number.isFinite(volume) ? Math.max(0, Math.min(100, volume)) : 25;
  audio.volume = volume / 100;

  const style = document.createElement('style');
  style.textContent = `
    #tlc-music {
      display:flex;
      align-items:center;
      flex-wrap:wrap;
      gap:9px;
    }
    #tlc-music button {
      background:#E3B23C;
      color:#1A1A1A;
      border:3px solid #1A1A1A;
      border-radius:14px;
      box-shadow:0 4px 0 #1A1A1A;
      padding:7px 12px;
      font:21px 'Patrick Hand',cursive;
      cursor:pointer;
    }
    #tlc-music label {
      display:flex;
      align-items:center;
      gap:7px;
      color:#F4E9D8;
      font:700 13px Nunito,sans-serif;
    }
    #tlc-music input {
      width:100px;
      accent-color:#E3B23C;
    }
  `;
  document.head.appendChild(style);

  function updateButton() {
    const button = document.getElementById('tlc-music-button');
    if (!button) return;
    button.textContent = audio.paused ? '♫ Music off' : '♫ Music on';
    button.setAttribute('aria-pressed', String(!audio.paused));
  }

  function mount() {
    const bar = document.querySelector('.top-controls');
    if (!bar || document.getElementById('tlc-music')) return;

    bar.insertAdjacentHTML('beforeend', `
      <div id="tlc-music">
        <button id="tlc-music-button" type="button">♫ Music off</button>
        <label>
          Volume
          <input id="tlc-music-volume" type="range"
            min="0" max="100" step="5" value="${volume}"
            aria-label="Background music volume">
          <span id="tlc-music-percent">${volume}%</span>
        </label>
      </div>
    `);

    updateButton();
  }

  const app = document.getElementById('app');
  new MutationObserver(mount).observe(app, {
    childList:true,
    subtree:true
  });
  mount();

  document.addEventListener('click', async (event) => {
    if (!event.target.closest('#tlc-music-button')) return;

    if (audio.paused) {
      try {
        await audio.play();
      } catch (error) {
        alert('Music could not play. Check the MP3 file.');
      }
    } else {
      audio.pause();
    }

    updateButton();
  });

  document.addEventListener('input', (event) => {
    if (event.target.id !== 'tlc-music-volume') return;

    volume = Number(event.target.value);
    audio.volume = volume / 100;
    localStorage.setItem('tlc:music-volume', String(volume));

    const label = document.getElementById('tlc-music-percent');
    if (label) label.textContent = volume + '%';
  });
})();
