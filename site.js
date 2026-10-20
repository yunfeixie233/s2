(() => {
  'use strict';
  const tocLinks = [...document.querySelectorAll('.article-toc a')];
  const targets = [...new Set(tocLinks.map(link => document.getElementById(decodeURIComponent(link.hash.slice(1)))).filter(Boolean))];
  const mobileToc = document.querySelector('.mobile-toc');
  let ticking = false;
  let currentId;
  function markSection(id) {
    if (id === currentId) return;
    currentId = id;
    let currentLabel = 'Introduction';
    tocLinks.forEach(link => {
      if (decodeURIComponent(link.hash.slice(1)) === id) {
        link.setAttribute('aria-current', 'location');
        currentLabel = link.textContent;
      } else link.removeAttribute('aria-current');
    });
    document.querySelectorAll('.toc-group').forEach(group => {
      group.open = [...group.querySelectorAll('a')].some(link => decodeURIComponent(link.hash.slice(1)) === id);
    });
    mobileToc.querySelector('.current-section').textContent = currentLabel;
  }
  function updateToc() {
    let current = targets[0];
    for (const target of targets) {
      if (target.getBoundingClientRect().top <= Math.max(180, innerHeight * .25)) current = target;
    }
    if (current) markSection(current.id);
    ticking = false;
  }
  addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(updateToc); ticking = true; }
  }, { passive: true });
  addEventListener('resize', updateToc);
  updateToc();
  tocLinks.forEach(link => link.addEventListener('click', () => {
    markSection(decodeURIComponent(link.hash.slice(1)));
    mobileToc.open = false;
  }));

  // Keep margin references out of article flow, including beside wide figures.
  const article = document.querySelector('.content');
  const marginNotes = [...article.querySelectorAll('.sidenote')];
  const marginBreakpoint = matchMedia('(min-width: 1280px)');
  let marginLayoutPending = false;
  function layoutMarginNotes() {
    if (!marginBreakpoint.matches) {
      article.classList.remove('has-margin-notes');
      return;
    }
    const body = article.getBoundingClientRect();
    const figureRight = Math.max(body.right, ...[...article.querySelectorAll('.wide-figure')].map(figure => figure.getBoundingClientRect().right));
    const railLeft = Math.max(body.right + 64, figureRight + 24);
    const railWidth = Math.min(300, document.documentElement.clientWidth - railLeft - 24);
    if (railWidth < 180) {
      article.classList.remove('has-margin-notes');
      return;
    }
    article.classList.add('has-margin-notes');
    article.style.setProperty('--margin-note-width', `${railWidth}px`);
    let nextTop = body.top;
    marginNotes.forEach(note => {
      const marker = note.previousElementSibling?.previousElementSibling;
      if (!marker) return;
      const parent = (note.offsetParent || article).getBoundingClientRect();
      const top = Math.max(marker.getBoundingClientRect().top, nextTop);
      note.style.setProperty('--note-left', `${railLeft - parent.left}px`);
      note.style.setProperty('--note-top', `${top - parent.top}px`);
      nextTop = top + note.getBoundingClientRect().height + 12;
    });
    updateToc();
  }
  function requestMarginLayout() {
    if (marginLayoutPending) return;
    marginLayoutPending = true;
    requestAnimationFrame(() => {
      marginLayoutPending = false;
      layoutMarginNotes();
    });
  }
  layoutMarginNotes();
  addEventListener('resize', requestMarginLayout);
  addEventListener('load', requestMarginLayout);
  document.fonts?.ready.then(requestMarginLayout);
  article.querySelectorAll('img, video').forEach(media => {
    media.addEventListener('load', requestMarginLayout);
    media.addEventListener('loadedmetadata', requestMarginLayout);
  });
  new ResizeObserver(requestMarginLayout).observe(article);

  document.querySelectorAll('.figure-panels').forEach(gallery => {
    const buttons = [...gallery.querySelectorAll('.panel-selector')];
    const scroll = gallery.querySelector('.figure-scroll');
    const image = scroll.querySelector('img');
    let selected = buttons[0];
    function panelPosition(button) {
      return Math.min(scroll.scrollWidth - scroll.clientWidth, Number(button.dataset.panelStart) * image.clientWidth);
    }
    function showPanel(button) {
      selected = button;
      buttons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      scroll.scrollTo({left: panelPosition(button), behavior: 'instant'});
    }
    gallery.querySelector('.panel-controls').hidden = false;
    buttons.forEach(button => button.addEventListener('click', () => showPanel(button)));
    scroll.addEventListener('scroll', () => {
      selected = buttons.reduce((best, item) => Math.abs(panelPosition(item) - scroll.scrollLeft) < Math.abs(panelPosition(best) - scroll.scrollLeft) ? item : best);
      buttons.forEach(item => item.setAttribute('aria-pressed', String(item === selected)));
    }, {passive: true});
    addEventListener('resize', () => showPanel(selected));
  });

  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const videos = [...document.querySelectorAll('.alignment-video')];
  const observer = new IntersectionObserver(entries => {
    entries.forEach(({ target: video, isIntersecting }) => {
      video.dataset.inView = String(isIntersecting);
      if (isIntersecting && !reducedMotion.matches && video.dataset.userPaused !== 'true' && !document.hidden) {
        video.play().catch(() => {});
      } else video.pause();
    });
  }, { threshold: .2 });
  videos.forEach(video => {
    video.controls = false;
    const controls = video.nextElementSibling;
    controls.hidden = false;
    const toggle = controls.querySelector('.animation-toggle');
    function updateButton() {
      toggle.textContent = video.paused ? 'Play' : 'Pause';
      toggle.setAttribute('aria-label', `${video.paused ? 'Play' : 'Pause'} animation ${video.id.split('-')[1]}`);
    }
    video.addEventListener('play', updateButton);
    video.addEventListener('pause', updateButton);
    toggle.addEventListener('click', () => {
      if (video.paused) {
        video.dataset.userPaused = 'false';
        video.play().catch(() => {});
      } else {
        video.dataset.userPaused = 'true';
        video.pause();
      }
    });
    controls.querySelector('.animation-restart').addEventListener('click', () => {
      video.currentTime = 0;
      video.dataset.userPaused = 'false';
      video.play().catch(() => {});
    });
    updateButton();
    observer.observe(video);
  });
  reducedMotion.addEventListener('change', () => {
    if (reducedMotion.matches) videos.forEach(video => video.pause());
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) videos.forEach(video => video.pause());
    else videos.filter(video => video.dataset.inView === 'true' && video.dataset.userPaused !== 'true' && !reducedMotion.matches).forEach(video => video.play().catch(() => {}));
  });

  document.querySelectorAll('.copy-citation').forEach(button => {
    button.hidden = false;
    const originalLabel = button.textContent;
    button.addEventListener('click', async () => {
      const text = document.getElementById(button.dataset.copyTarget).textContent;
      try {
        if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(text);
        else {
          const field = document.createElement('textarea');
          field.value = text;
          field.style.cssText = 'position:fixed;left:-9999px;top:0';
          document.body.append(field);
          field.select();
          const copied = document.execCommand('copy');
          field.remove();
          if (!copied) throw new Error('Copy unavailable');
        }
        button.textContent = 'Copied';
      } catch {
        button.textContent = 'Select text to copy';
      }
      setTimeout(() => { button.textContent = originalLabel; }, 1800);
    });
  });

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

  const dialog = document.querySelector('.figure-dialog');
  const dialogImage = dialog.querySelector('.dialog-image');
  const imageWrap = dialog.querySelector('.dialog-image-wrap');
  const zoomButton = dialog.querySelector('.zoom-button');
  let lastFigureButton = null;
  document.querySelectorAll('.figure-button, .full-figure-link').forEach(button => {
    button.addEventListener('click', () => {
      const figure = button.closest('figure');
      const source = figure.querySelector('.figure-overview img') || button.querySelector('img');
      lastFigureButton = button;
      dialogImage.src = source.src;
      dialogImage.alt = source.alt;
      dialog.querySelector('.dialog-title').textContent = 'Figure ' + figure.dataset.figure;
      const caption = figure.querySelector('.caption-text').cloneNode(true);
      caption.querySelectorAll('.sidenote, .sidenote-number, .margin-toggle').forEach(node => node.remove());
      dialog.querySelector('.dialog-caption').replaceChildren(caption);
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
