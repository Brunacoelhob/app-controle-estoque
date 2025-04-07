const configPadrao = {
    plugins: {
        legend: {
            labels: {
                color: '#FFF' // Cor da legenda
            }
        }
    },
    scales: {
        x: {
            ticks: {
                color: '#FFF' // Rótulo do eixo X
            },
            grid: {
                color: 'rgba(255,255,255,0.1)' // Linhas suaves
            }
        },
        y: {
            ticks: {
                color: '#FFF' // Rótulo do eixo Y
            },
            grid: {
                color: 'rgba(255,255,255,0.1)'
            }
        }
    }
};

// Gráfico de Colunas
new Chart(document.getElementById("graficoColunas"), {
    type: 'bar',
    data: {
        labels: ["Mouse", "Teclado", "Monitor", "Notebook"],
        datasets: [{
            label: "Vendas (R$)",
            data: [1200, 2100, 3000, 4200],
            backgroundColor: ['#4A90E2', '#50E3C2', '#F5A623', '#D0021B']
        }]
    },
    options: configPadrao
});

// Gráfico de Pizza
new Chart(document.getElementById("graficoPizza"), {
    type: 'pie',
    data: {
        labels: ["Mouse", "Monitor", "Cabo HDMI", "Teclado"],
        datasets: [{
            label: "Produtos em Falta",
            data: [10, 5, 7, 3],
            backgroundColor: ['#D0021B', '#F5A623', '#4A90E2', '#7ED321']
        }]
    },
    options: {
        plugins: {
            legend: {
                labels: {
                    color: '#FFF'
                }
            }
        }
    }
});

// Gráfico de Linhas
new Chart(document.getElementById("graficoLinhas"), {
    type: 'line',
    data: {
        labels: ["Jan", "Fev", "Mar", "Abr"],
        datasets: [{
            label: "Porcentagem de Vendas",
            data: [20, 35, 50, 80],
            borderColor: '#4A90E2',
            backgroundColor: 'rgba(74,144,226,0.2)',
            fill: true
        }]
    },
    options: configPadrao
});

// Gráfico de Comparação de Funcionários
new Chart(document.getElementById("graficoColab"), {
    type: 'bar',
    data: {
        labels: ["Bruna", "Caio", "João"],
        datasets: [{
            label: "Total Vendido (R$)",
            data: [1200, 2100, 3000],
            backgroundColor: '#50E3C2'
        }]
    },
    options: configPadrao
});
