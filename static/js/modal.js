async function openModal(url) {
    const modalRoot = document.getElementById('modal-root');
    if (!modalRoot) return;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to fetch modal content: ${response.statusText}`);
        }
        const html = await response.text();
        modalRoot.innerHTML = html;
        modalRoot.hidden = false;

        // Add event listeners for closing the modal
        const closeButton = modalRoot.querySelector('.close-modal');
        if (closeButton) {
            closeButton.addEventListener('click', closeModal);
        }
        modalRoot.addEventListener('click', (e) => {
            if (e.target === modalRoot) { // Background click
                closeModal();
            }
        });
        document.addEventListener('keydown', handleEscKey);

    } catch (error) {
        console.error('Error opening modal:', error);
        modalRoot.innerHTML = `<p style="color:white;">Error loading content.</p><button class="close-modal">Close</button>`;
        modalRoot.hidden = false;
    }
}

function closeModal() {
    const modalRoot = document.getElementById('modal-root');
    if (modalRoot) {
        modalRoot.innerHTML = '';
        modalRoot.hidden = true;
    }
    document.removeEventListener('keydown', handleEscKey);
}

function handleEscKey(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
}

// Function to handle form submission via fetch
async function handleFormSubmit(form) {
    const url = form.action;
    const method = form.method;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries()); // Basic conversion

    // More complex data structuring might be needed here based on API expectations

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': data.csrfmiddlewaretoken,
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (response.ok) {
            closeModal();
            const feedContent = document.getElementById('feed-content');
            if (feedContent && result.card_html) {
                feedContent.insertAdjacentHTML('afterbegin', result.card_html);
            }
        } else {
            alert(`Error: ${result.error || 'Something went wrong.'}`);
        }
    } catch (error) {
        console.error('Form submission error:', error);
        alert('An unexpected error occurred.');
    }
}
