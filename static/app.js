const MAX_ALLOWED_AMOUNT = 999999999999;

function logResponse(data, statusCode = 200, isOk = true) {
    const consoleEl = document.getElementById('jsonConsole');
    const statusEl = document.getElementById('responseStatus');

    consoleEl.textContent = typeof data === 'object' ? JSON.stringify(data, null, 2) : data;
    statusEl.textContent = `HTTP ${statusCode}`;

    statusEl.className = `text-xs font-mono px-2 py-0.5 rounded ${
        isOk ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'
    }`;
}

function updateWalletCard(wallet) {
    document.getElementById('walletCard').classList.remove('hidden');
    document.getElementById('activeWalletBadge').classList.remove('hidden');

    document.getElementById('cardBalance').textContent = wallet.balance;
    document.getElementById('cardCurrency').textContent = wallet.currency;
    document.getElementById('cardWalletId').textContent = wallet.id;
    document.getElementById('cardUserId').textContent = wallet.user_id;
    document.getElementById('currentWalletId').textContent = wallet.id;

    document.getElementById('actionWalletId').value = wallet.id;
}

async function sendApiRequest(url, method = 'GET', body = null, extraHeaders = {}) {
    try {
        const options = {
            method,
            headers: {...extraHeaders}
        };

        if (body) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }

        const response = await fetch(url, options);
        const data = await response.json();

        logResponse(data, response.status, response.ok);
        return {ok: response.ok, data};
    } catch (err) {
        logResponse({error: 'Сетевая ошибка или сервер недоступен', details: String(err)}, 500, false);
        return {ok: false};
    }
}

async function createWallet() {
    const userId = Number(document.getElementById('createUserId').value);
    const currency = document.getElementById('createCurrency').value.trim() || 'RUB';

    if (!userId || userId < 1) return alert('Укажите корректный User ID (>= 1)');

    const result = await sendApiRequest(`/wallets/?user_id=${userId}`, 'POST', {currency});
    if (result.ok) {
        updateWalletCard(result.data);
    }
}

async function getWallet() {
    const walletId = Number(document.getElementById('actionWalletId').value);
    if (!walletId || walletId < 1) return alert('Укажите корректный Wallet ID (>= 1)');

    const result = await sendApiRequest(`/wallets/${walletId}`);
    if (result.ok) {
        updateWalletCard(result.data);
        loadTransactions();
    }
}

async function deposit() {
    const walletId = Number(document.getElementById('actionWalletId').value);
    const amount = Number(document.getElementById('actionAmount').value);

    if (!walletId || walletId < 1) return alert('Укажите корректный Wallet ID (>= 1)');
    if (!amount || amount <= 0) return alert('Укажите сумму больше 0');
    if (amount > MAX_ALLOWED_AMOUNT) return alert('Слишком большая сумма');

    const idempotencyKey = crypto.randomUUID();

    const result = await sendApiRequest(
        `/wallets/${walletId}/deposit?amount=${amount}`,
        'POST',
        null,
        {'X-Idempotency-Key': idempotencyKey}
    );

    if (result.ok) {
        getWallet();
    }
}

async function withdraw() {
    const walletId = Number(document.getElementById('actionWalletId').value);
    const amount = Number(document.getElementById('actionAmount').value);

    if (!walletId || walletId < 1) return alert('Укажите корректный Wallet ID (>= 1)');
    if (!amount || amount <= 0) return alert('Укажите сумму больше 0');
    if (amount > MAX_ALLOWED_AMOUNT) return alert('Слишком большая сумма');

    const result = await sendApiRequest(`/wallets/${walletId}/withdraw?amount=${amount}`, 'POST');
    if (result.ok) {
        getWallet();
    }
}

async function transfer() {
    const fromId = Number(document.getElementById('transferFrom').value);
    const toId = Number(document.getElementById('transferTo').value);
    const amount = Number(document.getElementById('transferAmount').value);

    if (!fromId || fromId < 1) return alert('Укажите корректный Wallet ID отправителя');
    if (!toId || toId < 1) return alert('Укажите корректный Wallet ID получателя');
    if (fromId === toId) return alert('Нельзя перевести деньги самому себе на тот же кошелек');
    if (!amount || amount <= 0) return alert('Укажите сумму больше 0');
    if (amount > MAX_ALLOWED_AMOUNT) return alert('Слишком большая сумма');

    const url = `/wallets/transfer?from_wallet_id=${fromId}&to_wallet_id=${toId}&amount=${amount}`;
    const result = await sendApiRequest(url, 'POST');

    if (result.ok) {
        document.getElementById('actionWalletId').value = fromId;
        getWallet();
    }
}

async function loadTransactions() {
    const walletId = Number(document.getElementById('actionWalletId').value);
    if (!walletId || walletId < 1) return;

    const result = await sendApiRequest(`/wallets/${walletId}/transactions`);
    const tbody = document.getElementById('txTableBody');
    tbody.innerHTML = '';

    if (result.ok && Array.isArray(result.data)) {
        if (result.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="py-4 text-center text-slate-500">Транзакций пока нет</td></tr>';
            return;
        }

        result.data.forEach(tx => {
            const formattedDate = new Date(tx.created_at).toLocaleString('ru-RU');
            const isDeposit = tx.transaction_type.toLowerCase().includes('deposit');
            const badgeStyle = isDeposit
                ? 'text-emerald-400 bg-emerald-950/50 border-emerald-800'
                : 'text-amber-400 bg-amber-950/50 border-amber-800';

            tbody.innerHTML += `
        <tr class="hover:bg-slate-800/40 transition">
          <td class="py-2.5 px-3 font-mono text-slate-400">#${tx.id}</td>
          <td class="py-2.5 px-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-semibold border ${badgeStyle}">
              ${tx.transaction_type}
            </span>
          </td>
          <td class="py-2.5 px-3 font-semibold ${isDeposit ? 'text-emerald-400' : 'text-slate-200'}">
            ${isDeposit ? '+' : '-'}${tx.amount}
          </td>
          <td class="py-2.5 px-3 font-mono text-slate-400">${tx.status}</td>
          <td class="py-2.5 px-3 text-slate-500 text-[11px]">${formattedDate}</td>
        </tr>
      `;
        });
    }
}