/*
  Blockchain explorer: paginated block table, block detail view, and a
  "Verify Chain" button. Self-contained module -- dashboard.js just calls
  initBlockchainTab() once and refreshBlockchainTab() on each poll tick.
*/

import { listBlocks, verifyChain } from "./api.js";

const PAGE_SIZE = 20;
let currentPage = 1;
let initialized = false;

function truncateHash(hash) {
  return `${hash.slice(0, 10)}…${hash.slice(-6)}`;
}

async function loadBlocksPage(page) {
  const tbody = document.querySelector("#blocks-table tbody");
  const pageLabel = document.getElementById("blocks-page-label");

  try {
    const response = await listBlocks(page, PAGE_SIZE);
    currentPage = response.meta.page;

    tbody.innerHTML = "";
    for (const block of response.data) {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${block.index}</td>
        <td>${new Date(block.timestamp).toLocaleString()}</td>
        <td>${block.data?.event_type ?? "-"}</td>
        <td title="${block.hash}">${truncateHash(block.hash)}</td>
      `;
      row.addEventListener("click", () => showBlockDetail(block));
      tbody.appendChild(row);
    }

    pageLabel.textContent = `Page ${currentPage} (${response.meta.total_blocks} blocs)`;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4">Erreur: ${err.message}</td></tr>`;
  }
}

function showBlockDetail(block) {
  const detail = document.getElementById("block-detail");
  detail.hidden = false;
  detail.textContent = JSON.stringify(block, null, 2);
}

async function handleVerifyChain() {
  const resultEl = document.getElementById("verify-chain-result");
  resultEl.textContent = "Vérification...";
  resultEl.style.color = "";

  try {
    const response = await verifyChain();
    const { valid, broken_at_index } = response.data;
    resultEl.textContent = valid
      ? "✅ Chaîne valide"
      : `❌ Chaîne corrompue au bloc #${broken_at_index}`;
    resultEl.style.color = valid ? "#4ade80" : "#f87171";
  } catch (err) {
    resultEl.textContent = `Erreur: ${err.message}`;
    resultEl.style.color = "#f87171";
  }
}

export function initBlockchainTab() {
  if (initialized) {
    loadBlocksPage(currentPage);
    return;
  }
  initialized = true;

  document.getElementById("verify-chain-button").addEventListener("click", handleVerifyChain);
  document.getElementById("blocks-prev-page").addEventListener("click", () => {
    if (currentPage > 1) loadBlocksPage(currentPage - 1);
  });
  document.getElementById("blocks-next-page").addEventListener("click", () => {
    loadBlocksPage(currentPage + 1);
  });

  loadBlocksPage(1);
}

export function refreshBlockchainTab() {
  loadBlocksPage(currentPage);
}
