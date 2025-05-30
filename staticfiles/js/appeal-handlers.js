// Handle appeal form submissions with confirmations
function handleAppealAction(formId, action, message) {
    const form = document.getElementById(formId);
    if (!form) return;

    if (confirm(message)) {
        const actionInput = document.createElement('input');
        actionInput.type = 'hidden';
        actionInput.name = 'action';
        actionInput.value = action;
        form.appendChild(actionInput);
        form.submit();
    }
}
