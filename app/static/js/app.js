// Comportamentos simples da interface. Fica em arquivo próprio (e não inline) para que a política de
// segurança de conteúdo (CSP) possa bloquear scripts embutidos na página.

// Mensagens (flash) somem sozinhas depois de 4 segundos.
setTimeout(() => {
    const flash = document.querySelector(".flashes");
    if (flash) flash.style.display = "none";
}, 4000);

// Escolher um arquivo no campo marcado envia o formulário (foto de perfil).
document.querySelectorAll("input[data-enviar-ao-escolher]").forEach((campo) => {
    campo.addEventListener("change", () => campo.form.submit());
});

// Formulários com data-confirmar pedem confirmação antes de enviar (ex.: excluir produto).
document.querySelectorAll("form[data-confirmar]").forEach((form) => {
    form.addEventListener("submit", (evento) => {
        if (!window.confirm(form.dataset.confirmar)) evento.preventDefault();
    });
});
