document.addEventListener("DOMContentLoaded", function () {
    const messageContainer = document.getElementById("checkoutMessage");
    const loadingDiv = document.getElementById("loading");
    const PROD_BACKEND_URL = 'https://aif369-backend-api-830685315001.us-central1.run.app';
    const DEV_BACKEND_URL = 'https://aif369-backend-api-dev-830685315001.us-central1.run.app';
    const isProduction = window.location.hostname === 'aif369.com' || window.location.hostname === 'www.aif369.com';
    const BACKEND_URL = isProduction ? PROD_BACKEND_URL : DEV_BACKEND_URL;

    function showMessage(text, type = 'success') {
        messageContainer.textContent = text;
        messageContainer.className = 'message ' + type;
        window.scrollTo({ top: document.querySelector('.payment-section').offsetTop - 100, behavior: 'smooth' });
    }

    function showLoading(show = true) {
        loadingDiv.style.display = show ? 'block' : 'none';
    }

    // Inicializar PayPal Buttons
    paypal.Buttons({
        async createOrder(data, actions) {
            try {
                showLoading(true);

                console.log('📤 Enviando solicitud al backend para crear orden...');

                const response = await fetch(`${BACKEND_URL}/api/paypal/create-order`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        amount: '1.00',
                        currency: 'USD',
                        description: 'Test Payment - Prueba de integración PayPal',
                        source_page: window.location.href
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Error al crear orden');
                }

                const order = await response.json();
                console.log('✅ Orden creada:', order);
                console.log('Order ID:', order.id);

                showLoading(false);
                return order.id;
            } catch (error) {
                console.error('❌ Error creating order:', error);
                showMessage(`Error: ${error.message}`, 'error');
                showLoading(false);
                throw error;
            }
        },

        async onApprove(data, actions) {
            try {
                showLoading(true);
                console.log('📝 Orden aprobada por usuario:', data.orderID);

                const response = await fetch(`${BACKEND_URL}/api/paypal/capture-order`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        order_id: data.orderID
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Error al capturar orden');
                }

                const orderData = await response.json();
                console.log('✅ Pago capturado exitosamente:', orderData);

                showLoading(false);
                showMessage(
                    `✓ Pago exitoso!\n\nID de transacción: ${data.orderID}\n\nVerifica en PayPal Business Account.`,
                    'success'
                );

                // Log para debugging
                console.log('=== PAYPAL PAYMENT SUCCESS ===');
                console.log('Order ID:', data.orderID);
                console.log('Timestamp:', new Date().toISOString());
                console.log('Amount: $1.00 USD');
                console.log('=======================');
            } catch (error) {
                console.error('❌ Error capturing order:', error);
                showMessage(`Error: ${error.message}`, 'error');
                showLoading(false);
            }
        },

        onError(err) {
            console.error('❌ PayPal Error:', err);
            showLoading(false);

            // Determinar mensaje de error específico
            let errorMessage = 'Ocurrió un error con el pago.';
            if (err.message === 'User closed the popup') {
                errorMessage = 'Pago cancelado por el usuario.';
            } else if (err.message.includes('network')) {
                errorMessage = 'Error de conexión. Verifica tu internet.';
            }

            showMessage(errorMessage, 'error');
        },

        onCancel(data) {
            console.log('⚠️ Pago cancelado por usuario:', data);
            showMessage('Pago cancelado. Puedes intentar nuevamente.', 'error');
            showLoading(false);
        }
    }).render('#paypal-button-container');

    console.log('🔧 PayPal Test Page Initialized');
    console.log('Backend URL:', BACKEND_URL);
    console.log('Environment:', isProduction ? 'PRODUCTION' : 'DEVELOPMENT');
});
