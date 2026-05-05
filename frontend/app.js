const API_AUTH = '/api/v1/auth';
const API_BASE = '/api/v1/trade-licenses';

// ─── STATE ───
let token = localStorage.getItem('token');
let currentUser = {
    id: localStorage.getItem('userId'),
    name: localStorage.getItem('userName'),
    role: localStorage.getItem('userRole')
};
let currentRole = currentUser.role ? currentUser.role.toLowerCase() : 'applicant';
let selectedAppId = null;

// ─── AUTH DOM ───
const authOverlay    = document.getElementById('auth-overlay');
const mainApp        = document.getElementById('main-app');
const authTabs       = document.querySelectorAll('.auth-tab');
const authForms      = document.querySelectorAll('.auth-form');
const loginForm      = document.getElementById('login-form');
const registerForm   = document.getElementById('register-form');
const logoutBtn      = document.getElementById('logout-btn');

// ─── APP DOM ───
const navBtns        = document.querySelectorAll('.nav-tab');
const views          = document.querySelectorAll('.view-section');
const viewTitle      = document.getElementById('view-title');
const roleText       = document.getElementById('current-role');
const currentUserName = document.getElementById('current-user-name');
const userAvatar     = document.getElementById('user-avatar');
const submitForm     = document.getElementById('submit-form');
const myAppsTable    = document.querySelector('#my-apps-table tbody');
const reviewerTable  = document.querySelector('#reviewer-table tbody');
const approverTable  = document.querySelector('#approver-table tbody');

// ─── NOTIFICATION DOM ───
const notifBell  = document.getElementById('notification-bell');
const notifPanel = document.getElementById('notification-panel');
const notifList  = document.getElementById('notif-list');
const notifCount = document.getElementById('notif-count');

// ─── MODAL DOM ───
const modal       = document.getElementById('details-modal');
const closeModal  = document.getElementById('close-modal');
const modalBody   = document.getElementById('modal-body');
const modalActions = document.getElementById('modal-actions');

// ══════════════════════════════════════════
// AUTH LOGIC
// ══════════════════════════════════════════

function checkAuth() {
    if (token) {
        authOverlay.style.display = 'none';
        mainApp.style.display = 'flex';
        setupUserEnvironment();
        refreshData();
        startNotificationPolling();
    } else {
        authOverlay.style.display = 'flex';
        mainApp.style.display = 'none';

        // Reset login button in case it was left in loading state
        const loginBtn = loginForm.querySelector('button[type="submit"]');
        if (loginBtn) { loginBtn.textContent = 'Sign In →'; loginBtn.disabled = false; }

        // Reset register button too
        const regBtn = registerForm.querySelector('button[type="submit"]');
        if (regBtn) { regBtn.textContent = 'Create Account →'; regBtn.disabled = false; }
    }
}

function setupUserEnvironment() {
    const name = currentUser.name || 'User';
    currentUserName.textContent = name;
    if (userAvatar) userAvatar.textContent = name[0].toUpperCase();
    if (roleText) roleText.textContent = currentUser.role || '';

    const appBtn   = document.getElementById('nav-applicant');
    const revBtn   = document.getElementById('nav-reviewer');
    const aprvBtn  = document.getElementById('nav-approver');

    [appBtn, revBtn, aprvBtn].forEach(b => { if(b) b.style.display = 'none'; });

    if (currentUser.role === 'Applicant' && appBtn)  appBtn.style.display  = 'flex';
    if (currentUser.role === 'Reviewer'  && revBtn)  revBtn.style.display  = 'flex';
    if (currentUser.role === 'Approver'  && aprvBtn) aprvBtn.style.display = 'flex';

    if (currentUser.role === 'Applicant' && currentRole !== 'applicant') appBtn && appBtn.click();
    else if (currentUser.role === 'Reviewer'  && currentRole !== 'reviewer')  revBtn  && revBtn.click();
    else if (currentUser.role === 'Approver'  && currentRole !== 'approver')  aprvBtn && aprvBtn.click();
}

// Auth Tab Switching
authTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        authTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        authForms.forEach(f => f.classList.remove('active'));
        document.getElementById(`${tab.dataset.auth}-form`).classList.add('active');
    });
});

// Login
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = loginForm.querySelector('button[type="submit"]');
    btn.textContent = 'Signing in...';
    btn.disabled = true;

    const email    = document.getElementById('login_email').value;
    const password = document.getElementById('login_password').value;
    const role     = document.getElementById('login_role').value;

    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
        const res = await fetch(`${API_AUTH}/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (res.ok) {
            const data = await res.json();
            token = data.access_token;
            const payload = JSON.parse(atob(token.split('.')[1]));

            if (payload.role !== role) {
                showToast(`❌ You are not registered as ${role}.`, 'danger');
                btn.textContent = 'Sign In →';
                btn.disabled = false;
                return;
            }

            currentUser = {
                id: payload.sub,
                email: payload.email,
                role: payload.role,
                name: payload.email.split('@')[0]
            };

            localStorage.setItem('token', token);
            localStorage.setItem('userId', currentUser.id);
            localStorage.setItem('userName', currentUser.name);
            localStorage.setItem('userRole', currentUser.role);

            checkAuth();
        } else {
            const err = await res.json();
            showToast(`❌ ${err.detail || 'Login failed'}`, 'danger');
            btn.textContent = 'Sign In →';
            btn.disabled = false;
        }
    } catch (err) {
        console.error(err);
        btn.textContent = 'Sign In →';
        btn.disabled = false;
    }
});

// Register
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = registerForm.querySelector('button[type="submit"]');
    const password = document.getElementById('reg_password').value;
    const passwordConfirm = document.getElementById('reg_password_confirm').value;

    if (password !== passwordConfirm) {
        showToast('❌ Passwords do not match!', 'danger');
        return;
    }

    btn.textContent = 'Creating account...';
    btn.disabled = true;

    const payload = {
        name: document.getElementById('reg_name').value,
        phone: document.getElementById('reg_phone').value,
        email: document.getElementById('reg_email').value,
        password,
        role: document.getElementById('reg_role').value
    };

    try {
        const res = await fetch(`${API_AUTH}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast('✅ Registration successful! Please sign in.', 'success');
            authTabs[0].click();
        } else {
            const err = await res.json();
            showToast(`❌ ${err.detail || 'Registration failed'}`, 'danger');
        }
    } catch (err) { console.error(err); }

    btn.textContent = 'Create Account →';
    btn.disabled = false;
});

// Logout
logoutBtn.addEventListener('click', () => {
    localStorage.clear();
    token = null;
    currentUser = {};
    checkAuth();
});

// ══════════════════════════════════════════
// APP LOGIC
// ══════════════════════════════════════════

function getAuthHeaders() {
    return { 'Authorization': `Bearer ${token}` };
}

async function uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData
    });
    if (!res.ok) throw new Error('File upload failed');
    return await res.json();
}

// Navigation
navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        navBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const view = btn.dataset.view;
        currentRole = view;

        views.forEach(v => v.classList.remove('active'));
        document.getElementById(`${view}-view`).classList.add('active');

        if (roleText) roleText.textContent = currentUser.role || '';
        if (view === 'applicant') viewTitle.textContent = 'Application Portal';
        if (view === 'reviewer')  viewTitle.textContent = 'Review Dashboard';
        if (view === 'approver')  viewTitle.textContent = 'Approval Dashboard';

        refreshData();
    });
});

// Submit Application
submitForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = submitForm.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '⏳ Uploading files...';
    btn.disabled = true;

    try {
        const photoFile = document.getElementById('doc_photo').files[0];
        const idFile    = document.getElementById('doc_id').files[0];
        const leaseFile = document.getElementById('doc_lease').files[0];

        const [photoDoc, idDoc, leaseDoc] = await Promise.all([
            uploadDocument(photoFile),
            uploadDocument(idFile),
            uploadDocument(leaseFile)
        ]);

        const payload = {
            applicant_id: currentUser.id,
            business_details: {
                name: document.getElementById('biz_name').value,
                type: document.getElementById('biz_type').value,
                address: document.getElementById('biz_address').value,
                capital: parseFloat(document.getElementById('biz_capital').value),
                activity_description: document.getElementById('biz_desc').value
            },
            documents: [
                { file_name: 'Applicant Photo', storage_uri: photoDoc.storage_uri },
                { file_name: idDoc.file_name,   storage_uri: idDoc.storage_uri },
                { file_name: leaseDoc.file_name, storage_uri: leaseDoc.storage_uri }
            ],
            payment_transaction_id: `${document.getElementById('payment_method').value}-${document.getElementById('payment_txn_id').value}`,
            payment_amount: parseFloat(document.getElementById('payment_amount').value)
        };

        const res = await fetch(API_BASE, {
            method: 'POST',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            submitForm.reset();
            document.getElementById('biz_capital').value = '10000';
            document.getElementById('payment_amount').value = '500';
            btn.innerHTML = '✅ Submitted!';
            showToast('✅ Application submitted successfully!', 'success');
            setTimeout(() => { btn.innerHTML = originalText; btn.disabled = false; }, 2500);
            refreshData();
        } else {
            const err = await res.json();
            showToast(`❌ ${err.detail || 'Submission failed'}`, 'danger');
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    } catch (err) {
        console.error(err);
        showToast('❌ Submission failed. Check your connection.', 'danger');
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
});

// ══════════════════════════════════════════
// DATA RENDERING
// ══════════════════════════════════════════

async function refreshData() {
    if (!token) return;
    try {
        let url = API_BASE;
        if (currentRole === 'applicant') url += `?applicant_id=${currentUser.id}`;

        const res = await fetch(url, { headers: getAuthHeaders() });
        const data = await res.json();

        if (currentRole === 'applicant') renderApplicantTable(data);
        if (currentRole === 'reviewer')  renderReviewerTable(data);
        if (currentRole === 'approver')  renderApproverTable(data);
    } catch (err) { console.error(err); }
}

function getBadge(status) {
    return `<span class="badge ${status}">${status}</span>`;
}

function actionBtn(label, onclick, variant = 'primary') {
    return `<button class="btn btn-${variant}" style="padding:6px 14px;font-size:0.8rem;" onclick="${onclick}">${label}</button>`;
}

function renderApplicantTable(data) {
    if (!data.length) {
        myAppsTable.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--text-muted);padding:30px;">No applications yet. Submit your first one!</td></tr>`;
        return;
    }
    myAppsTable.innerHTML = data.map(app => `
        <tr>
            <td style="font-family:monospace;font-size:0.8rem;">…${app.id.slice(-8)}</td>
            <td>${app.business_type || '—'}</td>
            <td>${getBadge(app.status)}</td>
            <td>${actionBtn('View', `viewDetails('${app.id}')`)}</td>
        </tr>
    `).join('');
}

function renderReviewerTable(data) {
    const list = data.filter(a => ['Pending', 'Rereview'].includes(a.status));
    if (!list.length) {
        reviewerTable.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:30px;">Queue is empty. All caught up! ✅</td></tr>`;
        return;
    }
    reviewerTable.innerHTML = list.map(app => {
        const txnRaw  = app.payment_transaction_id || '';
        const txnParts = txnRaw.split('-');
        const payMethod = txnParts.length > 1 ? txnParts[0] : '—';
        const payTxnId  = txnParts.length > 1 ? txnParts.slice(1).join('-') : txnRaw;
        return `
        <tr>
            <td style="font-family:monospace;font-size:0.8rem;">…${app.id.slice(-8)}</td>
            <td style="font-family:monospace;font-size:0.8rem;">…${app.applicant_id.slice(-8)}</td>
            <td>${app.business_type}</td>
            <td><span style="color:var(--primary-light);font-weight:600;">📲 ${payMethod}</span></td>
            <td><code style="font-size:0.78rem;background:rgba(255,255,255,0.07);padding:2px 6px;border-radius:4px;">${payTxnId || '—'}</code></td>
            <td>${getBadge(app.status)}</td>
            <td>${actionBtn('Review', `viewDetails('${app.id}')`)}</td>
        </tr>`;
    }).join('');
}

function renderApproverTable(data) {
    const list = data.filter(a => ['Accepted', 'Approved', 'Rejected'].includes(a.status));
    if (!list.length) {
        approverTable.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:30px;">No applications to process yet.</td></tr>`;
        return;
    }
    approverTable.innerHTML = list.map(app => `
        <tr>
            <td style="font-family:monospace;font-size:0.8rem;">…${app.id.slice(-8)}</td>
            <td style="font-family:monospace;font-size:0.8rem;">…${app.applicant_id.slice(-8)}</td>
            <td>${app.business_type}</td>
            <td>${getBadge(app.status)}</td>
            <td>${actionBtn(app.status === 'Accepted' ? 'Decide' : 'View', `viewDetails('${app.id}')`)}</td>
        </tr>
    `).join('');
}

// ══════════════════════════════════════════
// MODAL
// ══════════════════════════════════════════

function detailRow(label, value) {
    return `<div class="detail-row"><strong>${label}</strong><span>${value}</span></div>`;
}

async function viewDetails(id) {
    selectedAppId = id;
    try {
        const res = await fetch(`${API_BASE}/${id}`, { headers: getAuthHeaders() });
        const app = await res.json();

        const docsHtml = app.attachments && app.attachments.length
            ? app.attachments.map(doc => `
                <a href="/${doc.storage_uri}" target="_blank" class="doc-link">
                    📄 ${doc.file_name} <span style="margin-left:auto;font-size:0.75rem;opacity:0.6;">Open ↗</span>
                </a>
            `).join('')
            : `<p style="color:var(--text-muted);font-size:0.85rem;">No documents uploaded.</p>`;

        // Parse payment method and transaction ID from combined string (e.g. "Telebirr-FT89234")
        const txnRaw = app.payment ? app.payment.transaction_id : '';
        const txnParts = txnRaw ? txnRaw.split('-') : [];
        const payMethod = txnParts.length > 1 ? txnParts[0] : '—';
        const payTxnId  = txnParts.length > 1 ? txnParts.slice(1).join('-') : txnRaw;

        // Reviewer info block (shown to approver)
        const reviewerBlock = app.reviewer_id ? `
            <div class="modal-divider"></div>
            <div style="font-size:0.78rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Reviewer Decision</div>
            ${detailRow('Reviewed By (ID)', `<code style="font-size:0.78rem;">…${app.reviewer_id.slice(-10)}</code>`)}
            ${app.review_note ? detailRow('Reviewer Note', app.review_note) : ''}
        ` : '';

        modalBody.innerHTML = `
            ${detailRow('Application ID', `<code style="font-size:0.78rem;">${app.id}</code>`)}
            ${detailRow('Status', getBadge(app.status))}
            <div class="modal-divider"></div>
            ${detailRow('Business Name', app.business_details.name)}
            ${detailRow('Business Type', app.business_details.type)}
            ${detailRow('Address', app.business_details.address)}
            ${detailRow('Capital', `$${app.business_details.capital.toLocaleString()}`)}
            ${detailRow('Activities', app.business_details.activity_description)}
            <div class="modal-divider"></div>
            <div style="font-size:0.78rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">💳 Payment Information</div>
            ${detailRow('Payment Method', `<span style="font-weight:600;color:var(--primary-light);">📲 ${payMethod}</span>`)}
            ${detailRow('Transaction ID', `<code style="font-size:0.82rem;background:rgba(255,255,255,0.07);padding:2px 8px;border-radius:5px;">${payTxnId || '—'}</code>`)}
            ${detailRow('Amount', `$${app.payment.amount} — ${app.payment.is_settled ? '✅ Settled' : '⏳ Pending'}`)}
            <div class="modal-divider"></div>
            <div style="margin-bottom:4px;font-size:0.78rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:.6px;">Documents</div>
            <div style="display:flex;flex-direction:column;gap:8px;">${docsHtml}</div>
            ${reviewerBlock}
            ${app.approval_note ? `<div class="modal-divider"></div>${detailRow('Approval Note', app.approval_note)}` : ''}
        `;


        modalActions.innerHTML = '';

        if (currentRole === 'reviewer' && ['Pending', 'Rereview'].includes(app.status)) {
            modalActions.innerHTML = `
                <div style="
                    width:100%;
                    background:rgba(99,102,241,0.08);
                    border:1px solid rgba(99,102,241,0.25);
                    border-radius:10px;
                    padding:12px 16px;
                    margin-bottom:12px;
                    display:flex;
                    align-items:center;
                    gap:12px;
                ">
                    <input type="checkbox" id="payment-verified-chk" onchange="toggleAcceptBtn()"
                        style="width:18px;height:18px;cursor:pointer;accent-color:var(--success);">
                    <label for="payment-verified-chk" style="cursor:pointer;font-size:0.88rem;font-weight:500;">
                        💳 I have verified the payment —
                        <strong style="color:var(--primary-light);">${payMethod}</strong>
                        / TXN: <code style="background:rgba(255,255,255,0.08);padding:1px 6px;border-radius:4px;">${payTxnId || '—'}</code>
                    </label>
                </div>
                <div style="display:flex;gap:8px;flex-wrap:wrap;">
                    ${actionBtn('Request Adjustment', "submitReview('Adjust')", 'warning')}
                    ${actionBtn('Reject', "submitReview('Reject')", 'danger')}
                    <button id="accept-btn" class="btn btn-success"
                        style="padding:6px 14px;font-size:0.8rem;opacity:0.4;cursor:not-allowed;"
                        onclick="submitReview('Accept')" disabled>
                        ✓ Accept (Paid)
                    </button>
                </div>
            `;
        } else if (currentRole === 'approver' && app.status === 'Accepted') {
            modalActions.innerHTML = `
                ${actionBtn('Re-review', "submitApproval('Rereview')", 'warning')}
                ${actionBtn('Reject', "submitApproval('Reject')", 'danger')}
                ${actionBtn('✓ Approve', "submitApproval('Approve')", 'success')}
            `;
        } else if (currentRole === 'applicant') {
            if (app.status === 'Pending') {
                modalActions.innerHTML = actionBtn('Cancel Application', 'cancelApplication()', 'danger');
            } else if (app.status === 'Approved') {
                modalActions.innerHTML = `
                    ${actionBtn('📄 Download License PDF', `downloadPdf('${app.id}')`, 'primary')}
                    ${actionBtn('🔄 Renew License', `renewApplication('${app.id}')`, 'success')}
                `;
            }
        }

        modal.classList.add('active');
    } catch (err) { console.error(err); }
}

closeModal.addEventListener('click', () => {
    modal.classList.remove('active');
    selectedAppId = null;
});

modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.classList.remove('active');
        selectedAppId = null;
    }
});

// ══════════════════════════════════════════
// ACTIONS
// ══════════════════════════════════════════

async function submitReview(action) {
    const note = prompt(`Note for "${action}" (optional):`, '');
    if (note === null) return;
    try {
        const res = await fetch(`${API_BASE}/${selectedAppId}/review`, {
            method: 'POST',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ reviewer_id: currentUser.id, action, note: note || undefined })
        });
        if (res.ok) {
            modal.classList.remove('active');
            showToast(`✅ Application ${action}ed`, 'success');
            refreshData();
        } else {
            const err = await res.json();
            showToast(`❌ ${err.detail}`, 'danger');
        }
    } catch (err) { console.error(err); }
}

async function submitApproval(action) {
    const note = prompt(`Note for "${action}" (optional):`, '');
    if (note === null) return;
    try {
        const res = await fetch(`${API_BASE}/${selectedAppId}/approval`, {
            method: 'POST',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ approver_id: currentUser.id, action, note: note || undefined })
        });
        if (res.ok) {
            modal.classList.remove('active');
            showToast(`✅ Application ${action}d`, 'success');
            refreshData();
        } else {
            const err = await res.json();
            showToast(`❌ ${err.detail}`, 'danger');
        }
    } catch (err) { console.error(err); }
}

async function cancelApplication() {
    if (!confirm('Are you sure you want to cancel this application?')) return;
    try {
        const res = await fetch(`${API_BASE}/${selectedAppId}?applicant_id=${currentUser.id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        if (res.ok || res.status === 204) {
            modal.classList.remove('active');
            showToast('Application cancelled.', 'warning');
            refreshData();
        } else {
            const err = await res.json();
            showToast(`❌ ${err.detail}`, 'danger');
        }
    } catch (err) { console.error(err); }
}

async function downloadPdf(id) {
    showToast('⏳ Generating PDF...', 'primary');
    const res = await fetch(`${API_BASE}/${id}/pdf`, { headers: getAuthHeaders() });
    if (res.ok) {
        const blob = await res.blob();
        const url  = window.URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href = url;
        a.download = `trade_license_${id.slice(-8)}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast('✅ PDF downloaded!', 'success');
    } else {
        showToast('❌ Failed to generate PDF', 'danger');
    }
}

async function renewApplication(id) {
    if (!confirm('Renew this license? A new application will be created for review.')) return;
    const bizName = prompt('Confirm / update business name:', 'Updated Business');
    if (!bizName) return;

    const payload = {
        applicant_id: currentUser.id,
        business_details: {
            name: bizName,
            type: 'Software',
            address: 'Updated Address',
            capital: 50000,
            activity_description: 'License renewal'
        },
        documents: [{ file_name: 'renewal.pdf', storage_uri: 's3://mock/renewal.pdf' }],
        payment_transaction_id: `renew-${Date.now()}`,
        payment_amount: 500
    };

    try {
        const res = await fetch(`${API_BASE}/${id}/renew`, {
            method: 'POST',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            showToast('✅ Renewal submitted!', 'success');
            modal.classList.remove('active');
            refreshData();
        } else {
            const err = await res.json();
            showToast(`❌ ${err.detail}`, 'danger');
        }
    } catch (err) { console.error(err); }
}

// ══════════════════════════════════════════
// NOTIFICATIONS
// ══════════════════════════════════════════

notifBell.addEventListener('click', () => {
    const isVisible = notifPanel.style.display === 'block';
    notifPanel.style.display = isVisible ? 'none' : 'block';
});

document.addEventListener('click', (e) => {
    if (!notifBell.contains(e.target) && !notifPanel.contains(e.target)) {
        notifPanel.style.display = 'none';
    }
});

async function refreshNotifications() {
    if (!token || !currentUser.id) return;
    try {
        const res = await fetch(`${API_BASE}/notifications?user_id=${currentUser.id}`, { headers: getAuthHeaders() });
        const data = await res.json();

        const unread = data.filter(n => !n.is_read);

        notifList.innerHTML = data.length
            ? data.map(n => `
                <div style="padding:10px 12px;background:rgba(0,0,0,0.3);border:1px solid ${n.is_read ? 'var(--border)' : 'rgba(99,102,241,0.35)'};border-radius:8px;margin-bottom:6px;">
                    <p style="font-size:0.85rem;">${n.message}</p>
                    <small style="color:var(--text-muted);font-size:0.75rem;">${new Date(n.created_at).toLocaleString()}</small>
                </div>
            `).join('')
            : `<p style="color:var(--text-muted);font-size:0.85rem;text-align:center;padding:16px;">No notifications yet.</p>`;

        notifCount.style.display = unread.length > 0 ? 'block' : 'none';
    } catch (err) { console.error(err); }
}

function startNotificationPolling() {
    refreshNotifications();
    setInterval(refreshNotifications, 30000);
}

// ══════════════════════════════════════════
// TOAST NOTIFICATIONS
// ══════════════════════════════════════════

function showToast(message, type = 'primary') {
    const colors = {
        success: 'var(--success)',
        danger: 'var(--danger)',
        warning: 'var(--warning)',
        primary: 'var(--primary-light)'
    };

    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: rgba(15,23,42,0.95);
        border: 1px solid ${colors[type] || colors.primary};
        color: white;
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: 500;
        z-index: 9999;
        max-width: 340px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        animation: fadeUp 0.3s ease;
        font-family: inherit;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

// ══════════════════════════════════════════
// PAYMENT VERIFICATION TOGGLE
// ══════════════════════════════════════════

function toggleAcceptBtn() {
    const chk = document.getElementById('payment-verified-chk');
    const btn = document.getElementById('accept-btn');
    if (!chk || !btn) return;
    if (chk.checked) {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.cursor = 'pointer';
    } else {
        btn.disabled = true;
        btn.style.opacity = '0.4';
        btn.style.cursor = 'not-allowed';
    }
}

// ══════════════════════════════════════════
// INIT
// ══════════════════════════════════════════

checkAuth();
