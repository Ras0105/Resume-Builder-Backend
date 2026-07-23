(function(){
  const form = document.getElementById('resumeForm');
  const steps = Array.from(document.querySelectorAll('.step'));
  const stepsNav = document.getElementById('stepsNav');
  const previewMount = document.getElementById('previewMount');
  const paymentOverlay = document.getElementById('paymentOverlay');
  const paymentStatusText = document.getElementById('paymentStatusText');
  let currentStep = 0;

  // Configure this to match whatever you charge — kept in paise (smallest
  // unit) to match what the backend expects. Adjust to your real price.
  const AMOUNT_PAISE = 2100; // ₹21
  const CURRENCY = 'INR';

  const API_BASE = window.RESUME_API_BASE || '';

  const STEP_LABELS = ['Contact','Summary','Education','Experience','Projects','Skills','Extras','Review'];

  STEP_LABELS.forEach((label, i) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'step-pip' + (i === 0 ? ' active' : '');
    btn.innerHTML = '<span class="n">' + String(i+1).padStart(2,'0') + '</span>' + label;
    btn.addEventListener('click', () => goToStep(i));
    stepsNav.appendChild(btn);
  });

  function goToStep(i){
    currentStep = Math.max(0, Math.min(steps.length - 1, i));
    steps.forEach(s => s.classList.toggle('active', Number(s.dataset.step) === currentStep));
    Array.from(stepsNav.children).forEach((pip, idx) => {
      pip.classList.toggle('active', idx === currentStep);
      pip.classList.toggle('done', idx < currentStep);
    });
    document.getElementById('prevBtn').style.visibility = currentStep === 0 ? 'hidden' : 'visible';
    const nextBtn = document.getElementById('nextBtn');
    nextBtn.textContent = currentStep === steps.length - 1 ? 'Done' : 'Next';
    document.querySelector('.builder-panel').scrollTo({top:0, behavior:'smooth'});
  }

  document.getElementById('nextBtn').addEventListener('click', () => {
    if (currentStep < steps.length - 1) goToStep(currentStep + 1);
  });
  document.getElementById('prevBtn').addEventListener('click', () => goToStep(currentStep - 1));

  // ---- Add / remove repeatable rows ----
  const containers = { edu: '.edu-rows', exp: '.exp-rows', proj: '.proj-rows', skill: '.skill-rows', leadership: '.leadership-rows', coding: '.coding-rows', custom: '.custom-rows' };
  const templates = { edu: 'tpl-edu', exp: 'tpl-exp', proj: 'tpl-proj', skill: 'tpl-skill', leadership: 'tpl-leadership', coding: 'tpl-coding', custom: 'tpl-custom' };

  form.addEventListener('click', (e) => {
    const addType = e.target.closest('[data-add]')?.dataset.add;
    if (addType) {
      const tpl = document.getElementById(templates[addType]);
      const node = tpl.content.cloneNode(true);
      document.querySelector(containers[addType]).appendChild(node);
      renderPreview();
      return;
    }
    const removeType = e.target.closest('[data-remove]')?.dataset.remove;
    if (removeType) {
      e.target.closest('.entry-card').remove();
      renderPreview();
    }
  });

  // ---- Live preview ----
  form.addEventListener('input', renderPreview);

  function esc(str){
    return (str || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  const val = (sel, root=document) => (root.querySelector(sel)?.value || '').trim();

  function cleanDisplay(raw){
    return raw.trim().replace(/^https?:\/\//i, '').replace(/^www\./i, '');
  }

  function ghPath(raw){
    return cleanDisplay(raw).replace(/^github\.com\//i, '').replace(/\/$/, '');
  }

  const ICON_LINKEDIN = '<svg class="r-icon" width="12" height="12" viewBox="0 0 24 24"><rect width="24" height="24" rx="5" fill="#1A1A1A"/><text x="12" y="16.5" font-size="11" font-family="Arial,sans-serif" font-weight="700" fill="#fff" text-anchor="middle">in</text></svg>';
  const ICON_GITHUB = '<svg class="r-icon" width="12" height="12" viewBox="0 0 24 24"><rect width="24" height="24" rx="5" fill="#1A1A1A"/><text x="12" y="16" font-size="9.5" font-family="Arial,sans-serif" font-weight="700" fill="#fff" text-anchor="middle">&lt;/&gt;</text></svg>';

  function linkify(raw, prefix, label, icon){
    if (!raw) return '';
    const trimmed = raw.trim();
    let href, text;
    if (prefix === 'mailto') { href = 'mailto:' + trimmed; text = esc(trimmed); }
    else if (prefix === 'tel') { href = 'tel:' + trimmed.replace(/[^\d+]/g, ''); text = esc(trimmed); }
    else { href = trimmed.startsWith('http') ? trimmed : 'https://' + trimmed; text = esc(cleanDisplay(trimmed)); }
    const labelPart = label ? '<strong>' + label + ': </strong>' : '';
    const iconPart = icon || '';
    return iconPart + labelPart + '<a href="' + href + '" target="_blank" rel="noopener">' + text + '</a>';
  }

  function linkifyAs(rawUrl, displayText){
    const text = esc(displayText);
    if (!rawUrl) return text;
    const href = rawUrl.trim().startsWith('http') ? rawUrl.trim() : 'https://' + rawUrl.trim();
    return '<a href="' + href + '" target="_blank" rel="noopener">' + text + '</a>';
  }

  function bulletsFromTextarea(raw){
    return raw.split('\n').map(l => l.trim()).filter(Boolean)
      .map(l => '<li>' + esc(l) + '</li>').join('');
  }

  function renderPreview(){
    const fullName = val('.f-fullName');
    const email = val('.f-email');
    const phone = val('.f-phone');
    const location = val('.f-location');
    const linkedin = val('.f-linkedin');
    const github = val('.f-github');
    const portfolio = val('.f-portfolio');
    const summary = val('.f-summary');

    const hasAnything = fullName || email || phone || location || linkedin || github || portfolio || summary
      || Array.from(document.querySelectorAll(
          '.edu-school,.exp-title,.proj-name,.skill-category,.skill-list,.lead-role,.coding-platform,.custom-heading,.f-interests,.f-certifications,.f-achievements'
        )).some(i => i.value.trim());

    if (!hasAnything) {
      previewMount.innerHTML = '<div class="empty-state">Start filling in your details on the left —<br>your resume builds here in real time.</div>';
      return;
    }

    let html = '<div class="resume-paper" id="resumePaper">';

    // Header
    html += '<div class="r-name">' + (esc(fullName) || 'Your Name') + '</div>';
    const contactParts = [];
    if (location) contactParts.push(esc(location));
    if (phone) contactParts.push(linkify(phone, 'tel'));
    if (email) contactParts.push(linkify(email, 'mailto'));
    if (linkedin) contactParts.push(linkify(linkedin, 'url', null, ICON_LINKEDIN));
    if (github) contactParts.push(linkify(github, 'url', null, ICON_GITHUB));
    if (portfolio) contactParts.push(linkify(portfolio, 'url'));
    if (contactParts.length) {
      html += '<div class="r-contact">' + contactParts.join('<span class="sep">|</span>') + '</div>';
    }
    if (summary) html += '<div class="r-summary">' + esc(summary) + '</div>';

    // Education
    const eduRows = Array.from(document.querySelectorAll('.edu-row')).map(row => ({
      school: val('.edu-school', row), location: val('.edu-location', row),
      degree: val('.edu-degree', row), gpa: val('.edu-gpa', row),
      start: val('.edu-start', row), end: val('.edu-end', row)
    })).filter(r => r.school || r.degree);

    if (eduRows.length) {
      html += '<div class="r-section"><h3>Education</h3>';
      eduRows.forEach(r => {
        const dates = [r.start, r.end].filter(Boolean).join(' – ');
        html += '<div class="r-entry">';
        html += '<div class="r-row"><strong>' + esc(r.school) + '</strong><span>' + esc(r.location) + '</span></div>';
        let degreeLine = esc(r.degree);
        if (r.gpa) degreeLine += '  ·  GPA: ' + esc(r.gpa);
        html += '<div class="r-row sub"><span class="r-italic">' + degreeLine + '</span><span class="r-italic">' + esc(dates) + '</span></div>';
        html += '</div>';
      });
      html += '</div>';
    }

    // Experience
    const expRows = Array.from(document.querySelectorAll('.exp-row')).map(row => ({
      title: val('.exp-title', row), company: val('.exp-company', row),
      location: val('.exp-location', row), dates: val('.exp-dates', row),
      bullets: val('.exp-bullets', row)
    })).filter(r => r.title || r.company);

    if (expRows.length) {
      html += '<div class="r-section"><h3>Experience</h3>';
      expRows.forEach(r => {
        html += '<div class="r-entry">';
        html += '<div class="r-row"><strong>' + esc(r.title) + '</strong><span>' + esc(r.dates) + '</span></div>';
        html += '<div class="r-row sub"><span class="r-italic">' + esc(r.company) + '</span><span class="r-italic">' + esc(r.location) + '</span></div>';
        if (r.bullets) html += '<ul class="r-bullets">' + bulletsFromTextarea(r.bullets) + '</ul>';
        html += '</div>';
      });
      html += '</div>';
    }

    // Projects
    const projRows = Array.from(document.querySelectorAll('.proj-row')).map(row => ({
      name: val('.proj-name', row), stack: val('.proj-stack', row),
      date: val('.proj-date', row), link: val('.proj-link', row),
      live: val('.proj-live', row), bullets: val('.proj-bullets', row)
    })).filter(r => r.name);

    if (projRows.length) {
      html += '<div class="r-section"><h3>Projects</h3>';
      projRows.forEach(r => {
        let nameLine = '<strong>' + esc(r.name) + '</strong>';
        if (r.stack) nameLine += ' <span class="r-italic">| ' + esc(r.stack) + '</span>';
        html += '<div class="r-entry">';
        html += '<div class="r-row"><span>' + nameLine + '</span><span>' + esc(r.date) + '</span></div>';
        const linkBits = [];
        if (r.link) {
          const label = /github\.com/i.test(r.link) ? 'GitHub' : 'Repo';
          linkBits.push('<strong>' + label + ':</strong> ' + linkifyAs(r.link, ghPath(r.link)));
        }
        if (r.live) linkBits.push(linkifyAs(r.live, 'Live'));
        if (linkBits.length) html += '<div class="r-row sub"><span class="r-italic">' + linkBits.join(' <span class="sep">|</span> ') + '</span><span></span></div>';
        if (r.bullets) html += '<ul class="r-bullets">' + bulletsFromTextarea(r.bullets) + '</ul>';
        html += '</div>';
      });
      html += '</div>';
    }

    // Skills
    const skillRows = Array.from(document.querySelectorAll('.skill-row')).map(row => ({
      category: val('.skill-category', row), list: val('.skill-list', row)
    })).filter(r => r.category && r.list);

    if (skillRows.length) {
      html += '<div class="r-section"><h3>Technical Skills</h3>';
      skillRows.forEach(r => {
        html += '<div class="r-skill-line"><strong>' + esc(r.category) + ':</strong> ' + esc(r.list) + '</div>';
      });
      html += '</div>';
    }

    // Leadership / Position of Responsibility
    const leadRows = Array.from(document.querySelectorAll('.leadership-row')).map(row => ({
      role: val('.lead-role', row), org: val('.lead-org', row),
      dates: val('.lead-dates', row), bullets: val('.lead-bullets', row)
    })).filter(r => r.role || r.org);

    if (leadRows.length) {
      html += '<div class="r-section"><h3>Leadership / Position of Responsibility</h3>';
      leadRows.forEach(r => {
        html += '<div class="r-entry">';
        html += '<div class="r-row"><strong>' + esc(r.role) + '</strong><span>' + esc(r.dates) + '</span></div>';
        html += '<div class="r-row sub"><span class="r-italic">' + esc(r.org) + '</span><span></span></div>';
        if (r.bullets) html += '<ul class="r-bullets">' + bulletsFromTextarea(r.bullets) + '</ul>';
        html += '</div>';
      });
      html += '</div>';
    }

    // Coding profiles
    const codingRows = Array.from(document.querySelectorAll('.coding-row')).map(row => ({
      platform: val('.coding-platform', row), link: val('.coding-link', row), stat: val('.coding-stat', row)
    })).filter(r => r.platform);

    if (codingRows.length) {
      html += '<div class="r-section"><h3>Coding Profiles</h3>';
      codingRows.forEach(r => {
        const name = linkifyAs(r.link, r.platform);
        html += '<div class="r-skill-line"><strong>' + name + '</strong>' + (r.stat ? ' — ' + esc(r.stat) : '') + '</div>';
      });
      html += '</div>';
    }

    // Extras
    const certifications = val('.f-certifications');
    const achievements = val('.f-achievements');
    if (certifications || achievements) {
      html += '<div class="r-section"><h3>Certifications &amp; Achievements</h3><ul class="r-bullets">';
      if (certifications) html += bulletsFromTextarea(certifications);
      if (achievements) html += bulletsFromTextarea(achievements);
      html += '</ul></div>';
    }

    // Interests
    const interests = val('.f-interests');
    if (interests) {
      html += '<div class="r-section"><h3>Interests</h3><div class="r-skill-line">' + esc(interests) + '</div></div>';
    }

    // Custom sections
    const customRows = Array.from(document.querySelectorAll('.custom-row')).map(row => ({
      heading: val('.custom-heading', row), content: val('.custom-content', row)
    })).filter(r => r.heading);

    customRows.forEach(r => {
      html += '<div class="r-section"><h3>' + esc(r.heading) + '</h3>';
      if (r.content) html += '<ul class="r-bullets">' + bulletsFromTextarea(r.content) + '</ul>';
      html += '</div>';
    });

    html += '</div>';
    previewMount.innerHTML = html;
  }

  // ---------------------------------------------------------------------
  // Collect raw form data into the shape the backend's ResumeData schema
  // expects. This is the ONLY thing that gets sent to the server — the
  // server re-renders the final PDF from this, it never trusts anything
  // else the browser might claim later.
  // ---------------------------------------------------------------------
  function collectResumeData(){
    const rows = (rowSelector, mapper) =>
      Array.from(document.querySelectorAll(rowSelector)).map(row => mapper(row)).filter(Boolean);

    return {
      contact: {
        fullName: val('.f-fullName'),
        email: val('.f-email'),
        phone: val('.f-phone') || null,
        location: val('.f-location') || null,
        linkedin: val('.f-linkedin') || null,
        github: val('.f-github') || null,
        portfolio: val('.f-portfolio') || null,
      },
      summary: val('.f-summary') || null,
      education: rows('.edu-row', row => {
        const school = val('.edu-school', row), degree = val('.edu-degree', row);
        if (!school && !degree) return null;
        return {
          school, degree,
          location: val('.edu-location', row),
          gpa: val('.edu-gpa', row),
          start: val('.edu-start', row),
          end: val('.edu-end', row),
        };
      }),
      experience: rows('.exp-row', row => {
        const title = val('.exp-title', row), company = val('.exp-company', row);
        if (!title && !company) return null;
        return {
          title, company,
          location: val('.exp-location', row),
          dates: val('.exp-dates', row),
          bullets: val('.exp-bullets', row),
        };
      }),
      projects: rows('.proj-row', row => {
        const name = val('.proj-name', row);
        if (!name) return null;
        return {
          name,
          stack: val('.proj-stack', row),
          date: val('.proj-date', row),
          link: val('.proj-link', row),
          live: val('.proj-live', row),
          bullets: val('.proj-bullets', row),
        };
      }),
      skills: rows('.skill-row', row => {
        const category = val('.skill-category', row), list = val('.skill-list', row);
        if (!category || !list) return null;
        return { category, list };
      }),
      leadership: rows('.leadership-row', row => {
        const role = val('.lead-role', row), org = val('.lead-org', row);
        if (!role && !org) return null;
        return {
          role, org,
          dates: val('.lead-dates', row),
          bullets: val('.lead-bullets', row),
        };
      }),
      coding_profiles: rows('.coding-row', row => {
        const platform = val('.coding-platform', row);
        if (!platform) return null;
        return {
          platform,
          link: val('.coding-link', row),
          stat: val('.coding-stat', row),
        };
      }),
      interests: val('.f-interests') || null,
      certifications: val('.f-certifications') || null,
      achievements: val('.f-achievements') || null,
      custom_sections: rows('.custom-row', row => {
        const heading = val('.custom-heading', row);
        if (!heading) return null;
        return { heading, content: val('.custom-content', row) };
      }),
    };
  }

  // ---- Payment overlay helpers ----
  function showOverlay(text){
    paymentStatusText.textContent = text;
    paymentOverlay.hidden = false;
  }
  function hideOverlay(){
    paymentOverlay.hidden = true;
  }

  // ---- Poll order status until it's COMPLETED or FAILED ----
  function pollOrderStatus(orderId, { intervalMs = 2000, timeoutMs = 600000 } = {}){
    const startedAt = Date.now();

    return new Promise((resolve, reject) => {
      const tick = async () => {
        if (Date.now() - startedAt > timeoutMs) {
          reject(new Error('timeout'));
          return;
        }
        try {
          const res = await fetch(`${API_BASE}/api/order/${orderId}/status`);
          if (!res.ok) throw new Error('status check failed');
          const data = await res.json();

          if (data.status === 'completed') {
            resolve(data);
            return;
          }
          if (data.status === 'failed') {
            reject(new Error('payment_failed'));
            return;
          }
          setTimeout(tick, intervalMs);
        } catch (err) {
          setTimeout(tick, intervalMs);
        }
      };
      tick();
    });
  }

  // ---- Kick off the whole pay -> generate -> email flow ----
  async function startCheckout(){
    if (!document.getElementById('resumePaper')) {
      alert('Add some resume content before downloading.');
      goToStep(0);
      return;
    }

    const email = val('.f-email');
    const fullName = val('.f-fullName');
    if (!email) {
      alert('Please add your email on the Contact step — that\'s where we\'ll send your finished resume.');
      goToStep(0);
      return;
    }
    if (!fullName) {
      alert('Please add your name on the Contact step.');
      goToStep(0);
      return;
    }

    showOverlay('Preparing your order…');

    let order;
    try {
      const res = await fetch(`${API_BASE}/api/create-order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_email: email,
          resume_data: collectResumeData(),
          amount_paise: AMOUNT_PAISE,
          currency: CURRENCY,
        }),
      });
      if (!res.ok) throw new Error('create-order failed');
      order = await res.json();
    } catch (err) {
      hideOverlay();
      alert('Could not start checkout. Please try again in a moment.');
      return;
    }

    showOverlay('Opening payment window…');

    const rzp = new Razorpay({
      key: order.razorpay_key_id,
      order_id: order.razorpay_order_id,
      amount: order.amount_paise,
      currency: order.currency,
      name: 'ResumeDraft',
      description: 'Resume PDF download',
      prefill: { name: fullName, email },
      handler: function(){
        // Razorpay confirms success here, but this is a UI signal only —
        // the actual order status flips to "paid" via the server-side
        // webhook, independently of anything this callback says.
        showOverlay('Payment received. Generating your resume…');
        pollOrderStatus(order.order_id)
          .then(() => {
            showOverlay('Done! Your resume has been emailed to you.');
            setTimeout(hideOverlay, 4000);
          })
          .catch(() => {
            showOverlay('Payment went through, but generation is taking longer than expected. We\'ll email it as soon as it\'s ready.');
            setTimeout(hideOverlay, 6000);
          });
      },
      modal: {
        ondismiss: function(){
          hideOverlay();
        },
      },
      theme: { color: '#C76E37' },
    });

    rzp.on('payment.failed', function(){
      hideOverlay();
      alert('Payment failed or was cancelled. You can try again whenever you\'re ready.');
    });

    rzp.open();
  }

  document.getElementById('downloadTop').addEventListener('click', startCheckout);
  document.getElementById('downloadBottom').addEventListener('click', startCheckout);

  document.getElementById('resetBtn').addEventListener('click', () => {
    if (confirm('Clear everything and start over?')) location.reload();
  });

  // init
  renderPreview();
  goToStep(0);
})();

