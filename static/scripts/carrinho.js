document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('addressForm');
    const finalizarButton = document.getElementById('finalizarCompra');

    // Valida se todos os campos estão preenchidos
    function validarCampos() {
        const allFieldsFilled = Array.from(form.elements).every(input => input.value.trim() !== '');
        finalizarButton.disabled = !allFieldsFilled;
    }

    form.addEventListener('input', validarCampos);

    finalizarButton.addEventListener('click', function () {
        console.log("Botão clicado!"); // Verifica se o clique está sendo capturado
        const linkCheckout = finalizarButton.getAttribute('data-link');
        console.log("Link de Checkout:", linkCheckout); // Verifica o link do data-link

        if (!finalizarButton.disabled && linkCheckout) {
            window.location.href = linkCheckout; // Redireciona para a rota /checkout
        } else {
            alert('Por favor, preencha todos os campos antes de finalizar a compra.');
        }
    });
});
