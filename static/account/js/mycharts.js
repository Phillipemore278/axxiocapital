document.addEventListener('DOMContentLoaded', function () {

    // ===== DASHBOARD DONUT CHART =====
    const donutCanvas = document.getElementById("donutChart");
    const donutLabelsEl = document.getElementById("donut-labels");
    const donutValuesEl = document.getElementById("donut-values");

    if (donutCanvas && donutLabelsEl && donutValuesEl) {
        const labels = JSON.parse(donutLabelsEl.textContent);
        const values = JSON.parse(donutValuesEl.textContent);

        new Chart(donutCanvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        getComputedStyle(document.documentElement).getPropertyValue("--color-primary"),
                        getComputedStyle(document.documentElement).getPropertyValue("--color-success")
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                cutout: '85%',
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: true }
                }
            }
        });
    }

    // The performance yield 

    const perfLabelsEl = document.getElementById("performance-labels");
    const perfValuesEl = document.getElementById("performance-values");
    const ctx2 = document.getElementById('lineChart');

    if (perfLabelsEl && perfValuesEl && ctx2) {

        const dynamicLabels = JSON.parse(perfLabelsEl.textContent);
        const dynamicValues = JSON.parse(perfValuesEl.textContent);

        console.log("Labels:", dynamicLabels);
        console.log("Values:", dynamicValues);

        function createFadeGradient(ctx, chartArea, color) {
            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            gradient.addColorStop(0, color.replace('1)', '0.35)'));
            gradient.addColorStop(1, color.replace('1)', '0)'));
            return gradient;
        }

        new Chart(ctx2, {
            type: 'line',
            data: {
                labels: dynamicLabels,
                datasets: [{
                    label: 'Current Year',
                    data: dynamicValues,
                    borderColor: 'rgba(3, 112, 99, 1)',
                    borderWidth: 4,
                    tension: 0.45,
                    pointRadius: 8,
                    fill: true,
                    backgroundColor: (context) => {
                        const { chart } = context;
                        if (!chart.chartArea) return null;

                        return createFadeGradient(
                            chart.ctx,
                            chart.chartArea,
                            'rgba(3, 112, 99, 1)'
                        );
                    }
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                }
            }
        });

    } else {
        console.warn("Performance chart elements missing");
    }


    // ===== ALLOCATION CHART =====
    const allocationCanvas = document.getElementById("allocationChart");
    const allocationLabelsEl = document.getElementById("allocation-labels");
    const allocationValuesEl = document.getElementById("allocation-values");

    if (allocationCanvas && allocationLabelsEl && allocationValuesEl) {
        const labels = JSON.parse(allocationLabelsEl.textContent);
        const values = JSON.parse(allocationValuesEl.textContent);

        new Chart(allocationCanvas, {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        getComputedStyle(document.documentElement)
                            .getPropertyValue("--color-primary"),
                        getComputedStyle(document.documentElement)
                            .getPropertyValue("--color-success"),
                        getComputedStyle(document.documentElement)
                            .getPropertyValue("--color-warning")
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                cutout: "65%"
            }
        });
    }
});