document.addEventListener("DOMContentLoaded", function() {
    const decrementBtn = document.querySelector(".decrement");
    const incrementBtn = document.querySelector(".increment");
    const quantityInput = document.querySelector(".quantity-input");
    const addToCartBtn = document.querySelector(".add-to-cart-button");
    const comprarAgoraBtn = document.querySelector(".comprar-agora");
    const addToCartForm = document.getElementById("add-to-cart-form");
    let cartCountElement = document.getElementById("cart-count");
    const lottieAnimation = document.getElementById("lottie-animation");

    // Incrementar e Decrementar a quantidade
    if (decrementBtn && incrementBtn && quantityInput) {
        decrementBtn.addEventListener("click", function() {
            let currentValue = parseInt(quantityInput.value);
            if (currentValue > 1) {
                quantityInput.value = currentValue - 1;
            }
        });

        incrementBtn.addEventListener("click", function() {
            let currentValue = parseInt(quantityInput.value);
            quantityInput.value = currentValue + 1;
        });
    }

    // Botão "Adicionar ao Carrinho" usando AJAX
    if (addToCartBtn) {
        addToCartBtn.addEventListener("click", function() {
            const formData = new FormData(addToCartForm);

            fetch(addToCartForm.action, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    console.log("Produto adicionado com sucesso ao carrinho");

                    // Atualiza a contagem de produtos no carrinho
                    if (cartCountElement) {
                        let currentCount = parseInt(cartCountElement.textContent) || 0;
                        let quantityToAdd = parseInt(quantityInput.value) || 1;
                        cartCountElement.textContent = currentCount + quantityToAdd;

                        console.log(`Novo valor do cart-count: ${cartCountElement.textContent}`);
                    } else {
                        console.error("Elemento cart-count não encontrado.");
                    }

                    // Animação do botão
                    addToCartBtn.classList.add("added");
                    setTimeout(function() {
                        addToCartBtn.classList.remove("added");
                    }, 2000);

                    // Reproduz a animação Lottie ao clicar no botão "Adicionar ao Carrinho"
                    if (lottieAnimation) {
                        lottieAnimation.stop(); // Para garantir que a animação reinicie
                        lottieAnimation.play();
                        lottieAnimation.style.display = "block"; // Exibe a animação
                    }
                } else {
                    console.error("Erro ao adicionar o produto ao carrinho:", data.message);
                }
            })
            .catch(error => {
                console.error("Erro ao adicionar o produto ao carrinho:", error);
            });
        });

        // Ocultar a animação ao terminar
        if (lottieAnimation) {
            lottieAnimation.addEventListener("complete", function() {
                lottieAnimation.style.display = "none"; // Oculta a animação após terminar
            });
        }
    }

    // Botão "Comprar Agora" usando AJAX e redirecionando para o carrinho
    if (comprarAgoraBtn) {
        comprarAgoraBtn.addEventListener("click", function() {
            const formData = new FormData(addToCartForm);
            const carrinhoUrl = comprarAgoraBtn.getAttribute("data-carrinho-url");

            fetch(addToCartForm.action, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    window.location.href = carrinhoUrl;
                } else {
                    console.error("Erro ao adicionar o produto ao carrinho:", data.message);
                }
            })
            .catch(error => {
                console.error("Erro ao adicionar o produto ao carrinho:", error);
            });
        });
    }
});