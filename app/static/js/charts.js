/* =========================================
   SubTracker - Chart Utilities
   ========================================= */


/*
 * Create a simple bar chart.
 */

function createBarChart(
    canvasId,
    labels,
    values,
    label
) {

    const canvas = document.getElementById(canvasId);

    if (!canvas) {
        return;
    }

    new Chart(canvas, {

        type: "bar",

        data: {

            labels: labels,

            datasets: [

                {
                    label: label,
                    data: values
                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            scales: {

                y: {
                    beginAtZero: true
                }

            }

        }

    });

}


/*
 * Create a line chart.
 */

function createLineChart(
    canvasId,
    labels,
    values,
    label
) {

    const canvas = document.getElementById(canvasId);

    if (!canvas) {
        return;
    }

    new Chart(canvas, {

        type: "line",

        data: {

            labels: labels,

            datasets: [

                {
                    label: label,
                    data: values,
                    tension: 0.3,
                    fill: false
                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            scales: {

                y: {
                    beginAtZero: true
                }

            }

        }

    });

}