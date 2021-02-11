function initAutoReveal() {
  const elems = document.querySelectorAll(".autoreveal");
  elems.forEach(elem => {
    const rowToReveal = document.getElementById(elem.dataset.autorevealId);
    const countdown = new Countdown(elem, () => reveal(rowToReveal));
    countdown.startCounter()
  });
}

function reveal(element) {
  element.classList.remove("tasks-unpublished");
}

class Countdown {
  constructor(timeElement, finishAction) {
    this.endtime = timeElement.getAttribute("datetime");
    this.timeElement = timeElement;
    this.finishAction = finishAction;
    this.initialText = timeElement.innerText;
  }

  startCounter() {
    this.updateClock();
    if (this.getTimeRemaining().total > 0) {
      this.interval = setInterval(() => this.updateClock(), 1000);
    }
  }

  getTimeRemaining() {
    const total = Date.parse(this.endtime) - new Date();
    const seconds = Math.floor((total / 1000) % 60);
    const minutes = Math.floor((total / 1000 / 60) % 60);
    const hours = Math.floor((total / 1000 / 60 / 60) % 24);
    const days = Math.floor(total / 1000 / 60 / 60 / 24);
    return { total, days, hours, minutes, seconds };
  }

  updateClock() {
    const t = this.getTimeRemaining();
    const format = (number) => (number < 10 ? `0${number}` : number);
    const elem = this.timeElement;
    if (t.days > 0) {
      elem.innerText = t.days > 1 ? `in ${t.days} days` : "in 1 day";
    } else if (t.hours > 0) {
      elem.innerText = t.hours > 1 ? `in ${t.hours} hours` : "in 1 hour";
    } else if (t.minutes > 0) {
      elem.innerText = `in ${t.minutes}min ${t.seconds}s`
    } else {
      elem.innerText = `in ${t.seconds}s`
    }
    if (t.total <= 0) {
      elem.innerText = this.initialText;
      clearInterval(this.interval);
      this.finishAction();
    }
  }
}

if (document.readyState != "loading") {
  initAutoReveal();
} else {
  document.addEventListener("DOMContentLoaded", () => initAutoReveal());
}
