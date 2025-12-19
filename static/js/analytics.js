(function () {
  function hasData(arr) {
    return Array.isArray(arr) && arr.some(v => Number(v) > 0);
  }

  // -------------------------
  // Monthly Pie
  // -------------------------
  const pieCanvas = document.getElementById("monthlyPie");
  const pieEmpty = document.getElementById("monthlyPieEmpty");

  if (pieCanvas && monthlyCategoryData && hasData(monthlyCategoryData.values)) {
    pieEmpty.style.display = "none";
    new Chart(pieCanvas, {
      type: "pie",
      data: {
        labels: monthlyCategoryData.labels,
        datasets: [{
          data: monthlyCategoryData.values
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" }
        }
      }
    });
  } else if (pieEmpty) {
    pieEmpty.style.display = "block";
  }

  // -------------------------
  // Yearly Overview (line)
  // -------------------------
  const yearlyCanvas = document.getElementById("yearlyLine");
  const yearlyEmpty = document.getElementById("yearlyLineEmpty");

  const yearlyHasAny =
    hasData(yearlyOverviewData.income) ||
    hasData(yearlyOverviewData.expenses) ||
    hasData(yearlyOverviewData.savings);

  if (yearlyCanvas && yearlyOverviewData && yearlyHasAny) {
    yearlyEmpty.style.display = "none";
    new Chart(yearlyCanvas, {
      type: "line",
      data: {
        labels: yearlyOverviewData.labels,
        datasets: [
          { label: "Income", data: yearlyOverviewData.income, tension: 0.3 },
          { label: "Expenses", data: yearlyOverviewData.expenses, tension: 0.3 },
          { label: "Savings", data: yearlyOverviewData.savings, tension: 0.3 },
        ]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: "bottom" } },
        scales: { y: { beginAtZero: true } }
      }
    });
  } else if (yearlyEmpty) {
    yearlyEmpty.style.display = "block";
  }

  // -------------------------
  // Compare Bar (Month1 vs Month2)
  // -------------------------
  const compareCanvas = document.getElementById("compareBar");

  if (compareCanvas && compareData && compareData.labels) {
    new Chart(compareCanvas, {
      type: "bar",
      data: {
        labels: compareData.labels,
        datasets: [
          { label: compareData.month1_label, data: compareData.month1_values },
          { label: compareData.month2_label, data: compareData.month2_values }
        ]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: "bottom" } },
        scales: { y: { beginAtZero: true } }
      }
    });
  }
})();
