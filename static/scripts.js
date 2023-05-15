// MULTI POOL TABLE

function updateMultiPoolTable(data) {
    const multiPoolTable = document.getElementById("multi-pool-table");
    const exchangeMap = {
        "univ2": "UniV2",
        "sushiv2": "SushiV2",
        "uniswapv3": "UniV3"
    };
    
    let exchange = exchangeMap[data.exchange];
    // Insert row for each pool
    const row = multiPoolTable.insertRow();
    row.insertCell().innerHTML = `${exchange}:${data.token0_symbol}/${data.token1_symbol}`;
    row.insertCell().innerHTML = `$ ${Number(data.reserveUSD).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    row.insertCell().innerHTML = `$ ${Number(data.daily_volumeUSD).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    row.insertCell().innerHTML = `% ${data.volume_to_reserve_ratio}`;
    row.insertCell().innerHTML = `% ${Number(data.return_net_percentage).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    row.insertCell().innerHTML = `% ${data.risk_score}`;

    // Make row clickable
    row.style.cursor = "pointer";
    row.addEventListener("click", () => {
        const timeHorizon = getSelectedTimeHorizon(document.getElementsByName('time_horizon'));
        const riskPreference = getSelectedRiskPreference(document.getElementsByName('risk_preference'));
        fetch(`/api/pool?pool_address=${data.pool_id}&risk_preference=${riskPreference}&time_horizon=${timeHorizon}&accumulate=True`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(poolData => {
                displayPoolData(poolData);
            })
            .catch(error => {
                console.error('Fetch failed:', error);
            });
    });
}

function getSelectedRiskPreference(riskPreferenceRadios) {
    for (let radio of riskPreferenceRadios) {
        if (radio.checked) {
            return radio.value;
        }
    }
}

function getSelectedTimeHorizon(timeHorizonRadios) {
    for (let radio of timeHorizonRadios) {
        if (radio.checked) {
            return radio.value;
        }
    }
}

function fetchAndDisplayPoolData() {
    const pools = ["0x06da0fd433c1a5d7a4faa01111c044910a184553", "0x21b8065d10f73ee2e260e5b47d3344d3ced7596e", 
                    "0x397ff1542f962076d0bfe58ea045ffa2d347aca0", "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f",
                    "0xa478c2975ab1ea89e8196811f51a7b7ade33eb11", "0xae461ca67b15dc8dc81ce7615e0320da1a9ab8d5",
                    "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc", "0xbb2b8038a1640196fbe3e38816f3e67cba72d940",
                    "0xccb63225a7b19dcf66717e4d40c9a72b39331d61", "0xceff51756c56ceffca006cd410b03ffc46dd3a58",
                    "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"];
    const riskPreference = getSelectedRiskPreference(document.getElementsByName('risk_preference'));
    const timeHorizon = getSelectedTimeHorizon(document.getElementsByName('time_horizon'));
    const accumulate = "True";

    // Clear the table before fetching new data
    const multiPoolTable = document.getElementById("multi-pool-table");
    while (multiPoolTable.rows.length > 1) {
        multiPoolTable.deleteRow(1);
    }

    pools.forEach(poolAddress => {
        fetch(`/api/pool?pool_address=${poolAddress}&risk_preference=${riskPreference}&time_horizon=${timeHorizon}&accumulate=${accumulate}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                updateMultiPoolTable(data.pool_info);
            })
            .catch(error => {
                console.error('Fetch failed:', error);
            });
    });
}

function debounce(func, delay) {
    let timeoutId;
    return function() {
      const context = this;
      const args = arguments;
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        func.apply(context, args);
      }, delay);
    };
  }

function sortTable(n) {
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.getElementById("multi-pool-table");
    switching = true;
    // Set the sorting direction to ascending:
    dir = "asc";
    /* Make a loop that will continue until
    no switching has been done: */
    while (switching) {
      // Start by saying: no switching is done:
      switching = false;
      rows = table.rows;
      /* Loop through all table rows (except the
      first, which contains table headers): */
      for (i = 1; i < (rows.length - 1); i++) {
        // Start by saying there should be no switching:
        shouldSwitch = false;
        /* Get the two elements you want to compare,
        one from current row and one from the next: */
        x = rows[i].getElementsByTagName("TD")[n];
        y = rows[i + 1].getElementsByTagName("TD")[n];
        /* Check if the two rows should switch place,
        based on the direction, asc or desc: */
        if (dir == "asc") {
          if (Number(x.innerHTML.replace(/[^0-9.-]+/g,"")) > Number(y.innerHTML.replace(/[^0-9.-]+/g,""))) {
            // If so, mark as a switch and break the loop:
            shouldSwitch = true;
            break;
          }
        } else if (dir == "desc") {
          if (Number(x.innerHTML.replace(/[^0-9.-]+/g,"")) < Number(y.innerHTML.replace(/[^0-9.-]+/g,""))) {
            // If so, mark as a switch and break the loop:
            shouldSwitch = true;
            break;
          }
        }
      }
      if (shouldSwitch) {
        /* If a switch has been marked, make the switch
        and mark that a switch has been done: */
        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
        switching = true;
        // Each time a switch is done, increase this count by 1:
        switchcount ++;
      } else {
        /* If no switching has been done AND the direction is "asc",
        set the direction to "desc" and run the while loop again. */
        if (switchcount == 0 && dir == "asc") {
          dir = "desc";
          switching = true;
        }
      }
    }

    // Remove the class from all headers
    var headers = table.rows[0].getElementsByTagName("TH");
    for (i = 0; i < headers.length; i++) {
        headers[i].classList.remove("sort-asc");
        headers[i].classList.remove("sort-desc");
    }

    // Add the appropriate class to the sorted header
    if (dir == "asc") {
        table.rows[0].getElementsByTagName("TH")[n].classList.add("sort-asc");
    } else {
        table.rows[0].getElementsByTagName("TH")[n].classList.add("sort-desc");
    }
}

function displayPoolData(data) {
    // Create a lightbox container
    const lightbox = document.createElement("div");
    lightbox.style.position = "fixed";
    lightbox.style.top = "0";
    lightbox.style.left = "0";
    lightbox.style.width = "100vw";
    lightbox.style.height = "100vh";
    lightbox.style.backgroundColor = "rgba(0, 0, 0, 0.3)"; // Darker color, more transparent
    lightbox.style.display = "flex";
    lightbox.style.justifyContent = "center";
    lightbox.style.alignItems = "center";

    // Create a content container
    const content = document.createElement("div");
    content.style.backgroundColor = "rgba(150, 200, 250, 0.95)"; // Semi-transparent white
    content.style.padding = "20px";
    content.style.maxWidth = "80%";
    content.style.maxHeight = "80%";
    content.style.overflow = "auto";
    content.style.borderRadius = "15px"; // Rounded corners for a smoother design
    content.style.boxShadow = "0 10px 20px rgba(0, 0, 0, 0.19), 0 6px 6px rgba(0, 0, 0, 0.23)"; // Shadow for 3D effect


    // Print pool info
    let poolInfoTable = updatePoolInfoTable(data.pool_info);
    content.appendChild(poolInfoTable);

    // Spacer
    let spacer = document.createElement('div');
    spacer.style.height = '20px';
    content.appendChild(spacer);

    // Print output data
    let table = updateTable(data.static_kpis);
    content.appendChild(table);

    // Print charts
    let charts = plotCharts([
        { id: 'total_risk_score', div: 'total_risk-score_chart', name: 'Total Risk Score', data: data.dynamic_kpis.risk_score },
        { id: 'return_net_percentage', div: 'return-net-percentage-chart', name: 'Return Net Percentage', data: data.dynamic_kpis.return_net_percentage },
        { id: 'impermanent_loss_percentage', div: "impermanent-loss-percentage-chart", name: 'Impermanent Loss Percentage', data: data.dynamic_kpis.impermanent_loss_percentage },
        { id: 'daily_volume_usd', div: "daily-volume-usd-chart", name: 'Daily Volume USD', data: data.dynamic_kpis.daily_volumeUSD },
        { id: 'volume_to_reserve', div: "volume-to-reserve-ratio-chart", name: 'Volume to Reserve Ratio', data: data.dynamic_kpis.volume_to_reserve }
    ]);


    for (let chart of charts) {
        content.appendChild(chart);
    }

    // Append content to lightbox
    lightbox.appendChild(content);
    
    // Append lightbox to body
    document.body.appendChild(lightbox);

    // Close lightbox on click
    lightbox.addEventListener('click', function() {
        document.body.removeChild(lightbox);
    });
}

// SUB-SITE POOL KPIs

function plotCharts(kpiList) {
    const layout = {
        showlegend: false
    };

    const chartDivs = [];

    for (const kpi of kpiList) {
        const chartDiv = document.createElement('div');
        chartDiv.id = kpi.div;

        const trace = {
            x: Object.keys(kpi.data),
            y: Object.values(kpi.data),
            mode: 'lines',
            name: kpi.name
        };

        Plotly.newPlot(chartDiv, [trace], { ...layout, title: kpi.name });
        chartDivs.push(chartDiv);
    }

    return chartDivs;
}

function updateTable(data) {
    const table = document.createElement('table');
    table.innerHTML = `
        <tr>
            <th>KPI</th>
            <th>Value</th>
        </tr>
    `;
    for (const [key, value] of Object.entries(data)) {
        const row = table.insertRow();
        const kpiCell = row.insertCell();
        const valueCell = row.insertCell();
        kpiCell.innerHTML = key;
        valueCell.innerHTML = value;
    }
    return table;
}

function updatePoolInfoTable(data) {
    const poolInfoTable = document.createElement('table');
    poolInfoTable.innerHTML = `
        <tr>
            <th>Pool Info</th>
            <th>Value</th>
        </tr>
    `;
    for (const [key, value] of Object.entries(data)) {
        const row = poolInfoTable.insertRow();
        const infoCell = row.insertCell();
        const valueCell = row.insertCell();
        infoCell.innerHTML = key;
        valueCell.innerHTML = value;
    }
    return poolInfoTable;
}

let lastSortedColumn = null;
let sortDirections = Array(5).fill('asc');

document.querySelectorAll('th').forEach((header, index) => {
    header.addEventListener('click', () => sortTable(index));
});
  
const pools_form = document.getElementById('multi-pool-form');
if (pools_form) {
    pools_form.addEventListener('change', debounce(async (event) => {
        event.preventDefault();
        fetchAndDisplayPoolData();
    }, 1000));
}

window.onload = function() {
    fetchAndDisplayPoolData();
};
