function parseCSV(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const lines = reader.result.trim().split(/\r?\n/);
            const data = lines.map(line => {
                const [account, amount] = line.split(/[;,]/).map(s => s.trim());
                return { account, amount: parseFloat(amount) || 0 };
            });
            resolve(data);
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsText(file);
    });
}

function sumAmounts(data) {
    return data.reduce((sum, row) => sum + row.amount, 0);
}

function sumByPrefix(data, prefix) {
    return data.filter(row => row.account.startsWith(prefix))
               .reduce((sum, row) => sum + row.amount, 0);
}

function addSpv() {
    const container = document.getElementById('spv-container');
    const idx = container.children.length + 1;
    const div = document.createElement('div');
    div.className = 'spv';
    div.innerHTML = `
        <h3>SPV ${idx}</h3>
        <label>Nom: <input type="text" class="spv-name"></label>
        <label>Balance (CSV): <input type="file" class="spv-file" accept=".csv"></label>
        <label>Valeur réévaluée de l'actif: <input type="number" class="spv-asset" step="0.01"></label>
        <label>Pourcentage de détention (%): <input type="number" class="spv-percent" step="0.01"></label>
        <label>Taux d'IS (%): <input type="number" class="spv-tax" step="0.01" value="25"></label>
        <label><input type="checkbox" class="spv-sccv"> SPV de type SCCV (exonéré d'IS)</label>
    `;
    container.appendChild(div);
}

document.getElementById('add-spv').addEventListener('click', addSpv);

document.addEventListener('DOMContentLoaded', () => {
    addSpv();
});

function displayResults(fundNav, navPerShare, spvResults) {
    let out = `VL du fonds: ${fundNav.toFixed(2)}\n`;
    out += `VL par part: ${navPerShare.toFixed(4)}\n`;
    spvResults.forEach(r => {
        out += `\n${r.name}: VL ${r.nav.toFixed(2)}, Provision IS ${r.tax.toFixed(2)}`;
    });
    document.getElementById('output').textContent = out;
}

function alertMissingFund() {
    alert('Veuillez importer la balance du fonds et renseigner le nombre de parts.');
}

async function calculate() {
    const fundFile = document.getElementById('fund-file').files[0];
    const fundShares = parseFloat(document.getElementById('fund-shares').value);
    if (!fundFile || !fundShares) {
        alertMissingFund();
        return;
    }
    const fundData = await parseCSV(fundFile);
    const fundTotal = sumAmounts(fundData);
    const fundBookSpv = sumByPrefix(fundData, '2');
    let fundNav = fundTotal - fundBookSpv;

    const spvDivs = document.querySelectorAll('#spv-container .spv');
    const spvResults = [];
    for (const div of spvDivs) {
        const name = div.querySelector('.spv-name').value || 'SPV';
        const file = div.querySelector('.spv-file').files[0];
        const assetVal = parseFloat(div.querySelector('.spv-asset').value) || 0;
        const percent = parseFloat(div.querySelector('.spv-percent').value) || 0;
        const taxRate = (parseFloat(div.querySelector('.spv-tax').value) || 0) / 100;
        const isSccv = div.querySelector('.spv-sccv').checked;
        if (!file) continue;
        const data = await parseCSV(file);
        const total = sumAmounts(data);
        const bookStock = sumByPrefix(data, '3');
        const baseWithoutStock = total - bookStock;
        const latentGain = assetVal - bookStock;
        const tax = isSccv ? 0 : latentGain * taxRate;
        const spvNav = baseWithoutStock + assetVal - tax;
        fundNav += spvNav * (percent / 100);
        spvResults.push({ name, nav: spvNav, tax });
    }

    const navPerShare = fundNav / fundShares;
    displayResults(fundNav, navPerShare, spvResults);
}

document.getElementById('calculate').addEventListener('click', calculate);
