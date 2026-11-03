(() => {
  const ROUND_SECONDS = 60;
  const PASSIVE_DECAY = 9;
  const STOKE_AMOUNT = 12;

  const flameValue = document.getElementById('flameValue');
  const timeValue = document.getElementById('timeValue');
  const statusText = document.getElementById('statusText');
  const flame = document.getElementById('flame');
  const stokeBtn = document.getElementById('stokeBtn');
  const restartBtn = document.getElementById('restartBtn');

  let flameLevel = 100;
  let timeLeft = ROUND_SECONDS;
  let timerId = null;
  let active = false;

  function updateUi() {
    flameValue.textContent = String(Math.round(flameLevel));
    timeValue.textContent = String(timeLeft);

    const intensity = Math.max(0, flameLevel / 100);
    flame.style.opacity = String(Math.max(0, intensity));
    flame.style.transform = `translateX(-50%) scale(${0.65 + intensity * 0.45})`;
    flame.style.filter = `brightness(${0.5 + intensity * 0.8})`;
  }

  function endGame(win) {
    active = false;
    stokeBtn.disabled = true;
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }

    if (win) {
      statusText.textContent = 'Dawn arrives. You kept the last candle alive!';
    } else {
      statusText.textContent = 'The flame died out. Darkness wins.';
      flameLevel = 0;
      updateUi();
    }
  }

  function tick() {
    if (!active) {
      return;
    }

    timeLeft = Math.max(0, timeLeft - 1);
    flameLevel = Math.max(0, flameLevel - PASSIVE_DECAY);

    updateUi();

    if (flameLevel <= 0) {
      endGame(false);
      return;
    }

    if (timeLeft <= 0) {
      endGame(true);
    }
  }

  function startGameIfNeeded() {
    if (active) {
      return;
    }

    active = true;
    stokeBtn.disabled = false;
    statusText.textContent = 'Keep stoking the flame to survive until dawn.';

    timerId = setInterval(tick, 1000);
  }

  function stokeFlame() {
    if (!active) {
      startGameIfNeeded();
    }

    if (!active) {
      return;
    }

    flameLevel = Math.min(100, flameLevel + STOKE_AMOUNT);
    statusText.textContent = 'You feed the fire. Keep going...';
    updateUi();
  }

  function restart() {
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }

    flameLevel = 100;
    timeLeft = ROUND_SECONDS;
    active = false;
    stokeBtn.disabled = false;
    statusText.textContent = 'Press "Stoke Flame" to begin.';
    updateUi();
  }

  stokeBtn.addEventListener('click', stokeFlame);
  restartBtn.addEventListener('click', restart);

  restart();
})();
