(() => {
  'use strict';
  const tocLinks = [...document.querySelectorAll('.left-toc a')];
  const targets = tocLinks.map(link => document.getElementById(link.hash.slice(1))).filter(Boolean);
  let ticking = false;
  function markSection(id) {
    tocLinks.forEach(link => {
      if (link.hash === '#' + id) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }
  function updateToc() {
    let current = targets[0];
    for (const target of targets) {
      if (target.getBoundingClientRect().top <= Math.max(140, window.innerHeight * 0.25)) current = target;
    }
    if (current) markSection(current.id);
    ticking = false;
  }
  addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(updateToc); ticking = true; }
  }, { passive: true });
  addEventListener('resize', updateToc);
  updateToc();
  tocLinks.forEach(link => link.addEventListener('click', () => markSection(link.hash.slice(1))));

  const technicalNotes = [...document.querySelectorAll('.technical-note')];
  let notesOpenBeforePrint;
  addEventListener('beforeprint', () => {
    notesOpenBeforePrint = technicalNotes.map(note => note.open);
    technicalNotes.forEach(note => { note.open = true; });
  });
  addEventListener('afterprint', () => {
    if (notesOpenBeforePrint) technicalNotes.forEach((note, i) => { note.open = notesOpenBeforePrint[i]; });
    notesOpenBeforePrint = undefined;
  });

  const overlapButton = document.querySelector('.overlap-button');
  const explainer = document.querySelector('.explainer');
  const overlapDescription = document.querySelector('.overlap-description');
  overlapButton?.addEventListener('click', () => {
    const active = overlapButton.getAttribute('aria-pressed') !== 'true';
    overlapButton.setAttribute('aria-pressed', String(active));
    overlapButton.textContent = active ? 'Shared neighbors shown' : 'Show shared neighbors';
    overlapButton.setAttribute('aria-label', overlapButton.textContent);
    explainer.classList.toggle('show-shared', active);
    overlapDescription.textContent = active
      ? 'A and C are neighbors in both spaces. B is close only in the model’s representation; D is close only in motion.'
      : 'Both panels contain the same episodes. Compare the three neighbors of the query in each space.';
  });

  const dialog = document.querySelector('.figure-dialog');
  const dialogImage = dialog.querySelector('.dialog-image');
  const imageWrap = dialog.querySelector('.dialog-image-wrap');
  const zoomButton = dialog.querySelector('.zoom-button');
  let lastFigureButton = null;
  document.querySelectorAll('.figure-button').forEach(button => {
    button.addEventListener('click', () => {
      const figure = button.closest('figure');
      const source = button.querySelector('img');
      lastFigureButton = button;
      dialogImage.src = source.src;
      dialogImage.alt = source.alt;
      dialog.querySelector('.dialog-title').textContent = 'Figure ' + figure.dataset.figure;
      dialog.querySelector('.dialog-caption').textContent = figure.querySelector('.caption-text').textContent;
      imageWrap.classList.remove('actual-size');
      zoomButton.textContent = 'Actual size';
      zoomButton.setAttribute('aria-pressed', 'false');
      document.body.classList.add('dialog-open');
      dialog.showModal();
      imageWrap.scrollTo(0, 0);
    });
  });
  dialog.querySelector('.close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('close', () => {
    document.body.classList.remove('dialog-open');
    lastFigureButton?.focus({ preventScroll: true });
  });
  zoomButton.addEventListener('click', () => {
    const actual = imageWrap.classList.toggle('actual-size');
    zoomButton.textContent = actual ? 'Fit to window' : 'Actual size';
    zoomButton.setAttribute('aria-pressed', String(actual));
  });
})();
