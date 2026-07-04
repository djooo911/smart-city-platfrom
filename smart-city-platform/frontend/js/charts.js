/*
  Chart.js wrapper for the per-lamp brightness/ambient-light history line
  chart, fed by GET /lamps/{id}/history. `Chart` is the Chart.js global
  loaded via <script> in index.html before this module.
*/

let chart = null;

export function renderHistoryChart(canvasEl, readings) {
  const chronological = [...readings].reverse(); // API returns most-recent-first
  const labels = chronological.map((r) => new Date(r.timestamp).toLocaleTimeString());
  const brightness = chronological.map((r) => r.led_brightness_pct);
  const ambientLight = chronological.map((r) => r.ambient_light_pct);

  if (chart) {
    chart.destroy();
  }

  chart = new Chart(canvasEl, {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "Luminosité LED (%)", data: brightness, borderColor: "#38bdf8", tension: 0.2 },
        { label: "Lumière ambiante (%)", data: ambientLight, borderColor: "#fbbf24", tension: 0.2 },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: { ticks: { color: "#94a3b8" } },
        y: { ticks: { color: "#94a3b8" }, min: 0, max: 100 },
      },
      plugins: {
        legend: { labels: { color: "#e2e8f0" } },
      },
    },
  });
}
