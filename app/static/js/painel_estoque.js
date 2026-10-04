// Gráficos do painel: usam os dados reais embutidos pelo servidor (nada de valores fixos).
const dados = JSON.parse(document.getElementById("dados-painel").textContent);

const opcoesComEixos = {
    plugins: { legend: { labels: { color: "#FFF" } } },
    scales: {
        x: { ticks: { color: "#FFF" }, grid: { color: "rgba(255,255,255,0.1)" } },
        y: { ticks: { color: "#FFF" }, grid: { color: "rgba(255,255,255,0.1)" }, beginAtZero: true },
    },
};
const opcoesPizza = { plugins: { legend: { labels: { color: "#FFF" } } } };
const paleta = ["#4A90E2", "#50E3C2", "#F5A623", "#D0021B", "#7ED321", "#BD10E0", "#9B9B9B"];

function criar(id, config) {
    const canvas = document.getElementById(id);
    if (canvas) new Chart(canvas, config);
}

criar("graficoEstoque", {
    type: "bar",
    data: {
        labels: dados.estoque.rotulos,
        datasets: [
            { label: "Quantidade atual", data: dados.estoque.quantidade, backgroundColor: "#4A90E2" },
            { label: "Mínimo", data: dados.estoque.minimo, backgroundColor: "#F5A623" },
        ],
    },
    options: opcoesComEixos,
});

criar("graficoFaltantes", {
    type: "pie",
    data: {
        labels: dados.faltantes.rotulos,
        datasets: [{ label: "Unidades faltando", data: dados.faltantes.deficit, backgroundColor: paleta }],
    },
    options: opcoesPizza,
});

criar("graficoMovimentacao", {
    type: "line",
    data: {
        labels: dados.movimentacao.rotulos,
        datasets: [
            { label: "Entradas", data: dados.movimentacao.entradas, borderColor: "#50E3C2", tension: 0.2 },
            { label: "Saídas", data: dados.movimentacao.saidas, borderColor: "#D0021B", tension: 0.2 },
        ],
    },
    options: opcoesComEixos,
});

criar("graficoUsuarios", {
    type: "bar",
    data: {
        labels: dados.por_usuario.rotulos,
        datasets: [{ label: "Unidades movimentadas", data: dados.por_usuario.unidades, backgroundColor: "#50E3C2" }],
    },
    options: opcoesComEixos,
});
